#!/usr/bin/env python3
"""Document ingestion script for NCHU AI Counselor.

Imports school documents (HTML, text, markdown, web pages) into the Qdrant
vector database with embeddings from DashScope text-embedding-v3.

Usage:
    python scripts/ingest_documents.py --source-dir ./docs/nchu --source-type html
    python scripts/ingest_documents.py --url https://xgc.nchu.edu.cn/xxx --source-type web
    python scripts/ingest_documents.py --source-file faq.txt --source-type text
"""
from __future__ import annotations

import argparse
import hashlib
import logging
import os
import re
import sys
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import httpx
from bs4 import BeautifulSoup
from qdrant_client import QdrantClient
from qdrant_client.models import (
    Distance,
    FieldCondition,
    Filter,
    MatchValue,
    PointStruct,
    VectorParams,
)

# ---------------------------------------------------------------------------
# Configuration (from environment, with sensible defaults)
# ---------------------------------------------------------------------------

DASHSCOPE_API_KEY = os.getenv("DASHSCOPE_API_KEY", "")
DASHSCOPE_EMBEDDING_URL = (
    "https://dashscope.aliyuncs.com/compatible-mode/v1/embeddings"
)
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "text-embedding-v3")
EMBEDDING_DIMENSION = 1024  # text-embedding-v3 output dimension

QDRANT_URL = os.getenv("QDRANT_URL", "http://localhost:6333")
QDRANT_COLLECTION = os.getenv("QDRANT_COLLECTION", "nchu_counselor")

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql+asyncpg://postgres:postgres@localhost:5432/nchu_ai_counselor",
)

# Chunking defaults
TARGET_CHUNK_SIZE = 400  # characters
MIN_CHUNK_SIZE = 200  # merge paragraphs below this
OVERLAP_SIZE = 50  # overlap between chunks
SENTENCE_SPLIT_THRESHOLD = 600  # split paragraphs longer than this

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Data structures
# ---------------------------------------------------------------------------


@dataclass
class Document:
    """Represents a source document before chunking."""

    content: str
    doc_id: str  # md5 hash of content
    source: str  # category label
    title: str
    url: str | None = None


@dataclass
class Chunk:
    """A single text chunk ready for embedding."""

    content: str
    doc_id: str
    chunk_index: int
    total_chunks: int
    chunk_hash: str
    metadata: dict[str, Any] = field(default_factory=dict)


# ---------------------------------------------------------------------------
# Embedding service (inline, no dependency on app.services.embedding_service)
# ---------------------------------------------------------------------------


class EmbeddingService:
    """Generate embeddings via DashScope compatible-mode API."""

    def __init__(
        self,
        api_key: str = DASHSCOPE_API_KEY,
        api_url: str = DASHSCOPE_EMBEDDING_URL,
        model: str = EMBEDDING_MODEL,
    ) -> None:
        self.api_key = api_key
        self.api_url = api_url
        self.model = model

    def embed(self, texts: list[str]) -> list[list[float]]:
        """Embed a batch of texts and return vectors."""
        if not self.api_key:
            raise RuntimeError(
                "DASHSCOPE_API_KEY is not set. "
                "Please set it in your .env or environment."
            )

        payload: dict[str, Any] = {
            "model": self.model,
            "input": {"texts": texts},
            "encoding_format": "float",
        }
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        with httpx.Client(timeout=60.0) as client:
            resp = client.post(self.api_url, json=payload, headers=headers)
            resp.raise_for_status()
            data = resp.json()

        # DashScope compatible-mode returns OpenAI-like format
        embeddings: list[list[float]] = [
            item["embedding"] for item in data.get("data", [])
        ]
        return embeddings

    def embed_single(self, text: str) -> list[float]:
        """Embed a single text and return its vector."""
        vectors = self.embed([text])
        return vectors[0]


# ---------------------------------------------------------------------------
# Chunker (inline, no dependency on app.rag.chunker)
# ---------------------------------------------------------------------------


