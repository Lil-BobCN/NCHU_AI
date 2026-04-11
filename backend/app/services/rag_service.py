"""RAG core service.

Orchestrates the full Retrieval-Augmented Generation pipeline:
embed query -> retrieve documents -> build context -> generate answer.
"""
from __future__ import annotations

from typing import Any

from app.core.exceptions import RetrievalError, LLMError
from app.models.rag import RAGResponse, SourceDocument


class RAGService:
    """RAG pipeline orchestrator.

    Attributes:
        llm_service: LLMService for generating answers.
        embedding_service: EmbeddingService for query embedding.
        retriever: Retriever for document search.
        prompt_builder: PromptBuilder for message construction.
        top_k: Default number of documents to retrieve.
    """

    def __init__(
        self,
        llm_service: Any,
        embedding_service: Any,
        retriever: Any,
        prompt_builder: Any,
        top_k: int = 5,
    ) -> None:
        """Initialize the RAG service.

        Args:
            llm_service: LLMService instance.
            embedding_service: EmbeddingService instance.
            retriever: Retriever instance for vector search.
            prompt_builder: PromptBuilder instance.
            top_k: Default number of documents to retrieve.
        """
        self.llm_service = llm_service
        self.embedding_service = embedding_service
        self.retriever = retriever
        self.prompt_builder = prompt_builder
        self.top_k = top_k

    async def retrieve(
        self,
        query: str,
        top_k: int | None = None,
    ) -> list[dict[str, Any]]:
        """Retrieve relevant documents for a query.

        Embeds the query and searches the vector store for similar documents.

        Args:
            query: Search query text.
            top_k: Number of results (defaults to service-level setting).

        Returns:
            List of source document dicts with content, source, and score.

        Raises:
            RetrievalError: If the retrieval operation fails.
        """
        k = top_k or self.top_k
        try:
            documents = await self.retriever.search(query, top_k=k)
            return documents

        except RetrievalError:
            raise
        except Exception as exc:
            raise RetrievalError(f"Retrieval failed: {exc}")

    async def query(
        self,
        query: str,
        top_k: int | None = None,
        conversation_history: list[dict[str, str]] | None = None,
    ) -> RAGResponse:
        """Execute the full RAG pipeline.

        Flow:
        1. Retrieve relevant documents from the vector store.
        2. Build LLM messages with context injection.
        3. Generate answer via LLM.
        4. Calculate confidence based on document similarity scores.

        Args:
            query: User query text.
            top_k: Number of documents to retrieve.
            conversation_history: Optional prior conversation messages.

        Returns:
            RAGResponse with query, sources, and generated context/answer.

        Raises:
            RetrievalError: If document retrieval fails.
            LLMError: If LLM generation fails.
        """
        k = top_k or self.top_k

        # Step 1: Retrieve documents
        try:
            documents = await self.retriever.search(query, top_k=k)
        except RetrievalError:
            raise
        except Exception as exc:
            raise RetrievalError(f"Retrieval failed: {exc}")

        # Step 2: Build source documents for response
        sources = []
        for doc in documents:
            sources.append(
                SourceDocument(
                    content=doc.get("content", ""),
                    source=doc.get("source", "unknown"),
                    score=doc.get("score", 0.0),
                    metadata=doc.get("metadata", {}),
                )
            )

        # Step 3: Build context text for LLM
        context_parts = []
        for doc in documents:
            context_parts.append(doc.get("content", ""))
        context_text = "\n\n---\n\n".join(context_parts) if context_parts else ""

        # Step 4: Build LLM messages
        messages = self.prompt_builder.build_context(
            query=query,
            documents=documents,
            conversation_history=conversation_history,
        )

        # Step 5: Generate answer
        try:
            answer = await self.llm_service.chat_completion(messages)
        except LLMError:
            raise
        except Exception as exc:
            raise LLMError(f"LLM generation failed: {exc}")

        # Step 6: Calculate confidence based on top document similarity
        confidence = 0.0
        if documents:
            scores = [doc.get("score", 0.0) for doc in documents]
            confidence = sum(scores) / len(scores)

        # Build the combined context (answer + sources)
        full_context = answer

        return RAGResponse(
            query=query,
            sources=sources,
            context=full_context,
            confidence=confidence,
        )

    async def stream_query(
        self,
        query: str,
        top_k: int | None = None,
        conversation_history: list[dict[str, str]] | None = None,
    ):
        """Execute RAG pipeline with streaming response.

        Same as ``query`` but yields SSE-formatted chunks instead of
        returning a complete response.

        Args:
            query: User query text.
            top_k: Number of documents to retrieve.
            conversation_history: Optional prior conversation messages.

        Yields:
            SSE-formatted data lines from the LLM.

        Raises:
            RetrievalError: If document retrieval fails.
        """
        k = top_k or self.top_k

        # Step 1: Retrieve documents
        try:
            documents = await self.retriever.search(query, top_k=k)
        except RetrievalError:
            raise
        except Exception as exc:
            raise RetrievalError(f"Retrieval failed: {exc}")

        # Step 2: Build LLM messages
        messages = self.prompt_builder.build_context(
            query=query,
            documents=documents,
            conversation_history=conversation_history,
        )

        # Step 3: Stream the LLM response (with web_search tool)
        tools = [{"type": "web_search"}]
        async for chunk in self.llm_service.chat(messages, stream=True, tools=tools):
            yield chunk
