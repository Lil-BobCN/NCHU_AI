"""FastAPI dependency injection helpers.

Provides reusable async dependencies for database sessions, Redis connections,
application settings, and all RAG/LLM services.

Service factories use module-level singletons (lazy-initialized) to avoid
recreating expensive clients per request while remaining compatible with
FastAPI's Depends() injection.
"""
from __future__ import annotations

from typing import AsyncGenerator

from qdrant_client import AsyncQdrantClient

from app.config import Settings, get_settings
from app.db.repositories.chat_repo import ChatRepository
from app.rag.prompt_builder import PromptBuilder
from app.rag.retriever import Retriever
from app.services.embedding_service import EmbeddingService
from app.services.llm_service import LLMService
from app.services.rag_service import RAGService
from app.services.session_service import SessionService


# ---------------------------------------------------------------------------
# Module-level service singletons (lazy-initialized on first access)
# ---------------------------------------------------------------------------
_llm_service: LLMService | None = None
_embedding_service: EmbeddingService | None = None
_qdrant_client: AsyncQdrantClient | None = None
_retriever: Retriever | None = None
_prompt_builder: PromptBuilder | None = None
_rag_service: RAGService | None = None
_session_service: SessionService | None = None


def _get_settings() -> Settings:
    """Resolve settings from the cached config singleton."""
    return get_settings()


def _get_llm_service() -> LLMService:
    """Get or create the LLM service singleton."""
    global _llm_service
    if _llm_service is None:
        settings = _get_settings()
        _llm_service = LLMService(
            api_key=settings.dashscope_api_key,
            model_name=settings.dashscope_model,
            base_url=settings.dashscope_api_base_url,
            max_retries=settings.retry_total,
            timeout=settings.request_timeout,
        )
    return _llm_service


def _get_embedding_service() -> EmbeddingService:
    """Get or create the embedding service singleton."""
    global _embedding_service
    if _embedding_service is None:
        settings = _get_settings()
        _embedding_service = EmbeddingService(
            api_key=settings.dashscope_api_key,
            model=settings.embedding_model,
        )
    return _embedding_service


def _get_qdrant_client() -> AsyncQdrantClient:
    """Get or create the Qdrant async client singleton."""
    global _qdrant_client
    if _qdrant_client is None:
        settings = _get_settings()
        _qdrant_client = AsyncQdrantClient(url=settings.qdrant_url)
    return _qdrant_client


def _get_retriever() -> Retriever:
    """Get or create the retriever singleton."""
    global _retriever
    if _retriever is None:
        _retriever = Retriever(
            qdrant_client=_get_qdrant_client(),
            embedding_service=_get_embedding_service(),
        )
    return _retriever


def _get_prompt_builder() -> PromptBuilder:
    """Get or create the prompt builder singleton."""
    global _prompt_builder
    if _prompt_builder is None:
        _prompt_builder = PromptBuilder()
    return _prompt_builder


def _get_rag_service() -> RAGService:
    """Get or create the RAG service singleton."""
    global _rag_service
    if _rag_service is None:
        _rag_service = RAGService(
            llm_service=_get_llm_service(),
            embedding_service=_get_embedding_service(),
            retriever=_get_retriever(),
            prompt_builder=_get_prompt_builder(),
        )
    return _rag_service


def _get_session_service() -> SessionService:
    """Get or create the session service singleton."""
    global _session_service
    if _session_service is None:
        # TODO: Replace with real repository once DB session is wired
        from unittest.mock import AsyncMock

        mock_repo = AsyncMock(spec=ChatRepository)
        _session_service = SessionService(chat_repo=mock_repo)
    return _session_service


# ---------------------------------------------------------------------------
# FastAPI dependency providers (thin wrappers around the singletons)
# ---------------------------------------------------------------------------


def get_settings_dep() -> Settings:
    """Get application settings singleton.

    Returns:
        Application Settings instance.
    """
    return _get_settings()


async def get_db() -> AsyncGenerator[object, None]:
    """Provide an async database session per request.

    Yields:
        Async SQLAlchemy session.

    Note:
        TODO: Replace stub with actual async session from session.py.
    """
    yield None  # type: ignore[misc]


async def get_redis() -> AsyncGenerator[object, None]:
    """Provide a Redis connection per request.

    Yields:
        Redis client instance.

    Note:
        TODO: Replace stub with actual Redis connection.
    """
    yield None  # type: ignore[misc]


def get_llm_service() -> LLMService:
    """Provide the LLM service dependency.

    Returns:
        Configured LLMService instance.
    """
    return _get_llm_service()


def get_embedding_service() -> EmbeddingService:
    """Provide the embedding service dependency.

    Returns:
        Configured EmbeddingService instance.
    """
    return _get_embedding_service()


def get_qdrant_client() -> AsyncQdrantClient:
    """Provide the Qdrant client dependency.

    Returns:
        Configured AsyncQdrantClient instance.
    """
    return _get_qdrant_client()


def get_retriever() -> Retriever:
    """Provide the retriever dependency.

    Returns:
        Configured Retriever instance.
    """
    return _get_retriever()


def get_prompt_builder() -> PromptBuilder:
    """Provide the prompt builder dependency.

    Returns:
        Configured PromptBuilder instance.
    """
    return _get_prompt_builder()


def get_rag_service() -> RAGService:
    """Provide the RAG service dependency.

    Returns:
        Configured RAGService instance.
    """
    return _get_rag_service()


def get_session_service() -> SessionService:
    """Provide the session service dependency.

    Returns:
        Configured SessionService instance.
    """
    return _get_session_service()


def get_chat_repo() -> ChatRepository:
    """Provide a chat repository instance.

    Note:
        TODO: Replace with actual session-scoped repository.
    """
    # TODO: Implement with actual database session
    return None  # type: ignore[return-value]