class Chunker:
    """Split document content into overlapping chunks."""

    def __init__(
        self,
        target_size: int = TARGET_CHUNK_SIZE,
        min_size: int = MIN_CHUNK_SIZE,
        overlap: int = OVERLAP_SIZE,
        sentence_threshold: int = SENTENCE_SPLIT_THRESHOLD,
    ) -> None:
        self.target_size = target_size
        self.min_size = min_size
        self.overlap = overlap
        self.sentence_threshold = sentence_threshold

    def chunk(self, document: Document) -> list[Chunk]:
        """Chunk a document and return Chunk objects with metadata."""
        raw_chunks = self._split(document.content)
        total = len(raw_chunks)
        result: list[Chunk] = []

        for idx, text in enumerate(raw_chunks):
            chunk_hash = hashlib.md5(text.encode("utf-8")).hexdigest()
            meta = {
                "doc_id": document.doc_id,
                "source": document.source,
                "title": document.title,
                "url": document.url,
                "chunk_index": idx,
                "total_chunks": total,
                "chunk_hash": chunk_hash,
                "ingested_at": datetime.now(timezone.utc).isoformat(),
            }
            result.append(
                Chunk(
                    content=text,
                    doc_id=document.doc_id,
                    chunk_index=idx,
                    total_chunks=total,
                    chunk_hash=chunk_hash,
                    metadata=meta,
                )
            )
        return result

    def _split(self, text: str) -> list[str]:
        """Split text into chunks using paragraph + sentence strategy."""
        # Split by double newlines (paragraphs)
        paragraphs = re.split(r"\n\s*\n", text)
        paragraphs = [p.strip() for p in paragraphs if p.strip()]

        if not paragraphs:
            return []

        # Step 1: Merge small paragraphs
        merged = self._merge_small(paragraphs)

        # Step 2: Split oversized paragraphs by sentences
        final: list[str] = []
        for para in merged:
            if len(para) > self.sentence_threshold:
                final.extend(self._split_by_sentences(para))
            else:
                final.append(para)

        # Step 3: Ensure chunk sizes are reasonable
        return self._adjust_sizes(final)

    def _merge_small(self, paragraphs: list[str]) -> list[str]:
        """Merge consecutive small paragraphs until min_size is reached."""
        merged: list[str] = []
        buffer = ""

        for para in paragraphs:
            if not buffer:
                buffer = para
                continue

            if len(buffer) < self.min_size:
                buffer = buffer + "\n" + para
            else:
                merged.append(buffer)
                buffer = para

        if buffer:
            merged.append(buffer)

        return merged

    def _split_by_sentences(self, text: str) -> list[str]:
        """Split a long paragraph into sentence-level chunks with overlap."""
        # Chinese sentence boundaries: 。！？；\n
        # English sentence boundaries: . ! ?
        sentences = re.split(r"([。！？；.!?]+\s*)", text)
        # Rejoin sentences with their trailing punctuation
        parts: list[str] = []
        i = 0
        while i < len(sentences):
            sent = sentences[i].strip()
            if i + 1 < len(sentences):
                sent += sentences[i + 1].strip()
                i += 2
            else:
                i += 1
            if sent:
                parts.append(sent)

        if not parts:
            return [text]

        # Group sentences into chunks of approximately target_size
        chunks: list[str] = []
        current = ""
        for part in parts:
            if len(current) + len(part) > self.target_size and current:
                chunks.append(current)
                # Overlap: keep last portion of previous chunk
                overlap_start = max(0, len(current) - self.overlap)
                current = current[overlap_start:] + part
            else:
                current += part

        if current:
            chunks.append(current)

        return chunks

    def _adjust_sizes(self, chunks: list[str]) -> list[str]:
        """Final pass: merge tiny chunks and trim excessively large ones."""
        if not chunks:
            return []

        adjusted: list[str] = []
        for chunk in chunks:
            if len(chunk) < self.min_size and adjusted:
                # Merge into previous chunk
                adjusted[-1] = adjusted[-1] + "\n" + chunk
            elif len(chunk) > self.target_size * 2:
                # Hard split for very large chunks
                for i in range(0, len(chunk), self.target_size):
                    adjusted.append(chunk[i : i + self.target_size])
            else:
                adjusted.append(chunk)

        return adjusted


