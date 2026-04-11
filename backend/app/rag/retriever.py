"""Qdrant vector store retriever for RAG.

Wraps the qdrant-client library to provide async similarity search,
document ingestion, and collection management.
"""
from __future__ import annotations

from typing import Any

from qdrant_client import AsyncQdrantClient
from qdrant_client.models import (
    Distance,
    FieldCondition,
    Filter,
    MatchValue,
    PayloadSchemaType,
    PointStruct,
    VectorParams,
)

from app.core.exceptions import RetrievalError


class Retriever:
    """Qdrant vector store wrapper for RAG retrieval.

    Attributes:
        client: Async Qdrant client instance.
        embedding_service: Service for generating embedding vectors.
        collection_name: Qdrant collection to operate on.
    """

    def __init__(
        self,
        qdrant_client: AsyncQdrantClient,
        embedding_service: Any,
        collection_name: str = "nchu_counselor",
        vector_size: int = 1536,
    ) -> None:
        """Initialize the retriever.

        Args:
            qdrant_client: Async Qdrant client instance.
            embedding_service: EmbeddingService instance for vector generation.
            collection_name: Qdrant collection name.
            vector_size: Embedding vector dimension.
        """
        self.client = qdrant_client
        self.embedding_service = embedding_service
        self.collection_name = collection_name
        self.vector_size = vector_size

    async def ensure_collection(self) -> None:
        """Create the Qdrant collection if it does not exist.

        Configures the collection with cosine distance and creates
        payload indexes for common metadata fields.
        """
        collections = await self.client.get_collections()
        collection_names = [c.name for c in collections.collections]

        if self.collection_name not in collection_names:
            await self.client.create_collection(
                collection_name=self.collection_name,
                vectors_config=VectorParams(
                    size=self.vector_size,
                    distance=Distance.COSINE,
                ),
            )

            # Create payload indexes for filtering
            for field in ("source", "category", "college"):
                await self.client.create_payload_index(
                    collection_name=self.collection_name,
                    field_name=field,
                    field_schema=PayloadSchemaType.KEYWORD,
                )

    async def search(
        self,
        query: str,
        top_k: int = 5,
        filters: dict[str, Any] | None = None,
    ) -> list[dict[str, Any]]:
        """Perform similarity search against the vector store.

        Embeds the query text, then searches for the top_k most similar
        documents in Qdrant.

        Args:
            query: Search query text.
            top_k: Number of results to return.
            filters: Optional metadata filters (e.g., {"source": "policy.pdf"}).

        Returns:
            List of dicts with ``content``, ``source``, ``score``, and ``metadata``.

        Raises:
            RetrievalError: If the search operation fails.
        """
        try:
            # Embed the query
            query_vector = await self.embedding_service.embed(query)

            # Build filter if provided
            qdrant_filter = None
            if filters:
                conditions = [
                    FieldCondition(key=key, match=MatchValue(value=value))
                    for key, value in filters.items()
                    if value is not None
                ]
                if conditions:
                    qdrant_filter = Filter(must=conditions)

            # Search
            results = await self.client.query_points(
                collection_name=self.collection_name,
                query=query_vector,
                query_filter=qdrant_filter,
                limit=top_k,
                with_payload=True,
            )

            # Format results
            documents = []
            for hit in results.points:
                payload = hit.payload or {}
                documents.append(
                    {
                        "content": payload.get("content", ""),
                        "source": payload.get("source", "unknown"),
                        "score": float(hit.score),
                        "metadata": {
                            k: v
                            for k, v in payload.items()
                            if k not in ("content", "source")
                        },
                    }
                )

            return documents

        except RetrievalError:
            raise
        except Exception as exc:
            raise RetrievalError(f"Vector search failed: {exc}")

    async def add_documents(self, documents: list[dict[str, Any]]) -> list[str]:
        """Add documents to the vector store.

        Each document should have ``content`` and optional ``metadata``.
        Embeddings are generated for each document before insertion.

        Args:
            documents: List of dicts with ``content`` and optional ``metadata``.

        Returns:
            List of Qdrant point IDs for the inserted documents.

        Raises:
            RetrievalError: If the insertion fails.
        """
        if not documents:
            return []

        try:
            # Extract texts and generate embeddings in batch
            texts = [doc.get("content", "") for doc in documents]
            embeddings = await self.embedding_service.embed_batch(texts)

            # Build points
            import uuid

            points = []
            for i, doc in enumerate(documents):
                point_id = str(uuid.uuid4())
                payload = {
                    "content": doc.get("content", ""),
                    **doc.get("metadata", {}),
                }
                # Ensure source field exists
                if "source" not in payload:
                    payload["source"] = "unknown"

                points.append(
                    PointStruct(
                        id=point_id,
                        vector=embeddings[i],
                        payload=payload,
                    )
                )

            # Upsert into Qdrant
            await self.client.upsert(
                collection_name=self.collection_name,
                points=points,
            )

            return [p.id for p in points]

        except RetrievalError:
            raise
        except Exception as exc:
            raise RetrievalError(f"Document insertion failed: {exc}")

    async def delete_documents(self, doc_ids: list[str]) -> bool:
        """Delete documents from the vector store by Qdrant point ID.

        Args:
            doc_ids: List of Qdrant point IDs to delete.

        Returns:
            True if deletion succeeded.

        Raises:
            RetrievalError: If the deletion fails.
        """
        if not doc_ids:
            return True

        try:
            await self.client.delete(
                collection_name=self.collection_name,
                points_selector=doc_ids,
            )
            return True

        except RetrievalError:
            raise
        except Exception as exc:
            raise RetrievalError(f"Document deletion failed: {exc}")

    async def count(self) -> int:
        """Get the total number of documents in the collection.

        Returns:
            Document count.

        Raises:
            RetrievalError: If the count operation fails.
        """
        try:
            info = await self.client.get_collection(
                collection_name=self.collection_name
            )
            return info.points_count
        except RetrievalError:
            raise
        except Exception as exc:
            raise RetrievalError(f"Document count failed: {exc}")
