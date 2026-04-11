"""Text chunking for document ingestion.

Splits documents into overlapping chunks suitable for vector embedding
and retrieval. Supports paragraph-level and sentence-level splitting.
"""
from __future__ import annotations

import re
from typing import Any


class Chunker:
    """Splits text into overlapping chunks for RAG ingestion.

    Attributes:
        chunk_size: Target number of characters per chunk.
        overlap: Number of overlapping characters between chunks.
    """

    def __init__(
        self,
        chunk_size: int = 512,
        overlap: int = 50,
    ) -> None:
        """Initialize the chunker.

        Args:
            chunk_size: Target characters per chunk.
            overlap: Overlapping characters between consecutive chunks.
        """
        self.chunk_size = chunk_size
        self.overlap = overlap

    def _split_paragraphs(self, text: str) -> list[str]:
        """Split text into paragraphs.

        Args:
            text: Input text.

        Returns:
            List of paragraph strings.
        """
        paragraphs = re.split(r"\n\s*\n", text)
        return [p.strip() for p in paragraphs if p.strip()]

    def _split_sentences(self, text: str) -> list[str]:
        """Split text into sentences.

        Handles Chinese and English sentence boundaries.

        Args:
            text: Input text.

        Returns:
            List of sentence strings.
        """
        # Split on common sentence terminators in both Chinese and English
        sentences = re.split(
            r"(?<=[。！？.?!\n])\s*",
            text,
        )
        return [s.strip() for s in sentences if s.strip()]

    def chunk(
        self,
        text: str,
        metadata: dict[str, Any] | None = None,
    ) -> list[dict[str, Any]]:
        """Chunk text into retrieval-sized pieces.

        Strategy:
        1. Split into paragraphs first.
        2. If a paragraph fits within chunk_size, keep it whole.
        3. If a paragraph exceeds chunk_size, split into sentences and
           greedily group sentences into chunks.

        Args:
            text: Input text to chunk.
            metadata: Optional metadata to attach to each chunk.

        Returns:
            List of dicts with ``content``, ``metadata``, and ``chunk_index``.
        """
        if not text or not text.strip():
            return []

        base_metadata = metadata or {}
        paragraphs = self._split_paragraphs(text)
        chunks: list[dict[str, Any]] = []
        chunk_index = 0

        for paragraph in paragraphs:
            para_len = len(paragraph)

            # Paragraph fits within a single chunk
            if para_len <= self.chunk_size:
                chunks.append(
                    {
                        "content": paragraph,
                        "metadata": {**base_metadata},
                        "chunk_index": chunk_index,
                    }
                )
                chunk_index += 1
                continue

            # Paragraph too large — split into sentences and regroup
            sentences = self._split_sentences(paragraph)
            current_chunk = ""

            for sentence in sentences:
                # If adding this sentence exceeds the chunk size, emit current
                if current_chunk and len(current_chunk) + len(sentence) > self.chunk_size:
                    chunks.append(
                        {
                            "content": current_chunk,
                            "metadata": {**base_metadata},
                            "chunk_index": chunk_index,
                        }
                    )
                    chunk_index += 1

                    # Start next chunk with overlap from previous
                    if self.overlap > 0 and current_chunk:
                        overlap_start = max(0, len(current_chunk) - self.overlap)
                        current_chunk = current_chunk[overlap_start:] + " " + sentence
                    else:
                        current_chunk = sentence
                else:
                    if current_chunk:
                        current_chunk += " " + sentence
                    else:
                        current_chunk = sentence

            # Emit remaining chunk
            if current_chunk:
                chunks.append(
                    {
                        "content": current_chunk,
                        "metadata": {**base_metadata},
                        "chunk_index": chunk_index,
                    }
                )
                chunk_index += 1

        return chunks