# ---------------------------------------------------------------------------
# Document readers
# ---------------------------------------------------------------------------


def read_html_file(filepath: str | Path) -> Document:
    """Read and clean an HTML file into a Document."""
    path = Path(filepath)
    content = path.read_text(encoding="utf-8", errors="replace")
    soup = BeautifulSoup(content, "html.parser")

    # Extract title
    title_tag = soup.find("title")
    title = title_tag.get_text(strip=True) if title_tag else path.stem

    # Strip tags and normalize whitespace
    text = soup.get_text(separator="\n")
    text = _clean_text(text)

    doc_id = hashlib.md5(text.encode("utf-8")).hexdigest()
    return Document(
        content=text,
        doc_id=doc_id,
        source="nchu_html",
        title=title,
        url=None,
    )


def read_text_file(filepath: str | Path) -> Document:
    """Read a plain text or markdown file into a Document."""
    path = Path(filepath)
    text = path.read_text(encoding="utf-8", errors="replace")
    text = _clean_text(text)

    doc_id = hashlib.md5(text.encode("utf-8")).hexdigest()
    return Document(
        content=text,
        doc_id=doc_id,
        source="nchu_text",
        title=path.stem,
        url=None,
    )


def read_webpage(url: str) -> Document:
    """Fetch and clean a webpage into a Document."""
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/120.0.0.0 Safari/537.36"
        )
    }

    with httpx.Client(timeout=30.0, follow_redirects=True) as client:
        resp = client.get(url, headers=headers)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "html.parser")

    title_tag = soup.find("title")
    title = title_tag.get_text(strip=True) if title_tag else url

    text = soup.get_text(separator="\n")
    text = _clean_text(text)

    doc_id = hashlib.md5(text.encode("utf-8")).hexdigest()
    return Document(
        content=text,
        doc_id=doc_id,
        source="nchu_web",
        title=title,
        url=url,
    )


def _clean_text(text: str) -> str:
    """Normalize whitespace and remove empty lines."""
    # Collapse multiple newlines into double newlines
    text = re.sub(r"\n{3,}", "\n\n", text)
    # Remove lines that are only whitespace
    lines = [line.strip() for line in text.splitlines()]
    lines = [line for line in lines if line]
    return "\n".join(lines).strip()


# ---------------------------------------------------------------------------
# Qdrant storage
# ---------------------------------------------------------------------------


def ensure_collection(client: QdrantClient, collection_name: str) -> None:
    """Create collection if it doesn't exist."""
    collections = [c.name for c in client.get_collections().collections]
    if collection_name not in collections:
        client.create_collection(
            collection_name=collection_name,
            vectors_config=VectorParams(
                size=EMBEDDING_DIMENSION,
                distance=Distance.COSINE,
            ),
        )
        logger.info("Created collection: %s", collection_name)
    else:
        logger.info("Collection already exists: %s", collection_name)


def upsert_chunks(
    client: QdrantClient,
    collection_name: str,
    chunks: list[Chunk],
    embeddings: list[list[float]],
) -> None:
    """Upsert chunked embeddings to Qdrant (idempotent by point ID)."""
    points = []
    for chunk, vector in zip(chunks, embeddings):
        # Point ID = doc_id + chunk_index for idempotent upserts
        point_id = f"{chunk.doc_id}_{chunk.chunk_index}"
        points.append(
            PointStruct(
                id=point_id,
                vector=vector,
                payload=chunk.metadata,
            )
        )

    client.upsert(collection_name=collection_name, points=points)
    logger.info("  Upserted %d chunks to Qdrant", len(points))


def delete_existing_doc(
    client: QdrantClient, collection_name: str, doc_id: str
) -> None:
    """Delete all chunks for a given doc_id (for re-ingestion)."""
    client.delete(
        collection_name=collection_name,
        points_selector=Filter(
            must=[
                FieldCondition(
                    key="doc_id", match=MatchValue(value=doc_id)
                )
            ]
        ),
    )


# ---------------------------------------------------------------------------
# PostgreSQL metadata recording (optional, best-effort)
# ---------------------------------------------------------------------------


