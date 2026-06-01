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
class ChatModelRunOptions:
    web_search: bool | None = None
    profile: str | None = None
    mode: str | None = None


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

    @classmethod
    def citation(cls, citation: dict[str, Any]) -> ChatModelStreamEvent:
        return cls("citation", citation)

    @classmethod
    def notice(cls, code: str, detail: str) -> ChatModelStreamEvent:
        return cls("notice", {"code": code, "detail": detail})

    @classmethod
    def tool_started(
        cls,
        tool_name: str,
        *,
        tool_call_id: str,
        title: str,
    ) -> ChatModelStreamEvent:
        return cls(
            "tool_started",
            {
                "toolCallId": tool_call_id,
                "toolName": tool_name,
                "title": title,
            },
        )

    @classmethod
    def tool_delta(
        cls,
        tool_name: str,
        *,
        tool_call_id: str,
        detail: str,
        metadata: dict[str, Any] | None = None,
    ) -> ChatModelStreamEvent:
        data: dict[str, Any] = {
            "toolCallId": tool_call_id,
            "toolName": tool_name,
            "detail": detail,
        }
        if metadata:
            data["metadata"] = metadata
        return cls("tool_delta", data)

    @classmethod
    def tool_done(
        cls,
        tool_name: str,
        *,
        tool_call_id: str,
        status: str,
        detail: str,
        result_count: int | None = None,
    ) -> ChatModelStreamEvent:
        data: dict[str, Any] = {
            "toolCallId": tool_call_id,
            "toolName": tool_name,
            "status": status,
            "detail": detail,
        }
        if result_count is not None:
            data["resultCount"] = result_count
        return cls("tool_done", data)


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

    async def stream_reply(
        self,
        messages: list[ChatModelMessage],
        options: ChatModelRunOptions | None = None,
    ) -> AsyncIterator[str]:
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

    async def stream_reply(
        self,
        messages: list[ChatModelMessage],
        options: ChatModelRunOptions | None = None,
    ) -> AsyncIterator[str]:
        async for event in self.stream_events(messages, options):
            if event.type == "delta":
                content = event.data.get("content")
                if isinstance(content, str) and content:
                    yield content

    async def stream_events(
        self,
        messages: list[ChatModelMessage],
        options: ChatModelRunOptions | None = None,
    ) -> AsyncIterator[ChatModelStreamEvent]:
        if not self.configured:
            raise ChatModelConfigurationError(
                "Qwen model configuration is missing. Set DASHSCOPE_API_KEY and "
                "DASHSCOPE_MODEL, or the legacy QWEN_API_KEY and QWEN_MODEL aliases."
            )

        if self._api_mode == "generation":
            async for event in self._stream_generation_events(messages, options):
                yield event
            return

        async for event in self._stream_compatible_events(messages, options):
            yield event

    async def _stream_compatible_events(
        self,
        messages: list[ChatModelMessage],
        options: ChatModelRunOptions | None,
    ) -> AsyncIterator[ChatModelStreamEvent]:
        payload = self._build_payload(messages, options)
        search_enabled = "enable_search" in payload
        search_tool_call_id = "dashscope-web-search"
        if search_enabled:
            yield ChatModelStreamEvent.tool_started(
                "web_search",
                tool_call_id=search_tool_call_id,
                title="DashScope web search",
            )
            yield ChatModelStreamEvent.tool_delta(
                "web_search",
                tool_call_id=search_tool_call_id,
                detail="Search request sent to DashScope.",
                metadata={"strategy": self._web_search_strategy},
            )
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
                            if search_enabled:
                                yield ChatModelStreamEvent.tool_done(
                                    "web_search",
                                    tool_call_id=search_tool_call_id,
                                    status="error",
                                    detail=str(event.data["message"]),
                                )
                            raise ChatModelProviderError(str(event.data["message"]))
                        yield event
                if search_enabled:
                    yield ChatModelStreamEvent.tool_done(
                        "web_search",
                        tool_call_id=search_tool_call_id,
                        status="success",
                        detail="Provider search completed without source details.",
                    )
        except httpx.HTTPError as exc:
            raise ChatModelProviderError(f"Qwen provider request failed: {exc}") from exc

    async def _stream_generation_events(
        self,
        messages: list[ChatModelMessage],
        options: ChatModelRunOptions | None,
    ) -> AsyncIterator[ChatModelStreamEvent]:
        payload = self._build_generation_payload(messages, options)
        search_enabled = bool(payload["parameters"].get("enable_search"))
        search_tool_call_id = "dashscope-web-search"
        source_count = 0
        if search_enabled:
            yield ChatModelStreamEvent.tool_started(
                "web_search",
                tool_call_id=search_tool_call_id,
                title="DashScope web search",
            )
            yield ChatModelStreamEvent.tool_delta(
                "web_search",
                tool_call_id=search_tool_call_id,
                detail="Search request sent to DashScope.",
                metadata={
                    "strategy": self._web_search_strategy,
                    "sourceEnabled": self._search_source_enabled,
                    "citationEnabled": self._search_citation_enabled,
                },
            )
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
                            if search_enabled:
                                yield ChatModelStreamEvent.tool_done(
                                    "web_search",
                                    tool_call_id=search_tool_call_id,
                                    status="error",
                                    detail=str(event.data["message"]),
                                )
                            raise ChatModelProviderError(str(event.data["message"]))
                        if event.type == "source":
                            key = self._source_key(event.data)
                            if key in seen_sources:
                                continue
                            seen_sources.add(key)
                            source_count += 1
                        yield event
                if search_enabled:
                    yield ChatModelStreamEvent.tool_done(
                        "web_search",
                        tool_call_id=search_tool_call_id,
                        status="success" if source_count else "no_results",
                        detail=(
                            f"Provider returned {source_count} source(s)."
                            if source_count
                            else "Provider search completed without source details."
                        ),
                        result_count=source_count,
                    )
        except httpx.HTTPError as exc:
            raise ChatModelProviderError(f"Qwen provider request failed: {exc}") from exc

    def _build_payload(
        self,
        messages: list[ChatModelMessage],
        options: ChatModelRunOptions | None = None,
    ) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "model": self._model,
            "messages": self._build_messages(messages),
            "max_tokens": self._max_tokens,
            "stream": True,
            "enable_thinking": self._enable_thinking,
        }
        if self._should_use_web_search(messages, options):
            payload["enable_search"] = True
            payload["search_options"] = {
                "search_strategy": self._web_search_strategy,
            }
        return payload

    def _build_generation_payload(
        self,
        messages: list[ChatModelMessage],
        options: ChatModelRunOptions | None = None,
    ) -> dict[str, Any]:
        parameters: dict[str, Any] = {
            "result_format": "message",
            "incremental_output": True,
            "max_tokens": self._max_tokens,
            "enable_thinking": self._enable_thinking,
        }
        if self._should_use_web_search(messages, options):
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

    def _should_use_web_search(
        self,
        messages: list[ChatModelMessage],
        options: ChatModelRunOptions | None,
    ) -> bool:
        if not self._web_search_enabled:
            return False
        if options and options.web_search is not None:
            return options.web_search
        return self._should_enable_web_search(messages)

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
        events: list[ChatModelStreamEvent] = []
        events.extend(DashScopeChatModelProvider._citation_events(payload))
        events.extend(DashScopeChatModelProvider._citation_events(choices[0]))
        delta = choices[0].get("delta") or {}
        events.extend(DashScopeChatModelProvider._citation_events(delta))
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
        events.extend(DashScopeChatModelProvider._citation_events(search_info))
        events.extend(DashScopeChatModelProvider._citation_events(output))

        choices = output.get("choices") or []
        if not choices:
            return events
        message = choices[0].get("message") or {}
        events.extend(DashScopeChatModelProvider._citation_events(message))
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
    def _citation_events(payload: Any) -> list[ChatModelStreamEvent]:
        if not isinstance(payload, dict):
            return []
        raw_citations = payload.get("citations") or payload.get("citation")
        if raw_citations is None:
            return []
        if isinstance(raw_citations, dict):
            raw_citations = [raw_citations]
        if not isinstance(raw_citations, list):
            return []
        events: list[ChatModelStreamEvent] = []
        for raw_citation in raw_citations:
            normalized = DashScopeChatModelProvider._normalize_citation(raw_citation)
            if normalized:
                events.append(ChatModelStreamEvent.citation(normalized))
        return events

    @staticmethod
    def _normalize_citation(citation: Any) -> dict[str, Any] | None:
        if not isinstance(citation, dict):
            return None
        normalized: dict[str, Any] = {}
        for source_key, event_key in (
            ("id", "citationId"),
            ("citation_id", "citationId"),
            ("marker", "marker"),
            ("ref", "marker"),
            ("text", "text"),
            ("title", "title"),
            ("url", "url"),
            ("link", "url"),
            ("snippet", "snippet"),
            ("source_id", "sourceId"),
            ("sourceId", "sourceId"),
            ("source_index", "sourceIndex"),
            ("sourceIndex", "sourceIndex"),
            ("index", "sourceIndex"),
        ):
            value = citation.get(source_key)
            if value not in (None, "") and event_key not in normalized:
                normalized[event_key] = value
        return normalized or None

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
