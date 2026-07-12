"""Knowledge base catalog API."""

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_admin
from app.core.responses import ok
from app.db.models import Admin
from app.db.session import get_db
from app.services.knowledge_base_service import KnowledgeBaseService, serialize_knowledge_base_option


router = APIRouter(prefix="/knowledge-bases", tags=["knowledge-bases"])


@router.get("")
async def list_knowledge_bases(
    db: AsyncSession = Depends(get_db),
    _: Admin = Depends(get_current_admin),
):
    options = await KnowledgeBaseService().list_options(db)
    return ok(
        {
            "items": [serialize_knowledge_base_option(option) for option in options],
            "total": len(options),
        }
    )
