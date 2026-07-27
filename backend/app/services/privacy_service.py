"""
隐私信息脱敏服务。在文档入库阶段对解析后的文本做正则兜底脱敏，
确保手机号、身份证号等敏感信息不进入检索库和 LLM 上下文。

@author 自由行
"""

import re
from dataclasses import dataclass


# 个人手机号：1XX 开头 11 位数字
_MOBILE_RE = re.compile(r"(?<!\d)1[3-9]\d{9}(?!\d)")
# 身份证号码：18位（含末位 X）
_ID_CARD_RE = re.compile(r"(?<!\d)\d{6}(?:19|20)\d{2}(?:0[1-9]|1[0-2])(?:0[1-9]|[12]\d|3[01])\d{3}[\dXx](?!\d)")
# 银行卡号：16-19 位连续数字（可能误伤长数字编号，但业务风险可控）
_BANK_CARD_RE = re.compile(r"(?<!\d)\d{16,19}(?!\d)")


@dataclass
class PrivacyMaskResult:
    """脱敏结果"""
    text: str
    masked_count: int          # 脱敏次数
    masked_types: list[str]    # 脱敏类型列表


class PrivacyService:
    """隐私信息脱敏服务。

    对文档解析后的文本内容进行正则脱敏：
    - 个人手机号 → 1XXXXXXXXXX
    - 身份证号码 → XXXXXXXXXXXXXXXXXX
    - 银行卡号   → XXXXXXXXXXXXXXXX（16-19位数字）
    """

    def mask(self, text: str) -> PrivacyMaskResult:
        """对文本做隐私脱敏，返回脱敏后的文本和统计信息。"""
        if not text:
            return PrivacyMaskResult(text="", masked_count=0, masked_types=[])

        masked_types: list[str] = []
        result = text

        # 1. 身份证号（优先匹配，避免被手机号正则部分匹配）
        id_card_count = len(_ID_CARD_RE.findall(result))
        if id_card_count > 0:
            result = _ID_CARD_RE.sub("XXXXXXXXXXXXXXXXXX", result)
            masked_types.append(f"id_card({id_card_count})")

        # 2. 个人手机号
        mobile_count = len(_MOBILE_RE.findall(result))
        if mobile_count > 0:
            result = _MOBILE_RE.sub("1XXXXXXXXXX", result)
            masked_types.append(f"mobile({mobile_count})")

        # 3. 银行卡号（16-19位数字，排除已被手机号/身份证替换的）
        bank_card_count = len(_BANK_CARD_RE.findall(result))
        if bank_card_count > 0:
            result = _BANK_CARD_RE.sub("XXXXXXXXXXXXXXXX", result)
            masked_types.append(f"bank_card({bank_card_count})")

        total = id_card_count + mobile_count + bank_card_count
        return PrivacyMaskResult(
            text=result,
            masked_count=total,
            masked_types=masked_types,
        )

    def mask_document_text(self, text: str) -> str:
        """便捷方法：只返回脱敏后的文本。"""
        return self.mask(text).text


# 模块级单例
_privacy_service: PrivacyService | None = None


def get_privacy_service() -> PrivacyService:
    """获取 PrivacyService 单例。"""
    global _privacy_service
    if _privacy_service is None:
        _privacy_service = PrivacyService()
    return _privacy_service
