"""Qwen/DashScope streaming chat provider for Phase 3R."""
from __future__ import annotations

import json
from collections.abc import AsyncIterator
from dataclasses import dataclass
from ipaddress import ip_address
from typing import Any, Protocol
from urllib.parse import urlparse

import httpx

from app.config import Settings


@dataclass(frozen=True, slots=True)
class ChatModelMessage:
    role: str
    content: str
    partial: bool = False


@dataclass(frozen=True, slots=True)
class ChatModelRunOptions:
    web_search: bool | None = None
    reasoning_enabled: bool | None = None
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
        self._responses_model = settings.dashscope_responses_model.strip()
        self._model = self._select_model()
        self._timeout_seconds = settings.chat_model_timeout_seconds
        self._max_tokens = settings.chat_model_max_tokens
        self._system_prompt = settings.chat_model_system_prompt.strip()
        self._enable_thinking = settings.enable_thinking
        self._reasoning_effort = settings.chat_model_reasoning_effort
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

    def _select_model(self) -> str:
        if self._api_mode == "generation":
            return self._native_model
        if self._api_mode == "responses":
            return self._responses_model
        return self._compatible_model

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

        if self._api_mode == "responses":
            async for event in self._stream_responses_events(messages, options):
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

    async def _stream_responses_events(
        self,
        messages: list[ChatModelMessage],
        options: ChatModelRunOptions | None,
    ) -> AsyncIterator[ChatModelStreamEvent]:
        payload = self._build_responses_payload(messages, options)
        yield ChatModelStreamEvent.phase("thinking")

        timeout = httpx.Timeout(self._timeout_seconds)
        headers = {
            "Authorization": f"Bearer {self._api_key}",
            "Content-Type": "application/json",
        }

        try:
            async with httpx.AsyncClient(timeout=timeout) as client, client.stream(
                "POST",
                f"{self._compatible_base_url}/responses",
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
                    for event in self._parse_responses_sse_line(line):
                        if event.type == "provider_error":
                            raise ChatModelProviderError(str(event.data["message"]))
                        yield event
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
            "enable_thinking": self._thinking_enabled(options),
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
            "enable_thinking": self._thinking_enabled(options),
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

    def _build_responses_payload(
        self,
        messages: list[ChatModelMessage],
        options: ChatModelRunOptions | None = None,
    ) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "model": self._model,
            "input": self._build_responses_input(messages),
            "max_output_tokens": self._max_tokens,
            "stream": True,
            "reasoning": {
                "effort": self._responses_reasoning_effort(options),
                "summary": "auto",
            },
        }
        if self._should_use_web_search(messages, options):
            payload["tools"] = [{"type": "web_search"}]
        return payload

    def _build_messages(self, messages: list[ChatModelMessage]) -> list[dict[str, Any]]:
        rendered: list[dict[str, Any]] = [
            {"role": "system", "content": self._system_prompt}
        ]
        for item in messages:
            message: dict[str, Any] = {"role": item.role, "content": item.content}
            if item.partial:
                message["partial"] = True
            rendered.append(message)
        return rendered

    def _build_responses_input(self, messages: list[ChatModelMessage]) -> list[dict[str, str]]:
        rendered = [{"role": "system", "content": self._system_prompt}]
        rendered.extend({"role": item.role, "content": item.content} for item in messages)
        return rendered

    def _thinking_enabled(self, options: ChatModelRunOptions | None) -> bool:
        if options and options.reasoning_enabled is not None:
            return options.reasoning_enabled
        return self._enable_thinking

    def _responses_reasoning_effort(self, options: ChatModelRunOptions | None) -> str:
        if options and options.reasoning_enabled is False:
            return "none"
        if not self._thinking_enabled(options):
            return "none"
        mode = (options.mode if options else None) or ""
        if mode == "fast":
            return "minimal"
        if mode == "focus":
            return "high"
        return self._reasoning_effort

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
        choice = choices[0]
        events.extend(DashScopeChatModelProvider._finish_reason_events(choice))
        delta = choice.get("delta") or {}
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
        choice = choices[0]
        events.extend(DashScopeChatModelProvider._finish_reason_events(choice))
        message = choice.get("message") or {}
        events.extend(DashScopeChatModelProvider._citation_events(message))
        reasoning = message.get("reasoning_content")
        if isinstance(reasoning, str) and reasoning:
            events.append(ChatModelStreamEvent.reasoning(reasoning))
        content = message.get("content")
        if isinstance(content, str) and content:
            events.append(ChatModelStreamEvent.delta(content))
        return events

    @staticmethod
    def _parse_responses_sse_line(line: str) -> list[ChatModelStreamEvent]:
        if not line.startswith("data:"):
            return []
        data = line.removeprefix("data:").strip()
        if not data or data == "[DONE]":
            return []
        try:
            payload = json.loads(data)
        except json.JSONDecodeError:
            return []
        provider_error = DashScopeChatModelProvider._responses_provider_error_event(payload)
        if provider_error:
            return [provider_error]

        event_type = payload.get("type")
        events: list[ChatModelStreamEvent] = []
        if event_type in {"response.created", "response.in_progress"}:
            return [ChatModelStreamEvent.phase("thinking")]
        if event_type == "response.reasoning_summary_text.delta":
            delta = payload.get("delta")
            return (
                [ChatModelStreamEvent.reasoning(delta)]
                if isinstance(delta, str) and delta
                else []
            )
        if event_type == "response.output_text.delta":
            delta = payload.get("delta")
            return [ChatModelStreamEvent.delta(delta)] if isinstance(delta, str) and delta else []
        if event_type == "response.output_item.added":
            return DashScopeChatModelProvider._responses_output_item_events(
                payload.get("item"),
                status="started",
            )
        if event_type == "response.output_item.done":
            return DashScopeChatModelProvider._responses_output_item_events(
                payload.get("item"),
                status="done",
            )
        if isinstance(event_type, str) and event_type.startswith("response.web_search_call."):
            return DashScopeChatModelProvider._responses_web_search_event(payload, event_type)
        if event_type == "response.completed":
            response = payload.get("response")
            if isinstance(response, dict):
                for item in response.get("output") or []:
                    if isinstance(item, dict) and str(item.get("type", "")).endswith("_call"):
                        events.extend(
                            DashScopeChatModelProvider._responses_output_item_events(
                                item,
                                status="done",
                            )
                        )
                    elif isinstance(item, dict) and item.get("type") == "message":
                        events.extend(
                            DashScopeChatModelProvider._responses_message_reference_events(item)
                        )
            return events
        return events

    @staticmethod
    def _responses_output_item_events(
        item: Any,
        *,
        status: str,
    ) -> list[ChatModelStreamEvent]:
        if not isinstance(item, dict):
            return []
        item_type = item.get("type")
        if item_type == "message":
            return DashScopeChatModelProvider._responses_message_reference_events(item)
        if item_type == "reasoning":
            text = DashScopeChatModelProvider._responses_text_from_item(item)
            return [ChatModelStreamEvent.reasoning(text)] if text else []
        if not isinstance(item_type, str) or not item_type.endswith("_call"):
            return []

        tool_name = DashScopeChatModelProvider._responses_tool_name(item_type)
        tool_call_id = DashScopeChatModelProvider._responses_tool_call_id(item)
        title = DashScopeChatModelProvider._responses_tool_title(tool_name)
        if status == "started":
            return [
                ChatModelStreamEvent.tool_started(
                    tool_name,
                    tool_call_id=tool_call_id,
                    title=title,
                )
            ]

        events: list[ChatModelStreamEvent] = []
        sources = DashScopeChatModelProvider._responses_sources_from_item(item)
        events.extend(ChatModelStreamEvent.source(source) for source in sources)
        events.append(
            ChatModelStreamEvent.tool_done(
                tool_name,
                tool_call_id=tool_call_id,
                status="success" if sources or tool_name != "web_search" else "no_results",
                detail=DashScopeChatModelProvider._responses_tool_done_detail(tool_name, sources),
                result_count=len(sources) if sources else None,
            )
        )
        return events

    @staticmethod
    def _responses_web_search_event(
        payload: dict[str, Any],
        event_type: str,
    ) -> list[ChatModelStreamEvent]:
        tool_call_id = str(payload.get("item_id") or payload.get("id") or "responses-web-search")
        if event_type.endswith(".in_progress"):
            return [
                ChatModelStreamEvent.tool_started(
                    "web_search",
                    tool_call_id=tool_call_id,
                    title="Responses web search",
                )
            ]
        if event_type.endswith(".searching"):
            return [
                ChatModelStreamEvent.phase("searching"),
                ChatModelStreamEvent.tool_delta(
                    "web_search",
                    tool_call_id=tool_call_id,
                    detail="Responses API is searching the web.",
                ),
            ]
        if event_type.endswith(".completed"):
            return [
                ChatModelStreamEvent.tool_done(
                    "web_search",
                    tool_call_id=tool_call_id,
                    status="success",
                    detail="Responses API web search completed.",
                )
            ]
        return []

    @staticmethod
    def _responses_message_reference_events(item: dict[str, Any]) -> list[ChatModelStreamEvent]:
        events: list[ChatModelStreamEvent] = []
        for content_item in item.get("content") or []:
            if not isinstance(content_item, dict):
                continue
            for annotation in content_item.get("annotations") or []:
                normalized_source = (
                    DashScopeChatModelProvider._normalize_response_annotation_source(annotation)
                )
                if normalized_source:
                    events.append(ChatModelStreamEvent.source(normalized_source))
                normalized_citation = DashScopeChatModelProvider._normalize_citation(annotation)
                if normalized_citation:
                    events.append(ChatModelStreamEvent.citation(normalized_citation))
        return events

    @staticmethod
    def _responses_sources_from_item(item: dict[str, Any]) -> list[dict[str, Any]]:
        raw_sources = (
            item.get("sources")
            or item.get("search_results")
            or (item.get("action") or {}).get("sources")
            or (item.get("action") or {}).get("search_results")
            or []
        )
        sources: list[dict[str, Any]] = []
        if isinstance(raw_sources, list):
            for raw_source in raw_sources:
                normalized = DashScopeChatModelProvider._normalize_search_source(raw_source)
                if normalized:
                    sources.append(normalized)
        return sources

    @staticmethod
    def _normalize_response_annotation_source(annotation: Any) -> dict[str, Any] | None:
        if not isinstance(annotation, dict):
            return None
        if annotation.get("type") not in {"url_citation", "citation"}:
            return None
        normalized = DashScopeChatModelProvider._normalize_search_source(annotation)
        if normalized:
            return normalized
        url = annotation.get("url")
        if not isinstance(url, str) or not url:
            return None
        return {
            "title": annotation.get("title") or url,
            "url": url,
            "snippet": annotation.get("text") or annotation.get("snippet"),
        }

    @staticmethod
    def _responses_tool_name(item_type: str) -> str:
        return item_type.removesuffix("_call")

    @staticmethod
    def _responses_tool_title(tool_name: str) -> str:
        labels = {
            "web_search": "Responses web search",
            "web_extractor": "Responses web extractor",
            "function": "Responses function call",
            "code_interpreter": "Responses code interpreter",
        }
        return labels.get(tool_name, tool_name.replace("_", " ").title())

    @staticmethod
    def _responses_tool_done_detail(tool_name: str, sources: list[dict[str, Any]]) -> str:
        if tool_name == "web_search":
            return (
                f"Responses API returned {len(sources)} source(s)."
                if sources
                else "Responses API web search completed without source details."
            )
        return f"{DashScopeChatModelProvider._responses_tool_title(tool_name)} completed."

    @staticmethod
    def _responses_tool_call_id(item: dict[str, Any]) -> str:
        raw_id = item.get("id") or item.get("call_id") or item.get("callId")
        return str(raw_id) if raw_id else "responses-tool-call"

    @staticmethod
    def _responses_text_from_item(item: dict[str, Any]) -> str:
        summary = item.get("summary")
        if isinstance(summary, str):
            return summary
        if isinstance(summary, list):
            parts = []
            for entry in summary:
                if isinstance(entry, str):
                    parts.append(entry)
                elif isinstance(entry, dict) and isinstance(entry.get("text"), str):
                    parts.append(entry["text"])
            return "".join(parts)
        text = item.get("text")
        return text if isinstance(text, str) else ""

    @staticmethod
    def _responses_provider_error_event(payload: Any) -> ChatModelStreamEvent | None:
        provider_error = DashScopeChatModelProvider._provider_error_event(payload)
        if provider_error:
            return provider_error
        if not isinstance(payload, dict):
            return None
        error = payload.get("error")
        if not isinstance(error, dict):
            response = payload.get("response")
            error = response.get("error") if isinstance(response, dict) else None
        if not isinstance(error, dict):
            return None
        message = error.get("message") or error.get("detail") or error.get("code")
        if not isinstance(message, str) or not message:
            return None
        data: dict[str, Any] = {"message": message}
        code = error.get("code") or error.get("type")
        if isinstance(code, str) and code:
            data["code"] = code
        return ChatModelStreamEvent("provider_error", data)

    @staticmethod
    def _normalize_search_source(source: Any) -> dict[str, Any] | None:
        if not isinstance(source, dict):
            return None
        title = source.get("title") or source.get("site_name") or source.get("hostname")
        url = source.get("url") or source.get("link")
        if not isinstance(url, str) or not url.strip():
            return None
        parsed_url = urlparse(url.strip())
        hostname = (parsed_url.hostname or "").strip().lower()
        if not DashScopeChatModelProvider._is_public_source_url(parsed_url.scheme, hostname):
            return None
        if not isinstance(title, str) or not title.strip():
            title = DashScopeChatModelProvider._source_display_title(parsed_url)
        normalized: dict[str, Any] = {
            "title": title.strip(),
            "displayTitle": title.strip(),
            "display_title": title.strip(),
            "url": url.strip(),
            "hostname": hostname,
            "sourceQuality": "public_web",
            "trustLabel": "Public web source",
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
    def _source_display_title(parsed_url: Any) -> str:
        hostname = (parsed_url.hostname or "").strip().lower()
        path_parts = [
            part.replace("-", " ").replace("_", " ").strip()
            for part in parsed_url.path.split("/")
            if part.strip()
        ]
        if path_parts:
            leaf = path_parts[-1].rsplit(".", 1)[0].strip()
            if leaf:
                return f"{hostname} / {leaf}" if hostname else leaf
        return hostname or "Public web source"

    @staticmethod
    def _is_public_source_url(scheme: str, hostname: str) -> bool:
        if scheme not in {"http", "https"} or not hostname:
            return False
        if hostname in {"localhost", "localhost.localdomain"} or hostname.endswith(".local"):
            return False
        try:
            address = ip_address(hostname)
        except ValueError:
            return True
        return not (
            address.is_private
            or address.is_loopback
            or address.is_link_local
            or address.is_multicast
            or address.is_reserved
            or address.is_unspecified
        )

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
    def _finish_reason_events(choice: Any) -> list[ChatModelStreamEvent]:
        if not isinstance(choice, dict):
            return []
        finish_reason = choice.get("finish_reason") or choice.get("finishReason")
        if finish_reason not in {"length", "max_tokens"}:
            return []
        return [
            ChatModelStreamEvent.notice(
                "model_output_truncated",
                "Provider stopped because the configured output token budget was reached.",
            )
        ]

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
