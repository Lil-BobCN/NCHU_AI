"""Administrative knowledge, audit, and stats routes."""
from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status

from app.api.v1.deps import require_admin
from app.schemas.business import (
    AuditEventResponse,
    KnowledgeResponse,
    KnowledgeUpsert,
    StatsResponse,
)
from app.services.business import User, store

router = APIRouter(prefix="/admin", tags=["admin"])


@router.get("/knowledge", response_model=list[KnowledgeResponse])
async def list_knowledge(_user: Annotated[User, Depends(require_admin)]) -> list[KnowledgeResponse]:
    """List all knowledge base entries."""
    return list(store.knowledge.values())


@router.post(
    "/knowledge",
    response_model=KnowledgeResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_knowledge(
    payload: KnowledgeUpsert,
    user: Annotated[User, Depends(require_admin)],
) -> KnowledgeResponse:
    """Create a knowledge base entry."""
    return store.create_knowledge(
        actor_id=user.id,
        title=payload.title,
        content=payload.content,
        category=payload.category,
        tags=payload.tags,
        status=payload.status,
    )


@router.put("/knowledge/{knowledge_id}", response_model=KnowledgeResponse)
async def update_knowledge(
    knowledge_id: str,
    payload: KnowledgeUpsert,
    user: Annotated[User, Depends(require_admin)],
) -> KnowledgeResponse:
    """Replace a knowledge base entry."""
    item = store.knowledge.get(knowledge_id)
    if item is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Knowledge not found")
    return store.update_knowledge(
        actor_id=user.id,
        item=item,
        title=payload.title,
        content=payload.content,
        category=payload.category,
        tags=payload.tags,
        status=payload.status,
    )


@router.delete("/knowledge/{knowledge_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_knowledge(
    knowledge_id: str,
    user: Annotated[User, Depends(require_admin)],
) -> None:
    """Delete a knowledge base entry."""
    if knowledge_id not in store.knowledge:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Knowledge not found")
    store.delete_knowledge(user.id, knowledge_id)


@router.get("/audit", response_model=list[AuditEventResponse])
async def list_audit_events(
    _user: Annotated[User, Depends(require_admin)],
) -> list[AuditEventResponse]:
    """List in-memory audit events."""
    return list(reversed(store.audit_events))


@router.get("/stats", response_model=StatsResponse)
async def get_stats(_user: Annotated[User, Depends(require_admin)]) -> dict[str, int]:
    """Return simple business counters."""
    return store.stats()