def record_metadata_in_postgres(
    document: Document, chunks: list[Chunk], db_url: str
) -> None:
    """Record ingestion metadata in PostgreSQL (best-effort, non-blocking)."""
    try:
        import asyncpg  # type: ignore[import-not-found]
    except ImportError:
        logger.debug("asyncpg not available, skipping metadata recording")
        return

    # Parse asyncpg-compatible URL from SQLAlchemy-style URL
    pg_url = db_url.replace("postgresql+asyncpg://", "postgresql://")

    async def _record() -> None:
        conn = await asyncpg.connect(pg_url)
        try:
            # Ensure table exists
            await conn.execute(
                """
                CREATE TABLE IF NOT EXISTS document_ingestion_log (
                    doc_id TEXT PRIMARY KEY,
                    source TEXT,
                    title TEXT,
                    url TEXT,
                    total_chunks INTEGER,
                    ingested_at TIMESTAMPTZ
                )
                """
            )
            await conn.execute(
                """
                INSERT INTO document_ingestion_log
                    (doc_id, source, title, url, total_chunks, ingested_at)
                VALUES ($1, $2, $3, $4, $5, $6)
                ON CONFLICT (doc_id) DO UPDATE SET
                    source = EXCLUDED.source,
                    title = EXCLUDED.title,
                    url = EXCLUDED.url,
                    total_chunks = EXCLUDED.total_chunks,
                    ingested_at = EXCLUDED.ingested_at
                """,
                document.doc_id,
                document.source,
                document.title,
                document.url,
                len(chunks),
                datetime.now(timezone.utc),
            )
        finally:
            await conn.close()

    try:
        import asyncio

        asyncio.run(_record())
        logger.info("  Metadata recorded in PostgreSQL")
    except Exception as e:
        logger.warning("  Failed to record metadata in PostgreSQL: %s", e)


# ---------------------------------------------------------------------------
# Main ingestion pipeline
# ---------------------------------------------------------------------------


class IngestionPipeline:
    """End-to-end pipeline: read -> chunk -> embed -> store."""

    def __init__(self) -> None:
        self.embedding_service = EmbeddingService()
        self.chunker = Chunker()
        self.qdrant_client = QdrantClient(url=QDRANT_URL)
        self.batch_size = 32  # embeddings per API call

    def ingest_document(self, document: Document) -> int:
        """Ingest a single document. Returns number of chunks stored."""
        logger.info(
            "Processing: %s (id=%s, source=%s)",
            document.title,
            document.doc_id[:8],
            document.source,
        )

        # Step 1: Delete existing chunks for idempotency
        delete_existing_doc(self.qdrant_client, QDRANT_COLLECTION, document.doc_id)

        # Step 2: Chunk
        chunks = self.chunker.chunk(document)
        logger.info("  Chunked into %d pieces", len(chunks))

        if not chunks:
            logger.warning("  No chunks generated, skipping")
            return 0

        # Step 3: Embed in batches
        all_embeddings: list[list[float]] = []
        for i in range(0, len(chunks), self.batch_size):
            batch = [c.content for c in chunks[i : i + self.batch_size]]
            batch_embeddings = self.embedding_service.embed(batch)
            all_embeddings.extend(batch_embeddings)
            elapsed = (i + len(batch)) / len(chunks) * 100
            logger.info("  Embedding progress: %d/%d (%.0f%%)", i + len(batch), len(chunks), elapsed)
            # Be polite to the API
            time.sleep(0.2)

        # Step 4: Upsert to Qdrant
        upsert_chunks(self.qdrant_client, QDRANT_COLLECTION, chunks, all_embeddings)

        # Step 5: Record metadata (best-effort)
        record_metadata_in_postgres(document, chunks, DATABASE_URL)

        return len(chunks)

    def ingest_documents(self, documents: list[Document]) -> dict[str, int]:
        """Ingest multiple documents. Returns summary stats."""
        total_docs = len(documents)
        total_chunks = 0
        failed = 0

        logger.info("=" * 60)
        logger.info("Starting ingestion of %d documents", total_docs)
        logger.info("=" * 60)

        for idx, doc in enumerate(documents, 1):
            try:
                logger.info("[%d/%d]", idx, total_docs)
                n = self.ingest_document(doc)
                total_chunks += n
            except Exception as e:
                logger.error(
                    "Failed to ingest '%s': %s", doc.title, e, exc_info=True
                )
                failed += 1

        logger.info("=" * 60)
        logger.info(
            "Done! %d docs processed, %d failed, %d chunks stored",
            total_docs - failed,
            failed,
            total_chunks,
        )
        logger.info("=" * 60)

        return {"total_docs": total_docs, "failed": failed, "total_chunks": total_chunks}


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Ingest documents into NCHU AI Counselor vector database",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )

    # Source selection (mutually exclusive)
    source_group = parser.add_mutually_exclusive_group(required=True)
    source_group.add_argument(
        "--source-dir",
        help="Directory containing source files to ingest",
    )
    source_group.add_argument(
        "--source-file",
        help="Single file to ingest",
    )
    source_group.add_argument(
        "--url",
        help="URL to scrape and ingest",
    )

    parser.add_argument(
        "--source-type",
        required=True,
        choices=["html", "text", "web"],
        help="Type of source data",
    )
    parser.add_argument(
        "--source-label",
        default="nchu_website",
        help="Source category label for metadata (default: nchu_website)",
    )
    parser.add_argument(
        "--collection",
        default=QDRANT_COLLECTION,
        help=f"Qdrant collection name (default: {QDRANT_COLLECTION})",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be ingested without actually storing",
    )

    return parser.parse_args()


