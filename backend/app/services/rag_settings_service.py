"""RAG 设置服务：读取默认配置、运行时覆盖配置并写入本地缓存。"""

import json
from pathlib import Path
from typing import Any

from app.core.config import get_settings


class RagSettingsService:
    NUMERIC_FIELDS = {
        "chunk_size": int,
        "chunk_overlap": int,
        "table_chunk_rows": int,
        "table_full_index_max_rows": int,
        "table_sample_rows": int,
        "max_document_chunks": int,
        "max_embedding_chars_per_document": int,
        "vector_top_k": int,
        "keyword_top_k": int,
        "qa_top_k": int,
        "rerank_top_k": int,
        "similarity_threshold": float,
        "rerank_threshold": float,
        "rerank_max_candidates": int,
    }
    BOOLEAN_FIELDS = {"rerank_enabled"}

    def __init__(self) -> None:
        self.settings = get_settings()
        self.path = Path(__file__).resolve().parents[3] / ".cache" / "rag_settings.json"

    def defaults(self) -> dict[str, Any]:
        return {
            "chunk_size": self.settings.chunk_size,
            "chunk_overlap": self.settings.chunk_overlap,
            "table_chunk_rows": self.settings.table_chunk_rows,
            "table_full_index_max_rows": self.settings.table_full_index_max_rows,
            "table_sample_rows": self.settings.table_sample_rows,
            "max_document_chunks": self.settings.max_document_chunks,
            "max_embedding_chars_per_document": self.settings.max_embedding_chars_per_document,
            "vector_top_k": self.settings.vector_top_k,
            "keyword_top_k": self.settings.keyword_top_k,
            "qa_top_k": self.settings.qa_top_k,
            "rerank_top_k": self.settings.rerank_top_k,
            "similarity_threshold": self.settings.similarity_threshold,
            "rerank_threshold": self.settings.rerank_threshold,
            "rerank_enabled": self.settings.rerank_enabled,
            "rerank_max_candidates": self.settings.rerank_max_candidates,
        }

    def get_effective(self) -> dict[str, Any]:
        values = self.defaults()
        values.update(self._read_overrides())
        return values

    def save(self, payload: dict[str, Any]) -> dict[str, Any]:
        values = self.defaults()
        cleaned = self._clean(payload)
        values.update(cleaned)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(json.dumps(cleaned, ensure_ascii=False, indent=2), encoding="utf-8")
        return values

    def _read_overrides(self) -> dict[str, Any]:
        if not self.path.exists():
            return {}
        try:
            raw = json.loads(self.path.read_text(encoding="utf-8"))
        except Exception:
            return {}
        return self._clean(raw if isinstance(raw, dict) else {})

    def _clean(self, payload: dict[str, Any]) -> dict[str, Any]:
        values: dict[str, Any] = {}
        for field, caster in self.NUMERIC_FIELDS.items():
            if field not in payload:
                continue
            try:
                value = caster(payload[field])
            except (TypeError, ValueError):
                continue
            values[field] = max(0, value) if caster is int else value
        for field in self.BOOLEAN_FIELDS:
            if field not in payload:
                continue
            value = payload[field]
            if isinstance(value, str):
                values[field] = value.lower() in {"1", "true", "yes", "on"}
            else:
                values[field] = bool(value)
        return values
