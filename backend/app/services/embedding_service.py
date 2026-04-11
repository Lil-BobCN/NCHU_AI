"""DashScope embedding service.

Provides text embedding via the DashScope compatible-mode (OpenAI-compatible)
embedding API. Uses the text-embedding-v3 model by default.
"""
from __future__ import annotations

import asyncio
import json

import httpx

from app.core.exceptions import LLMError


class EmbeddingService:
    """DashScope embedding client with batch support.

    Attributes:
        api_key: DashScope API key.
        model: Embedding model name.
        dimension: Output embedding dimension.
        base_url: DashScope compatible-mode base URL.
    """

    def __init__(
        self,
        api_key: str,
        model: str = "text-embedding-v3",
        dimension: int = 1536,
        base_url: str = "https://dashscope.aliyuncs.com/compatible-mode/v1",
        max_retries: int = 2,
        timeout: int = 30,
    ) -> None:
        """Initialize the embedding service.

        Args:
            api_key: DashScope API key.
            model: Embedding model identifier.
            dimension: Expected embedding dimension.
            base_url: Base URL for the DashScope compatible-mode API.
            max_retries: Maximum retry attempts on transient failures.
            timeout: HTTP timeout in seconds.
        """
        self.api_key = api_key
        self.model = model
        self.dimension = dimension
        self.base_url = base_url.rstrip("/")
        self.max_retries = max_retries
        self.timeout = timeout

    def _headers(self) -> dict[str, str]:
        """Build HTTP headers for embedding API requests."""
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

    async def _embed_single(self, text: str) -> list[float]:
        """Embed a single text string.

        Args:
            text: Input text to embed.

        Returns:
            List of floats representing the embedding vector.

        Raises:
            LLMError: If the API call fails after all retries.
        """
        payload = {
            "model": self.model,
            "input": text,
            "dimensions": self.dimension,
        }
        url = f"{self.base_url}/embeddings"

        for attempt in range(self.max_retries + 1):
            try:
                async with httpx.AsyncClient(timeout=self.timeout) as client:
                    resp = await client.post(
                        url,
                        headers=self._headers(),
                        json=payload,
                    )

                    if resp.status_code != 200:
                        error_msg = (
                            f"Embedding request failed: HTTP {resp.status_code}"
                        )
                        try:
                            error_data = resp.json()
                            if "error" in error_data:
                                error_msg += f" - {error_data['error']}"
                        except (json.JSONDecodeError, ValueError):
                            error_msg += f" - {resp.text[:200]}"
                        raise LLMError(error_msg)

                    data = resp.json()
                    embeddings = data.get("data", [])
                    if not embeddings:
                        raise LLMError("Empty embedding response")

                    sorted_embeddings = sorted(
                        embeddings, key=lambda x: x.get("index", 0)
                    )
                    return sorted_embeddings[0].get("embedding", [])

            except LLMError:
                raise
            except httpx.TimeoutException:
                if attempt < self.max_retries:
                    await asyncio.sleep(0.5 * (attempt + 1))
                    continue
                raise LLMError("Embedding request timed out")
            except httpx.ConnectError:
                if attempt < self.max_retries:
                    await asyncio.sleep(0.5 * (attempt + 1))
                    continue
                raise LLMError("Embedding service connection failed")
            except Exception as exc:
                if attempt < self.max_retries:
                    await asyncio.sleep(0.5 * (attempt + 1))
                    continue
                raise LLMError(f"Embedding request failed: {exc}")

        raise LLMError("Embedding service unavailable after retries")

    async def embed(self, text: str) -> list[float]:
        """Embed a single text string.

        Args:
            text: Input text to embed.

        Returns:
            List of floats representing the embedding vector.

        Raises:
            LLMError: If the API call fails.
        """
        if not text or not text.strip():
            raise LLMError("Cannot embed empty text")
        return await self._embed_single(text.strip())

    async def embed_batch(self, texts: list[str]) -> list[list[float]]:
        """Embed multiple texts in a single batch request.

        DashScope compatible-mode supports batch input, so we send all
        texts in one request for efficiency.

        Args:
            texts: List of input texts to embed.

        Returns:
            List of embedding vectors, in the same order as input texts.

        Raises:
            LLMError: If the API call fails after all retries.
        """
        if not texts:
            return []

        valid_texts = [t.strip() for t in texts if t and t.strip()]
        if not valid_texts:
            raise LLMError("No valid texts to embed")

        payload = {
            "model": self.model,
            "input": valid_texts,
            "dimensions": self.dimension,
        }
        url = f"{self.base_url}/embeddings"

        for attempt in range(self.max_retries + 1):
            try:
                async with httpx.AsyncClient(timeout=self.timeout) as client:
                    resp = await client.post(
                        url,
                        headers=self._headers(),
                        json=payload,
                    )

                    if resp.status_code != 200:
                        error_msg = (
                            f"Batch embedding failed: HTTP {resp.status_code}"
                        )
                        try:
                            error_data = resp.json()
                            if "error" in error_data:
                                error_msg += f" - {error_data['error']}"
                        except (json.JSONDecodeError, ValueError):
                            error_msg += f" - {resp.text[:200]}"
                        raise LLMError(error_msg)

                    data = resp.json()
                    embeddings = data.get("data", [])
                    if not embeddings:
                        raise LLMError("Empty batch embedding response")

                    sorted_embeddings = sorted(
                        embeddings, key=lambda x: x.get("index", 0)
                    )
                    return [e.get("embedding", []) for e in sorted_embeddings]

            except LLMError:
                raise
            except httpx.TimeoutException:
                if attempt < self.max_retries:
                    await asyncio.sleep(0.5 * (attempt + 1))
                    continue
                raise LLMError("Batch embedding request timed out")
            except httpx.ConnectError:
                if attempt < self.max_retries:
                    await asyncio.sleep(0.5 * (attempt + 1))
                    continue
                raise LLMError("Embedding service connection failed")
            except Exception as exc:
                if attempt < self.max_retries:
                    await asyncio.sleep(0.5 * (attempt + 1))
                    continue
                raise LLMError(f"Batch embedding request failed: {exc}")

        raise LLMError("Embedding service unavailable after retries")
