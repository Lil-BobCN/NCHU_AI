"""Student self-service routes for Q&A, resources, and conversations."""
from __future__ import annotations

import asyncio
import json
import time
from collections.abc import AsyncIterator
from datetime import UTC, datetime
from ipaddress import ip_address
from typing import Annotated, Any
from urllib.parse import urlparse
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse

from app.api.v1.deps import chat_model_provider, current_user
from app.config import Settings, get_settings
from app.schemas.business import (
    ConversationCreate,
    ConversationMessageCreate,
    ConversationResponse,
    QuestionRequest,
    QuestionResponse,
    ResourceResponse,
    StudentChatRequest,
)
from app.services.business import Conversation, MessageAttachment, User, store
from app.services.chat_model import (
    ChatModelConfigurationError,
    ChatModelError,
    ChatModelMessage,
    ChatModelProvider,
    ChatModelRunOptions,
    ChatModelStreamEvent,
)
from app.services.sandbox import StudentCodeSandboxRunner

router = APIRouter(prefix="/student", tags=["student"])
MAX_OUTPUT_CONTINUATION_ATTEMPTS = 3


@router.post("/questions", response_model=QuestionResponse)
async def ask_question(
    payload: QuestionRequest,
    user: Annotated[User, Depends(current_user)],
) -> QuestionResponse:
    """Ask the counselor assistant a student-facing question."""
    message = store.answer_question(user.id, payload.question)
    return QuestionResponse(answer=message.content, resources=message.resources)


@router.post("/chat/stream")
async def stream_student_chat(
    payload: StudentChatRequest,
    user: Annotated[User, Depends(current_user)],
    provider: Annotated[ChatModelProvider, Depends(chat_model_provider)],
    settings: Annotated[Settings, Depends(get_settings)],
) -> StreamingResponse:
    """Stream a real-model assistant reply for the isolated student Chatbox."""
    if user.role != "student":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Student chat is only available to student accounts",
        )
    if not provider.configured:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=(
                "Qwen model configuration is missing. Set DASHSCOPE_API_KEY and "
                "DASHSCOPE_MODEL, or the legacy QWEN_API_KEY and QWEN_MODEL aliases."
            ),
        )

    conversation = _student_chat_conversation(payload, user)
    store.append_conversation_message(
        conversation,
        "student",
        payload.message,
        attachments=_attachment_metadata(payload.attachments),
    )
    model_messages = _conversation_model_messages(
        conversation,
        limit=settings.chat_model_context_message_limit,
    )

    return StreamingResponse(
        _stream_chat_events(conversation, user, provider, settings, model_messages, payload),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        },
    )


@router.get("/resources", response_model=list[ResourceResponse])
async def list_resources(
    query: str = "",
    category: str | None = None,
) -> list[ResourceResponse]:
    """List published support resources from the in-memory knowledge base."""
    return store.search_resources(query=query, category=category)


@router.get("/resources/{resource_id}", response_model=ResourceResponse)
async def get_resource(resource_id: str) -> ResourceResponse:
    """Get a published support resource by id."""
    resource = next(
        (item for item in store.search_resources() if item.id == resource_id),
        None,
    )
    if resource is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Resource not found")
    return ResourceResponse.model_validate(resource)


@router.get("/conversations", response_model=list[ConversationResponse])
async def list_conversations(
    user: Annotated[User, Depends(current_user)],
) -> list[ConversationResponse]:
    """List conversations owned by the current student."""
    return [
        item
        for item in store.conversations.values()
        if item.student_id == user.id or user.role in {"counselor", "admin"}
    ]


@router.post(
    "/conversations",
    response_model=ConversationResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_conversation(
    payload: ConversationCreate,
    user: Annotated[User, Depends(current_user)],
) -> ConversationResponse:
    """Create a student conversation, optionally seeded with a first message."""
    return store.create_conversation(user.id, payload.title, payload.message)


@router.get("/conversations/{conversation_id}", response_model=ConversationResponse)
async def get_conversation(
    conversation_id: str,
    user: Annotated[User, Depends(current_user)],
) -> ConversationResponse:
    """Get one conversation visible to the current user."""
    return _visible_conversation(conversation_id, user)


@router.post("/conversations/{conversation_id}/messages", response_model=ConversationResponse)
async def add_conversation_message(
    conversation_id: str,
    payload: ConversationMessageCreate,
    user: Annotated[User, Depends(current_user)],
) -> ConversationResponse:
    """Append a student message and generated assistant reply."""
    conversation = _visible_conversation(conversation_id, user)
    if conversation.student_id != user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only the owning student can add messages",
        )
    return store.add_student_message(conversation, payload.content)


