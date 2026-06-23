from fastapi import APIRouter, Depends
from pydantic import BaseModel

from app.api.deps import get_current_admin
from app.core.responses import ok
from app.db.models import Admin
from app.services.rag_settings_service import RagSettingsService


router = APIRouter(prefix="/settings", tags=["settings"])


class RagSettingsUpdate(BaseModel):
    chunk_size: int
    chunk_overlap: int
    table_chunk_rows: int = 50
    table_full_index_max_rows: int = 500
    table_sample_rows: int = 50
    max_document_chunks: int = 300
    max_embedding_chars_per_document: int = 200000
    vector_top_k: int
    keyword_top_k: int
    qa_top_k: int
    rerank_top_k: int
    similarity_threshold: float
    rerank_threshold: float
    rerank_enabled: bool = True
    rerank_max_candidates: int = 10


@router.get("/rag")
async def get_rag_settings(_: Admin = Depends(get_current_admin)):
    return ok({**RagSettingsService().get_effective(), "persisted": True})


@router.put("/rag")
async def update_rag_settings(
    payload: RagSettingsUpdate,
    _: Admin = Depends(get_current_admin),
):
    values = RagSettingsService().save(payload.model_dump())
    return ok({**values, "persisted": True})
