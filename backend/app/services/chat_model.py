"""Qwen/DashScope streaming chat provider for Phase 3R."""
from __future__ import annotations

import json
from collections.abc import AsyncIterator
from dataclasses import dataclass
from typing import Any, Protocol

import httpx

from app.config import Settings


@dataclass(frozen=True, slots=True)
class ChatModelMessage:
    role: str
    content: str


class ChatModelError(RuntimeError):
    """Base error for model proxy failures."""


class ChatModelConfigurationError(ChatModelError):
    """Raised when model provider configuration is missing."""


class ChatModelProviderError(ChatModelError):
    """Raised when the upstream model provider fails."""


class ChatModelProvider(Protocol):
    @property
    def configured(self) -> bool:
        """Return whether the provider has enough settings to call upstream."""

    async def stream_reply(self, messages: list[ChatModelMessage]) -> AsyncIterator[str]:
        """Yield assistant response chunks."""
        ...


class DashScopeChatModelProvider:
    """OpenAI-compatible DashScope chat-completions streaming adapter."""

    def __init__(self, settings: Settings) -> None:
        self._api_key = settings.dashscope_api_key.strip()
        self._base_url = settings.dashscope_api_base_url.strip().rstrip("/")
        self._model = settings.dashscope_model.strip()
        self._timeout_seconds = settings.chat_model_timeout_seconds
        self._system_prompt = settings.chat_model_system_prompt.strip()
        self._enable_thinking = settings.enable_thinking

    @property
    def configured(self) -> bool:
        return bool(self._api_key and self._base_url and self._model)

    async def stream_reply(self, messages: list[ChatModelMessage]) -> AsyncIterator[str]:
        if not self.configured:
            raise ChatModelConfigurationError(
                "Qwen model configuration is missing. Set DASHSCOPE_API_KEY and "
                "DASHSCOPE_MODEL, or the legacy QWEN_API_KEY and QWEN_MODEL aliases."
            )

        payload: dict[str, Any] = {
            "model": self._model,
            "messages": self._build_messages(messages),
            "stream": True,
        }
        if self._enable_thinking:
            payload["enable_thinking"] = True

        timeout = httpx.Timeout(self._timeout_seconds)
        headers = {
            "Authorization": f"Bearer {self._api_key}",
            "Content-Type": "application/json",
        }

        try:
            async with httpx.AsyncClient(timeout=timeout) as client, client.stream(
                "POST",
                f"{self._base_url}/chat/completions",
                headers=headers,
                json=payload,
            ) as response:
                if response.status_code >= 400:
                    detail = await response.aread()
                    raise ChatModelProviderError(
                        f"Qwen provider returned HTTP {response.status_code}: "
                        f"{detail.decode('utf-8', errors='ignore')[:300]}"
                    )
                async for line in response.aiter_lines():
                    chunk = self._parse_sse_line(line)
                    if chunk:
                        yield chunk
        except httpx.HTTPError as exc:
            raise ChatModelProviderError(f"Qwen provider request failed: {exc}") from exc

    def _build_messages(self, messages: list[ChatModelMessage]) -> list[dict[str, str]]:
        rendered = [{"role": "system", "content": self._system_prompt}]
        rendered.extend({"role": item.role, "content": item.content} for item in messages)
        return rendered

    @staticmethod
    def _parse_sse_line(line: str) -> str:
        if not line.startswith("data:"):
            return ""
        data = line.removeprefix("data:").strip()
        if not data or data == "[DONE]":
            return ""
        try:
            payload = json.loads(data)
        except json.JSONDecodeError:
            return ""
        choices = payload.get("choices") or []
        if not choices:
            return ""
        delta = choices[0].get("delta") or {}
        content = delta.get("content")
        return content if isinstance(content, str) else ""
