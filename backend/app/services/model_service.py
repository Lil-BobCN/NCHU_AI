"""
模型调用服务。封装 OpenAI-compatible Chat 与 Embedding 客户端，并处理 embedding 缓存。
"""

from collections.abc import AsyncGenerator
import hashlib

from openai import AsyncOpenAI

from app.core.concurrency import embedding_call_slot, model_call_slot
from app.core.config import get_settings
from app.services.redis_service import RedisService


_openai_clients: dict[tuple, AsyncOpenAI] = {}


def _openai_client(
    *,
    api_key: str,
    base_url: str,
    timeout: float,
    max_retries: int,
) -> AsyncOpenAI:
    key = (api_key, base_url, float(timeout), int(max_retries))
    client = _openai_clients.get(key)
    if client is None:
        client = AsyncOpenAI(
            api_key=api_key,
            base_url=base_url,
            timeout=timeout,
            max_retries=max_retries,
        )
        _openai_clients[key] = client
    return client


async def close_model_clients() -> None:
    clients = list(_openai_clients.values())
    _openai_clients.clear()
    for client in clients:
        await client.close()


class ModelService:
    def __init__(self) -> None:
        self.settings = get_settings()
        self.chat_client = _openai_client(
            api_key=self.settings.deepseek_api_key or "missing",
            base_url=self.settings.deepseek_base_url,
            timeout=self.settings.model_request_timeout_seconds,
            max_retries=max(0, self.settings.model_request_retries),
        )
        self.embedding_client = _openai_client(
            api_key=self.settings.embedding_api_key or self.settings.deepseek_api_key or "missing",
            base_url=self.settings.embedding_base_url,
            timeout=self.settings.model_request_timeout_seconds,
            max_retries=max(0, self.settings.model_request_retries),
        )
        self.redis_service = RedisService()

    async def embed(self, texts: list[str]) -> list[list[float]]:
        if not texts:
            return []
        cached = await self._get_cached_embeddings(texts)
        missing = [(index, text) for index, (text, embedding) in enumerate(zip(texts, cached, strict=True)) if embedding is None]
        if not missing:
            return [embedding for embedding in cached if embedding is not None]

        batch_size = max(1, self.settings.embedding_batch_size)
        embeddings: list[list[float] | None] = list(cached)
        missing_texts = [text for _, text in missing]
        missing_indices = [index for index, _ in missing]
        generated: list[list[float]] = []
        for start in range(0, len(missing_texts), batch_size):
            async with embedding_call_slot():
                response = await self.embedding_client.embeddings.create(
                    model=self.settings.embedding_model,
                    input=missing_texts[start : start + batch_size],
                )
            generated.extend(item.embedding for item in response.data)
        for index, embedding in zip(missing_indices, generated, strict=True):
            embeddings[index] = embedding
        await self._set_cached_embeddings(
            [text for _, text in missing],
            generated,
        )
        return [embedding for embedding in embeddings if embedding is not None]

    async def chat(self, messages: list[dict], stream: bool = False):
        if stream:
            return await self.chat_client.chat.completions.create(
                model=self.settings.chat_model,
                messages=messages,
                stream=True,
            )
        async with model_call_slot():
            return await self.chat_client.chat.completions.create(
                model=self.settings.chat_model,
                messages=messages,
                stream=False,
            )

    async def stream_answer(self, messages: list[dict]) -> AsyncGenerator[str, None]:
        async with model_call_slot():
            stream = await self.chat(messages, stream=True)
            async for event in stream:
                delta = event.choices[0].delta.content if event.choices else None
                if delta:
                    yield delta

    async def complete_text(self, messages: list[dict]) -> str:
        response = await self.chat(messages, stream=False)
        return response.choices[0].message.content or ""

    async def _get_cached_embeddings(self, texts: list[str]) -> list[list[float] | None]:
        if not self.settings.embedding_cache_enabled:
            return [None] * len(texts)
        results: list[list[float] | None] = []
        for text in texts:
            try:
                cached = await self.redis_service.get_json(self._embedding_cache_key(text))
                results.append(cached if isinstance(cached, list) else None)
            except Exception:
                results.append(None)
        return results

    async def _set_cached_embeddings(self, texts: list[str], embeddings: list[list[float]]) -> None:
        if not self.settings.embedding_cache_enabled:
            return
        ttl = max(1, self.settings.embedding_cache_ttl_seconds)
        for text, embedding in zip(texts, embeddings, strict=True):
            try:
                await self.redis_service.set_json(self._embedding_cache_key(text), embedding, ttl=ttl)
            except Exception:
                continue

    def _embedding_cache_key(self, text: str) -> str:
        digest = hashlib.sha256(text.encode("utf-8")).hexdigest()
        return f"embedding:{self.settings.embedding_model}:{digest}"
