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


@dataclass(frozen=True, slots=True)
class ChatModelStreamEvent:
    type: str
    data: dict[str, Any]

    @classmethod
    def delta(cls, content: str) -> ChatModelStreamEvent:
        return cls("delta", {"content": content})

    @classmethod
    def phase(cls, phase: str) -> ChatModelStreamEvent:
        return cls("phase", {"phase": phase})

    @classmethod
    def reasoning(cls, content: str) -> ChatModelStreamEvent:
        return cls("reasoning", {"content": content})

    @classmethod
    def source(cls, source: dict[str, Any]) -> ChatModelStreamEvent:
        return cls("source", source)


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
        self._compatible_base_url = settings.dashscope_api_base_url.strip().rstrip("/")
        self._native_base_url = settings.dashscope_native_api_base_url.strip().rstrip("/")
        self._api_mode = settings.dashscope_api_mode
        self._compatible_model = settings.dashscope_model.strip()
        self._native_model = settings.dashscope_native_model.strip()
        self._model = (
            self._native_model
            if self._api_mode == "generation"
            else self._compatible_model
        )
        self._timeout_seconds = settings.chat_model_timeout_seconds
        self._max_tokens = settings.chat_model_max_tokens
        self._system_prompt = settings.chat_model_system_prompt.strip()
        self._enable_thinking = settings.enable_thinking
        self._web_search_enabled = settings.chat_model_web_search_enabled
        self._web_search_strategy = settings.chat_model_web_search_strategy
        self._search_source_enabled = settings.chat_model_search_source_enabled
        self._search_citation_enabled = settings.chat_model_search_citation_enabled
        self._search_prepend_results = settings.chat_model_search_prepend_results
        self._search_citation_format = settings.chat_model_search_citation_format

    @property
    def configured(self) -> bool:
        base_url = (
            self._native_base_url
            if self._api_mode == "generation"
            else self._compatible_base_url
        )
        return bool(self._api_key and base_url and self._model)

    async def stream_reply(self, messages: list[ChatModelMessage]) -> AsyncIterator[str]:
        async for event in self.stream_events(messages):
            if event.type == "delta":
                content = event.data.get("content")
                if isinstance(content, str) and content:
                    yield content

    async def stream_events(
        self,
        messages: list[ChatModelMessage],
    ) -> AsyncIterator[ChatModelStreamEvent]:
        if not self.configured:
            raise ChatModelConfigurationError(
                "Qwen model configuration is missing. Set DASHSCOPE_API_KEY and "
                "DASHSCOPE_MODEL, or the legacy QWEN_API_KEY and QWEN_MODEL aliases."
            )

        if self._api_mode == "generation":
            async for event in self._stream_generation_events(messages):
                yield event
            return

        async for event in self._stream_compatible_events(messages):
            yield event

    async def _stream_compatible_events(
        self,
        messages: list[ChatModelMessage],
    ) -> AsyncIterator[ChatModelStreamEvent]:
        payload = self._build_payload(messages)
        if "enable_search" in payload:
            yield ChatModelStreamEvent.phase("searching")
        yield ChatModelStreamEvent.phase("generating")

        timeout = httpx.Timeout(self._timeout_seconds)
        headers = {
            "Authorization": f"Bearer {self._api_key}",
            "Content-Type": "application/json",
        }

        try:
            async with httpx.AsyncClient(timeout=timeout) as client, client.stream(
                "POST",
                f"{self._compatible_base_url}/chat/completions",
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
                    for event in self._parse_compatible_sse_line(line):
                        if event.type == "provider_error":
                            raise ChatModelProviderError(str(event.data["message"]))
                        yield event
        except httpx.HTTPError as exc:
            raise ChatModelProviderError(f"Qwen provider request failed: {exc}") from exc

    async def _stream_generation_events(
        self,
        messages: list[ChatModelMessage],
    ) -> AsyncIterator[ChatModelStreamEvent]:
        payload = self._build_generation_payload(messages)
        if payload["parameters"].get("enable_search"):
            yield ChatModelStreamEvent.phase("searching")
        yield ChatModelStreamEvent.phase("generating")

        timeout = httpx.Timeout(self._timeout_seconds)
        headers = {
            "Authorization": f"Bearer {self._api_key}",
            "Content-Type": "application/json",
            "X-DashScope-SSE": "enable",
        }
        seen_sources: set[str] = set()

        try:
            async with httpx.AsyncClient(timeout=timeout) as client, client.stream(
                "POST",
                f"{self._native_base_url}/services/aigc/text-generation/generation",
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
                    for event in self._parse_generation_sse_line(line):
                        if event.type == "provider_error":
                            raise ChatModelProviderError(str(event.data["message"]))
                        if event.type == "source":
                            key = self._source_key(event.data)
                            if key in seen_sources:
                                continue
                            seen_sources.add(key)
                        yield event
        except httpx.HTTPError as exc:
            raise ChatModelProviderError(f"Qwen provider request failed: {exc}") from exc

    def _build_payload(self, messages: list[ChatModelMessage]) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "model": self._model,
            "messages": self._build_messages(messages),
            "max_tokens": self._max_tokens,
            "stream": True,
            "enable_thinking": self._enable_thinking,
        }
        if self._web_search_enabled and self._should_enable_web_search(messages):
            payload["enable_search"] = True
            payload["search_options"] = {
                "search_strategy": self._web_search_strategy,
            }
        return payload

    def _build_generation_payload(self, messages: list[ChatModelMessage]) -> dict[str, Any]:
        parameters: dict[str, Any] = {
            "result_format": "message",
            "incremental_output": True,
            "max_tokens": self._max_tokens,
            "enable_thinking": self._enable_thinking,
        }
        if self._web_search_enabled and self._should_enable_web_search(messages):
            parameters["enable_search"] = True
            parameters["search_options"] = {
                "search_strategy": self._web_search_strategy,
                "enable_source": self._search_source_enabled,
                "enable_citation": self._search_citation_enabled,
                "citation_format": self._search_citation_format,
                "prepend_search_result": self._search_prepend_results,
            }
        return {
            "model": self._model,
            "input": {"messages": self._build_messages(messages)},
            "parameters": parameters,
        }

    def _build_messages(self, messages: list[ChatModelMessage]) -> list[dict[str, str]]:
        rendered = [{"role": "system", "content": self._system_prompt}]
        rendered.extend({"role": item.role, "content": item.content} for item in messages)
        return rendered

    @staticmethod
    def _should_enable_web_search(messages: list[ChatModelMessage]) -> bool:
        latest_user_message = next(
            (item.content for item in reversed(messages) if item.role == "user"),
            "",
        )
        text = latest_user_message.strip().lower()
        if not text:
            return False

        explicit_search_terms = (
            "联网",
            "搜索",
            "检索",
            "查一下",
            "帮我查",
            "网上",
            "官网",
            "网址",
            "链接",
            "新闻",
            "最新",
            "实时",
            "search",
            "web",
            "internet",
            "online",
            "official site",
            "url",
            "link",
            "news",
            "latest",
            "real-time",
        )
        if any(term in text for term in explicit_search_terms):
            return True

        temporal_terms = (
            "今天",
            "现在",
            "当前",
            "今年",
            "本周",
            "today",
            "current",
            "this week",
            "this year",
        )
        fact_terms = (
            "政策",
            "通知",
            "公告",
            "分数线",
            "招生",
            "排名",
            "比赛",
            "考试安排",
            "录取",
            "policy",
            "notice",
            "announcement",
            "admission",
            "ranking",
            "schedule",
        )
        return any(term in text for term in temporal_terms) and any(
            term in text for term in fact_terms
        )

    @staticmethod
    def _parse_sse_line(line: str) -> str:
        for event in DashScopeChatModelProvider._parse_compatible_sse_line(line):
            if event.type == "delta":
                content = event.data.get("content")
                return content if isinstance(content, str) else ""
        return ""

    @staticmethod
    def _parse_compatible_sse_line(line: str) -> list[ChatModelStreamEvent]:
        if not line.startswith("data:"):
            return []
        data = line.removeprefix("data:").strip()
        if not data or data == "[DONE]":
            return []
        try:
            payload = json.loads(data)
        except json.JSONDecodeError:
            return []
        provider_error = DashScopeChatModelProvider._provider_error_event(payload)
        if provider_error:
            return [provider_error]
        choices = payload.get("choices") or []
        if not choices:
            return []
        delta = choices[0].get("delta") or {}
        events: list[ChatModelStreamEvent] = []
        reasoning = delta.get("reasoning_content")
        if isinstance(reasoning, str) and reasoning:
            events.append(ChatModelStreamEvent.reasoning(reasoning))
        content = delta.get("content")
        if isinstance(content, str) and content:
            events.append(ChatModelStreamEvent.delta(content))
        return events

    @staticmethod
    def _parse_generation_sse_line(line: str) -> list[ChatModelStreamEvent]:
        if not line.startswith("data:"):
            return []
        data = line.removeprefix("data:").strip()
        if not data or data == "[DONE]":
            return []
        try:
            payload = json.loads(data)
        except json.JSONDecodeError:
            return []
        provider_error = DashScopeChatModelProvider._provider_error_event(payload)
        if provider_error:
            return [provider_error]

        events: list[ChatModelStreamEvent] = []
        output = payload.get("output") or {}
        search_info = output.get("search_info") or {}
        for source in search_info.get("search_results") or []:
            normalized = DashScopeChatModelProvider._normalize_search_source(source)
            if normalized:
                events.append(ChatModelStreamEvent.source(normalized))

        choices = output.get("choices") or []
        if not choices:
            return events
        message = choices[0].get("message") or {}
        reasoning = message.get("reasoning_content")
        if isinstance(reasoning, str) and reasoning:
            events.append(ChatModelStreamEvent.reasoning(reasoning))
        content = message.get("content")
        if isinstance(content, str) and content:
            events.append(ChatModelStreamEvent.delta(content))
        return events

    @staticmethod
    def _normalize_search_source(source: Any) -> dict[str, Any] | None:
        if not isinstance(source, dict):
            return None
        title = source.get("title") or source.get("site_name") or source.get("hostname")
        url = source.get("url") or source.get("link")
        if not isinstance(title, str) or not title.strip():
            title = "Untitled source"
        if not isinstance(url, str) or not url.strip():
            return None
        normalized: dict[str, Any] = {
            "title": title.strip(),
            "url": url.strip(),
        }
        for source_key, event_key in (
            ("snippet", "snippet"),
            ("content", "snippet"),
            ("index", "index"),
            ("site_name", "siteName"),
            ("hostname", "hostname"),
            ("publish_time", "publishedAt"),
            ("date", "publishedAt"),
        ):
            value = source.get(source_key)
            if value not in (None, "") and event_key not in normalized:
                normalized[event_key] = value
        return normalized

    @staticmethod
    def _source_key(source: dict[str, Any]) -> str:
        url = source.get("url")
        if isinstance(url, str) and url:
            return url
        title = source.get("title")
        return title if isinstance(title, str) else json.dumps(source, sort_keys=True)

    @staticmethod
    def _provider_error_event(payload: Any) -> ChatModelStreamEvent | None:
        if not isinstance(payload, dict):
            return None
        code = payload.get("code")
        message = payload.get("message")
        if not isinstance(message, str) or not message:
            return None
        data: dict[str, Any] = {"message": message}
        if isinstance(code, str) and code:
            data["code"] = code
        request_id = payload.get("request_id")
        if isinstance(request_id, str) and request_id:
            data["requestId"] = request_id
        return ChatModelStreamEvent("provider_error", data)