def _visible_conversation(conversation_id: str, user: User) -> Conversation:
    conversation = store.conversations.get(conversation_id)
    if conversation is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Conversation not found")
    if conversation.student_id != user.id and user.role not in {"counselor", "admin"}:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Conversation not found")
    return conversation


def _student_chat_conversation(payload: StudentChatRequest, user: User) -> Conversation:
    if payload.conversation_id:
        conversation = _visible_conversation(payload.conversation_id, user)
        if conversation.student_id != user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only the owning student can use this conversation",
            )
        return conversation
    title = payload.message.strip().replace("\n", " ")[:32] or "New chat"
    return store.create_empty_conversation(user.id, title)


def _attachment_metadata(attachments: list[Any]) -> list[MessageAttachment]:
    metadata: list[MessageAttachment] = []
    for index, attachment in enumerate(attachments, start=1):
        content = attachment.content or ""
        size = attachment.size if attachment.size is not None else len(content.encode("utf-8"))
        metadata.append(
            MessageAttachment(
                id=attachment.id or f"attachment-{uuid4().hex}",
                name=attachment.name or f"attachment-{index}",
                mime_type=attachment.mime_type,
                size=max(size, 0),
                encoding=attachment.encoding or "text",
            )
        )
    return metadata


def _conversation_model_messages(
    conversation: Conversation,
    *,
    limit: int,
) -> list[ChatModelMessage]:
    role_map = {"student": "user", "assistant": "assistant"}
    messages = [
        ChatModelMessage(role=role_map[message.role], content=message.content)
        for message in conversation.messages
        if message.role in role_map and message.content.strip()
    ]
    return messages[-limit:]