def load_documents_from_dir(
    directory: str, source_type: str, source_label: str
) -> list[Document]:
    """Load all matching files from a directory."""
    dir_path = Path(directory)
    if not dir_path.is_dir():
        logger.error("Directory not found: %s", directory)
        sys.exit(1)

    ext_map = {"html": ["*.html", "*.htm"], "text": ["*.txt", "*.md"]}
    extensions = ext_map.get(source_type, ["*"])

    documents: list[Document] = []
    for ext in extensions:
        for filepath in dir_path.glob(ext):
            try:
                if source_type == "html":
                    doc = read_html_file(filepath)
                else:
                    doc = read_text_file(filepath)
                doc.source = source_label
                documents.append(doc)
            except Exception as e:
                logger.warning("Skipping %s: %s", filepath, e)

    logger.info("Found %d documents in %s", len(documents), directory)
    return documents


def main() -> None:
    args = parse_args()

    # Override collection if specified
    global QDRANT_COLLECTION
    if args.collection:
        QDRANT_COLLECTION = args.collection

    # Load documents
    documents: list[Document] = []

    if args.source_dir:
        documents = load_documents_from_dir(
            args.source_dir, args.source_type, args.source_label
        )
    elif args.source_file:
        filepath = Path(args.source_file)
        if not filepath.exists():
            logger.error("File not found: %s", args.source_file)
            sys.exit(1)
        if args.source_type == "html":
            doc = read_html_file(filepath)
        else:
            doc = read_text_file(filepath)
        doc.source = args.source_label
        documents = [doc]
    elif args.url:
        try:
            doc = read_webpage(args.url)
            doc.source = args.source_label
            documents = [doc]
        except Exception as e:
            logger.error("Failed to fetch URL %s: %s", args.url, e)
            sys.exit(1)

    if not documents:
        logger.warning("No documents to ingest. Exiting.")
        return

    # Dry run
    if args.dry_run:
        logger.info("DRY RUN - would ingest %d documents:", len(documents))
        for doc in documents:
            chunker = Chunker()
            chunks = chunker.chunk(doc)
            logger.info(
                "  %s -> %d chunks (id=%s)", doc.title, len(chunks), doc.doc_id[:8]
            )
        return

    # Run pipeline
    pipeline = IngestionPipeline()
    ensure_collection(pipeline.qdrant_client, QDRANT_COLLECTION)
    pipeline.ingest_documents(documents)


if __name__ == "__main__":
    main()
