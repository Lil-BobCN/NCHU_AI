"""
Hash 工具。生成文件和文本摘要，用于去重、内容变更识别和缓存 key。
"""

import hashlib


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()