async def _stream_chat_events(
    conversation: Conversation,
    user: User,
    provider: ChatModelProvider,
    settings: Settings,
    model_messages: list[ChatModelMessage],
    request: StudentChatRequest,
) -> AsyncIterator[str]:
    chunks: list[str] = []
    run = _ChatRunSseBuilder(conversation.id)
    source_count = 0
    tool_count = 0
    started_at = time.perf_counter()
    options = ChatModelRunOptions(
        web_search=request.web_search,
        reasoning_enabled=request.reasoning_enabled,
        profile=request.profile,
        mode=request.mode,
    )
    sandbox = StudentCodeSandboxRunner(
        attachments=request.attachments,
        message=request.message,
        settings=settings,
    )

    yield _sse("conversation", {"conversationId": conversation.id})
    yield run.sse(
        "run_started",
        {
            "conversationId": conversation.id,
            "messageId": run.message_id,
            "status": "running",
        },
    )
    yield run.sse(
        "profile",
        {
            "provider": "qwen",
            "profile": request.profile,
            "mode": request.mode,
            "webSearch": request.web_search,
            "reasoningEnabled": request.reasoning_enabled,
            "attachments": "sandbox" if request.attachments else "none",
        },
    )
    yield run.sse("workflow_plan", {"steps": _base_workflow_steps()})
    yield run.sse(
        "workflow_step_started",
        {
            "step_id": "request-analyze",
            "kind": "plan",
            "title": "理解任务",
            "status": "running",
            "detail": "正在判断是否需要读取文件、运行代码或联网检索。",
        },
    )
    yield run.sse("phase", {"phase": "analyzing", "detail": "Analyzing request."})
    yield run.sse(
        "workflow_step_done",
        {
            "step_id": "request-analyze",
            "kind": "plan",
            "status": "success",
            "summary": "任务理解完成，开始执行可用能力。",
        },
    )
    if sandbox.should_run:
        yield run.sse("phase", {"phase": "working", "detail": "Running controlled sandbox."})
        async for sandbox_event in sandbox.stream():
            if sandbox_event.type == "tool_started" and sandbox_event.counts_as_tool:
                tool_count += 1
            yield run.sse(sandbox_event.type, sandbox_event.payload)
        store.record_audit(
            user.id,
            "student.chat.sandbox.run",
            "conversation",
            conversation.id,
            result="failure" if sandbox.failed else "success",
            event_tags=["chat:sandbox", "sandbox:ephemeral"],
            counter_key="student.chat.sandbox.run.count",
        )
        if sandbox.summary:
            model_messages = [
                *model_messages,
                ChatModelMessage(
                    role="user",
                    content=_sandbox_model_context(sandbox.summary),
                ),
            ]
        yield run.sse(
            "reasoning_summary_delta",
            {"content": "已读取上传内容并运行受控沙箱，正在结合执行结果生成回答。\n"},
        )
    yield run.sse(
        "workflow_step_started",
        {
            "step_id": "answer-generate",
            "kind": "think",
            "title": "生成回答",
            "status": "running",
            "detail": "正在结合真实执行过程组织回复。",
        },
    )
    try:
        stream_messages = model_messages
        continuation_count = 0
        while True:
            truncated = False
            async for event in _provider_stream_events(provider, stream_messages, options):
                event_type, event_payload = _standard_payload(event, source_count + 1)
                if event.type == "delta":
                    content = event.data.get("content")
                    if isinstance(content, str):
                        chunks.append(content)
                if event_type == "source":
                    source_count += 1
                if event.type == "tool_started":
                    tool_count += 1
                if _is_model_output_truncated_notice(event):
                    truncated = True
                if event_type:
                    yield run.sse(event_type, event_payload)
                    legacy = _legacy_sse(event_type, event_payload, conversation.id)
                    if legacy:
                        yield legacy
            partial_reply = "".join(chunks).strip()
            if not truncated or not partial_reply:
                break
            if continuation_count >= MAX_OUTPUT_CONTINUATION_ATTEMPTS:
                yield run.sse(
                    "notice",
                    {
                        "code": "max_output_continuations_reached",
                        "detail": (
                            "Provider kept reporting output token limits after "
                            f"{MAX_OUTPUT_CONTINUATION_ATTEMPTS} continuation pass(es)."
                        ),
                    },
                )
                yield run.sse(
                    "workflow_step_delta",
                    {
                        "step_id": "answer-generate",
                        "kind": "think",
                        "status": "running",
                        "detail": "模型多次达到长度上限，已停止自动续写并保留已生成内容。",
                    },
                )
                break
            continuation_count += 1
            yield run.sse(
                "notice",
                {
                    "code": "continuing_after_token_limit",
                    "detail": (
                        "Provider hit the output token limit, so the backend requested "
                        f"continuation pass {continuation_count}/"
                        f"{MAX_OUTPUT_CONTINUATION_ATTEMPTS}."
                    ),
                },
            )
            yield run.sse(
                "workflow_step_delta",
                {
                    "step_id": "answer-generate",
                    "kind": "think",
                    "status": "running",
                    "detail": "模型输出达到长度上限，正在请求真实续写。",
                },
            )
            stream_messages = _continuation_model_messages(model_messages, partial_reply)
    except ChatModelConfigurationError as exc:
        yield run.sse(
            "workflow_step_done",
            {
                "step_id": "answer-generate",
                "kind": "think",
                "status": "error",
                "summary": "模型配置缺失，回答生成中断。",
            },
        )
        yield run.sse("usage", _usage_payload(chunks, source_count, tool_count, started_at))
        error_payload = {"detail": str(exc), "code": "configuration_error"}
        yield run.sse("error", error_payload)
        yield _sse("error", error_payload)
        return
    except ChatModelError as exc:
        yield run.sse(
            "workflow_step_done",
            {
                "step_id": "answer-generate",
                "kind": "think",
                "status": "error",
                "summary": "模型返回失败，回答生成中断。",
            },
        )
        store.record_audit(
            user.id,
            "student.chat.stream.failure",
            "conversation",
            conversation.id,
            result="failure",
            event_tags=["chat:model:qwen"],
            counter_key="student.chat.stream.failure.count",
        )
        yield run.sse("usage", _usage_payload(chunks, source_count, tool_count, started_at))
        error_payload = {"detail": str(exc), "code": "provider_error"}
        yield run.sse("error", error_payload)
        yield _sse("error", error_payload)
        return
    except asyncio.CancelledError:
        partial_reply = "".join(chunks).strip()
        if partial_reply:
            store.append_conversation_message(conversation, "assistant", partial_reply)
        yield run.sse(
            "workflow_step_done",
            {
                "step_id": "answer-generate",
                "kind": "think",
                "status": "aborted",
                "summary": "用户停止了本轮生成。",
            },
        )
        yield run.sse("usage", _usage_payload(chunks, source_count, tool_count, started_at))
        yield run.sse(
            "aborted",
            {
                "conversationId": conversation.id,
                "detail": "The chat run was cancelled by the client.",
            },
        )
        return

    if source_count == 0:
        yield run.sse(
            "notice",
            {
                "code": "no_external_sources",
                "detail": "No external sources were returned for this run.",
            },
        )
    if tool_count == 0:
        yield run.sse(
            "notice",
            {
                "code": "no_external_tools",
                "detail": "No tool calls were executed for this run.",
            },
        )

    reply = "".join(chunks).strip()
    if reply:
        store.append_conversation_message(conversation, "assistant", reply)
    store.record_audit(
        user.id,
        "student.chat.stream.success",
        "conversation",
        conversation.id,
        event_tags=["chat:model:qwen"],
        counter_key="student.chat.stream.success.count",
    )
    yield run.sse(
        "workflow_step_done",
        {
            "step_id": "answer-generate",
            "kind": "think",
            "status": "success",
            "summary": "回答生成完成。",
        },
    )
    yield run.sse("usage", _usage_payload(chunks, source_count, tool_count, started_at))
    done_payload = {"conversationId": conversation.id}
    yield run.sse("done", done_payload)
    yield _sse("done", done_payload)


