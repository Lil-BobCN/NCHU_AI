"""Milvus vector store retriever for RAG.

This module is the formal Phase 1 vector-store path. The older Qdrant ingest
script remains in the repository only as migration reference material until the
Milvus smoke gate is stable.
"""
from __future__ import annotations

import asyncio
import json
import uuid
from typing import Any

from app.core.exceptions import RetrievalError


class Retriever:
    """Milvus vector store wrapper for RAG retrieval."""

    def __init__(
        self,
        milvus_client: Any,
        embedding_service: Any,
        collection_name: str = "nchu_counselor_documents",
        vector_dim: int = 1024,
        metric_type: str = "COSINE",
        index_type: str = "IVF_FLAT",
        index_nlist: int = 1024,
    ) -> None:
        """Initialize the retriever."""
        self.client = milvus_client
        self.embedding_service = embedding_service
        self.collection_name = collection_name
        self.vector_dim = vector_dim
        self.metric_type = metric_type
        self.index_type = index_type
        self.index_nlist = index_nlist

    async def _call(self, method_name: str, *args: Any, **kwargs: Any) -> Any:
        """Run a synchronous PyMilvus client call off the event loop."""
        method = getattr(self.client, method_name)
        return await asyncio.to_thread(method, *args, **kwargs)

    async def ensure_collection(self) -> None:
        """Create the Milvus collection and vector index if needed."""
        try:
            exists = await self._call("has_collection", self.collection_name)
            if exists:
                return

            from pymilvus import DataType, MilvusClient

            schema = MilvusClient.create_schema(
                auto_id=False,
                enable_dynamic_field=True,
            )
            schema.add_field(
                field_name="id",
                datatype=DataType.VARCHAR,
                is_primary=True,
                max_length=64,
            )
            schema.add_field(
                field_name="vector",
                datatype=DataType.FLOAT_VECTOR,
                dim=self.vector_dim,
            )
            schema.add_field(
                field_name="content",
                datatype=DataType.VARCHAR,
                max_length=65535,
            )
            schema.add_field(
                field_name="source",
                datatype=DataType.VARCHAR,
                max_length=1024,
            )

            await self._call(
                "create_collection",
                collection_name=self.collection_name,
                schema=schema,
            )

            index_params = self.client.prepare_index_params()
            index_params.add_index(
                field_name="vector",
                index_type=self.index_type,
                metric_type=self.metric_type,
                params={"nlist": self.index_nlist},
            )
            await self._call(
                "create_index",
                collection_name=self.collection_name,
                index_params=index_params,
                sync=True,
            )
        except Exception as exc:
            raise RetrievalError(
                f"Milvus collection initialization failed: {exc}"
            ) from exc

    async def search(
        self,
        query: str,
        top_k: int = 5,
        filters: dict[str, Any] | None = None,
    ) -> list[dict[str, Any]]:
        """Embed the query and perform TopK similarity search in Milvus."""
        try:
            await self.ensure_collection()
            query_vector = await self.embedding_service.embed(query)
            expr = self._build_filter_expr(filters)
            await self._call("load_collection", self.collection_name, replica_number=1)

            results = await self._call(
                "search",
                collection_name=self.collection_name,
                data=[query_vector],
                anns_field="vector",
                search_params={"metric_type": self.metric_type},
                limit=top_k,
                filter=expr,
                output_fields=["content", "source"],
            )
            return self._format_search_results(results)
        except RetrievalError:
            raise
        except Exception as exc:
            raise RetrievalError(f"Milvus vector search failed: {exc}") from exc

    async def add_documents(self, documents: list[dict[str, Any]]) -> list[str]:
        """Add documents to the Milvus collection."""
        if not documents:
            return []

        try:
            await self.ensure_collection()
            texts = [doc.get("content", "") for doc in documents]
            embeddings = await self.embedding_service.embed_batch(texts)

            rows = []
            doc_ids = []
            for index, doc in enumerate(documents):
                doc_id = str(uuid.uuid4())
                doc_ids.append(doc_id)
                metadata = doc.get("metadata", {}) or {}
                rows.append(
                    {
                        "id": doc_id,
                        "vector": embeddings[index],
                        "content": doc.get("content", ""),
                        "source": metadata.get("source", doc.get("source", "unknown")),
                        "metadata_json": json.dumps(metadata, ensure_ascii=False),
                    }
                )

            await self._call(
                "insert",
                collection_name=self.collection_name,
                data=rows,
            )
            await self._call("flush", collection_name=self.collection_name)
            return doc_ids
        except RetrievalError:
            raise
        except Exception as exc:
            raise RetrievalError(f"Milvus document insertion failed: {exc}") from exc

    async def delete_documents(self, doc_ids: list[str]) -> bool:
        """Delete documents from Milvus by primary key."""
        if not doc_ids:
            return True

        try:
            quoted_ids = ", ".join(json.dumps(doc_id) for doc_id in doc_ids)
            await self._call(
                "delete",
                collection_name=self.collection_name,
                filter=f"id in [{quoted_ids}]",
            )
            return True
        except RetrievalError:
            raise
        except Exception as exc:
            raise RetrievalError(f"Milvus document deletion failed: {exc}") from exc

    async def count(self) -> int:
        """Get the approximate number of entities in the collection."""
        try:
            info = await self._call("describe_collection", self.collection_name)
            return int(info.get("num_entities", 0))
        except RetrievalError:
            raise
        except Exception as exc:
            raise RetrievalError(f"Milvus document count failed: {exc}") from exc

    def _build_filter_expr(self, filters: dict[str, Any] | None) -> str | None:
        """Build a simple Milvus scalar filter expression from equality filters."""
        if not filters:
            return None
        conditions = []
        for key, value in filters.items():
            if value is None:
                continue
            safe_key = "".join(ch for ch in key if ch.isalnum() or ch == "_")
            if not safe_key:
                continue
            conditions.append(f"{safe_key} == {json.dumps(value)}")
        return " and ".join(conditions) if conditions else None

    def _format_search_results(self, results: Any) -> list[dict[str, Any]]:
        """Normalize PyMilvus search results into the service response shape."""
        hits = results[0] if results else []
        documents = []
        for hit in hits:
            if isinstance(hit, dict):
                entity = hit.get("entity") or {}
                score = hit.get("distance", hit.get("score", 0.0))
            else:
                entity = getattr(hit, "entity", {}) or {}
                score = getattr(hit, "distance", getattr(hit, "score", 0.0))
            documents.append(
                {
                    "content": entity.get("content", ""),
                    "source": entity.get("source", "unknown"),
                    "score": float(score),
                    "metadata": {
                        key: value
                        for key, value in entity.items()
                        if key not in {"content", "source", "vector"}
                    },
                }
            )
        return documents
