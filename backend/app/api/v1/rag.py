"""RAG retrieval endpoint.

Provides document retrieval from the vector store for a given query.
Endpoint: POST /rag/retrieval
"""
from __future__ import annotations

from fastapi import APIRouter, Depends

from app.api.deps import get_rag_service
from app.models.common import APIResponse
from app.models.rag import QueryRequest, RetrievalConfig
from app.services.rag_service import RAGService

router = APIRouter()


@router.post(
    "/retrieval",
    response_model=APIResponse,
    summary="RAG retrieval",
    description="Retrieve relevant documents from the vector store for a given query.",
)
async def rag_retrieval(
    request: QueryRequest,
    config: RetrievalConfig | None = None,
    rag_service: RAGService = Depends(get_rag_service),
) -> dict:
    """Perform RAG document retrieval.

    Embeds the query, searches the vector store, and returns source
    documents with relevance scores.

    Args:
        request: Query text and optional metadata.
        config: Retrieval configuration (top_k, filters, etc.).
        rag_service: Injected RAGService.

    Returns:
        Retrieved source documents and query info.
    """
    top_k = config.top_k if config else 5

    documents = await rag_service.retrieve(query=request.query, top_k=top_k)

    sources = [
        {
            "content": doc.get("content", ""),
            "source": doc.get("source", "unknown"),
            "score": doc.get("score", 0.0),
            "metadata": doc.get("metadata", {}),
        }
        for doc in documents
    ]

    return APIResponse.success(
        data={
            "query": request.query,
            "sources": sources,
            "count": len(sources),
        },
        message="Retrieval successful",
    ).model_dump()