async def _provider_stream_events(
    provider: ChatModelProvider,
    model_messages: list[ChatModelMessage],
    options: ChatModelRunOptions,
) -> AsyncIterator[ChatModelStreamEvent]:
    stream_events = getattr(provider, "stream_events", None)
    if callable(stream_events):
        async for event in stream_events(model_messages, options):
            yield event
        return
    async for chunk in provider.stream_reply(model_messages, options):
        yield ChatModelStreamEvent.delta(chunk)


def _is_model_output_truncated_notice(event: ChatModelStreamEvent) -> bool:
    return event.type == "notice" and event.data.get("code") == "model_output_truncated"


def _continuation_model_messages(
    model_messages: list[ChatModelMessage],
    partial_reply: str,
) -> list[ChatModelMessage]:
    return [
        *model_messages,
        ChatModelMessage(
            role="assistant",
            content=partial_reply.strip(),
            partial=True,
        ),
    ]


def _sse(event: str, data: dict[str, Any]) -> str:
    return f"event: {event}\ndata: {json.dumps(data, ensure_ascii=False)}\n\n"


class _ChatRunSseBuilder:
    schema_version = "chat.run.v1"

    def __init__(self, conversation_id: str) -> None:
        self.run_id = f"run_{uuid4().hex}"
        self.message_id = f"msg_{uuid4().hex}"
        self.conversation_id = conversation_id
        self._seq = 0

    def sse(self, event_type: str, payload: dict[str, Any]) -> str:
        self._seq += 1
        data = {
            "schema_version": self.schema_version,
            "run_id": self.run_id,
            "message_id": self.message_id,
            "conversation_id": self.conversation_id,
            "seq": self._seq,
            "type": event_type,
            "ts": datetime.now(UTC).isoformat().replace("+00:00", "Z"),
            "payload": payload,
        }
        for key, value in payload.items():
            if key not in data:
                data[key] = value
        return _sse(event_type, data)


