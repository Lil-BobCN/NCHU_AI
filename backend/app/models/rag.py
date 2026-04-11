"""RAG domain models.

Pydantic models for RAG queries, responses, and retrieval configuration.
"""
from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class SourceDocument(BaseModel):
    """A retrieved source document from the vector store.

    Attributes:
        content: Document text content.
        source: Source identifier (filename, URL, etc.).
        score: Relevance similarity score (0-1).
        metadata: Document metadata (page, section, etc.).
    """

    content: str
    source: str
    score: float = Field(..., ge=0.0, le=1.0)
    metadata: dict[str, Any] = Field(default_factory=dict)


class RAGResponse(BaseModel):
    """RAG retrieval response.

    Attributes:
        query: Original query text.
        sources: Retrieved source documents.
        context: Combined context text for LLM prompting (or the answer).
        confidence: Average similarity score across retrieved documents (0-1).
    """

    query: str
    sources: list[SourceDocument] = Field(default_factory=list)
    context: str = ""
    confidence: float = Field(default=0.0, ge=0.0, le=1.0)


class RetrievalConfig(BaseModel):
    """Configuration for RAG retrieval.

    Attributes:
        top_k: Number of documents to retrieve.
        score_threshold: Minimum similarity score threshold.
        filters: Optional metadata filters for vector search.
        embedding_model: Override default embedding model.
    """

    top_k: int = Field(default=5, ge=1, le=20)
    score_threshold: float = Field(default=0.7, ge=0.0, le=1.0)
    filters: dict[str, Any] = Field(default_factory=dict)
    embedding_model: str | None = None


class QueryRequest(BaseModel):
    """Request body for RAG retrieval.

    Attributes:
        query: Search query text.
        session_id: Optional chat session ID for context.
    """

    query: str = Field(..., min_length=1, max_length=2000)
    session_id: str | None = None
