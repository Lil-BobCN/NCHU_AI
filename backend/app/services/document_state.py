"""
文档状态辅助工具。根据解析结果判断是否可切片、是否需要转换或解压，以及终态提示。
"""

from typing import Any


LEGACY_OFFICE_EXTENSIONS = {".doc", ".xls"}
ARCHIVE_EXTENSIONS = {".zip", ".rar"}
BLOCKED_INDEX_STATUSES = {
    "needs_conversion",
    "needs_extraction",
    "no_indexable_content",
    "converted",
    "extracted",
}


def parse_terminal_status(parse_meta: dict[str, Any] | None) -> str:
    meta = parse_meta or {}
    if meta.get("needs_conversion"):
        return "needs_conversion"
    if meta.get("needs_extraction"):
        return "needs_extraction"
    if meta.get("skip_chunking"):
        return "no_indexable_content"
    return "parsed"


def parse_terminal_message(parse_meta: dict[str, Any] | None) -> str:
    status = parse_terminal_status(parse_meta)
    if status == "needs_conversion":
        return "解析完成，当前文件需要先转换为新版 Office 格式，未进入切片"
    if status == "needs_extraction":
        return "解析完成，当前压缩包需要先解压导入，未进入切片"
    if status == "no_indexable_content":
        return "解析完成，但没有可入库正文，未进入切片"
    return "解析完成"


def indexing_blocker(document: Any, parse_meta: dict[str, Any] | None = None) -> str | None:
    status = str(getattr(document, "status", "") or "")
    meta = parse_meta or {}
    if status == "needs_conversion" or meta.get("needs_conversion"):
        return "已跳过：请先转换为 .docx/.xlsx 后再切片、向量化或生成 QA"
    if status == "needs_extraction" or meta.get("needs_extraction"):
        return "已跳过：请先解压导入内部文档后再切片、向量化或生成 QA"
    if status == "converted":
        return "已跳过：原始文件已转换，请在转换后的文档上继续处理"
    if status == "extracted":
        return "已跳过：压缩包已解压，请在导入的文档上继续处理"
    if status == "no_indexable_content" or meta.get("skip_chunking"):
        return "已跳过：当前解析结果没有可入库正文"
    return None