def _standard_payload(
    event: ChatModelStreamEvent,
    next_source_index: int,
) -> tuple[str | None, dict[str, Any]]:
    data = event.data
    if event.type == "delta":
        return "answer_delta", {"content": _string_value(data.get("content"))}
    if event.type == "reasoning":
        return "reasoning_summary_delta", {"content": _string_value(data.get("content"))}
    if event.type == "phase":
        return "phase", {"phase": _string_value(data.get("phase"))}
    if event.type == "source":
        source_payload = _source_payload(data, next_source_index)
        return ("source", source_payload) if source_payload else (None, {})
    if event.type == "citation":
        return "citation", _citation_payload(data)
    if event.type in {"tool_started", "tool_delta", "tool_done"}:
        return event.type, _tool_payload(data)
    if event.type == "notice":
        return "notice", dict(data)
    return None, {}


def _sandbox_model_context(summary: str) -> str:
    return (
        "以下是后端受控临时沙箱的真实读取/执行结果。请基于这些结果回答学生，"
        "说明你读取了哪些文件；如果运行了命令，再说明运行了什么命令、错误在哪里、下一步如何修改。"
        "不要声称访问了真实学校系统或长期保存了文件。\n\n"
        f"{summary}"
    )


def _base_workflow_steps() -> list[dict[str, Any]]:
    return [
        {
            "step_id": "request-analyze",
            "kind": "plan",
            "title": "理解任务",
            "status": "queued",
        },
    ]


def _source_payload(source: dict[str, Any], index: int) -> dict[str, Any] | None:
    payload = dict(source)
    url = _string_value(payload.get("url"))
    if not url:
        return None
    parsed_url = urlparse(url)
    hostname = (parsed_url.hostname or "").strip().lower()
    if not _is_public_source_url(parsed_url.scheme, hostname):
        return None
    payload["url"] = url
    payload.setdefault("hostname", hostname)
    source_id = payload.get("source_id") or payload.get("sourceId")
    if not isinstance(source_id, str) or not source_id:
        source_id = f"source-{index}"
    payload["source_id"] = source_id
    payload["sourceId"] = source_id
    payload.setdefault("sourceQuality", "public_web")
    payload.setdefault("trustLabel", "Public web source")
    payload.setdefault(
        "sourcePolicy",
        "Shown only when the provider returned a public http(s) source URL.",
    )
    return payload


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


def _citation_payload(citation: dict[str, Any]) -> dict[str, Any]:
    payload = dict(citation)
    citation_id = payload.get("citation_id") or payload.get("citationId")
    if isinstance(citation_id, str) and citation_id:
        payload["citation_id"] = citation_id
        payload["citationId"] = citation_id
    return payload


def _tool_payload(data: dict[str, Any]) -> dict[str, Any]:
    payload = dict(data)
    tool_call_id = payload.get("tool_call_id") or payload.get("toolCallId")
    tool_name = payload.get("tool_name") or payload.get("toolName")
    if tool_call_id is not None:
        payload["tool_call_id"] = tool_call_id
        payload["toolCallId"] = tool_call_id
    if tool_name is not None:
        payload["tool_name"] = tool_name
        payload["toolName"] = tool_name
    return payload


def _usage_payload(
    chunks: list[str],
    source_count: int,
    tool_count: int,
    started_at: float,
) -> dict[str, Any]:
    return {
        "output_chars": len("".join(chunks)),
        "source_count": source_count,
        "tool_count": tool_count,
        "elapsed_ms": int((time.perf_counter() - started_at) * 1000),
    }


def _legacy_sse(
    event_type: str,
    payload: dict[str, Any],
    conversation_id: str,
) -> str | None:
    if event_type == "answer_delta":
        return _sse("delta", {"content": payload.get("content", "")})
    if event_type == "reasoning_summary_delta":
        return _sse("reasoning", {"content": payload.get("content", "")})
    if event_type == "source":
        return _sse("source", payload)
    if event_type == "phase":
        return _sse("phase", payload)
    if event_type == "notice":
        return _sse("notice", payload)
    if event_type == "done":
        return _sse("done", {"conversationId": conversation_id})
    if event_type == "error":
        return _sse("error", payload)
    return None


def _string_value(value: Any) -> str:
    return value if isinstance(value, str) else ""
