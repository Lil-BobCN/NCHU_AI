"""
通用响应 schema。用于描述统一 API 响应结构。
"""

from typing import Any
from pydantic import BaseModel


class ApiResponse(BaseModel):
    code: int = 0
    message: str = "ok"
    data: Any = None


class PageResponse(BaseModel):
    items: list[Any]
    page: int
    page_size: int
    total: int

