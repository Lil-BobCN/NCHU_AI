"""Acceptance tests for the Phase 1 business API surface."""
from __future__ import annotations

import json

import pytest
from httpx import AsyncClient

from app.api.v1.deps import chat_model_provider
from app.config import Settings, get_settings
from app.services.business import store
from app.services.chat_model import (
    ChatModelError,
    ChatModelMessage,
    ChatModelRunOptions,
    ChatModelStreamEvent,
    DashScopeChatModelProvider,
)


async def _login(async_client: AsyncClient, username: str, password: str = "password") -> dict:
    response = await async_client.post(
        "/api/v1/auth/login",
        json={"username": username, "password": password},
    )
    assert response.status_code == 200
    return response.json()


def _bearer(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def _sse_events(text: str) -> list[tuple[str, dict]]:
    events: list[tuple[str, dict]] = []
    for block in text.replace("\r\n", "\n").strip().split("\n\n"):
        event = "message"
        data_lines: list[str] = []
        for line in block.split("\n"):
            if line.startswith("event:"):
                event = line.removeprefix("event:").strip()
            if line.startswith("data:"):
                data_lines.append(line.removeprefix("data:").strip())
        if data_lines:
            events.append((event, json.loads("\n".join(data_lines))))
    return events


def _standard_sse_events(text: str) -> list[tuple[str, dict]]:
    return [
        (event, data)
        for event, data in _sse_events(text)
        if data.get("schema_version") == "chat.run.v1"
    ]


@pytest.mark.asyncio
async def test_local_login_issues_bearer_token(async_client: AsyncClient) -> None:
    payload = await _login(async_client, "student@example.edu")

    assert payload["token_type"] == "bearer"
    assert payload["provider"] == "local"
    assert payload["access_token"]
    assert payload["user"] == {
        "id": "student-1",
        "displayName": "Demo Student",
        "role": "student",
        "demoAccount": True,
        "sessionState": "authenticated",
    }


@pytest.mark.asyncio
async def test_sso_callback_is_explicitly_deferred(async_client: AsyncClient) -> None:
    response = await async_client.post(
        "/api/v1/auth/sso/callback",
        json={
            "provider": "campus-sso",
            "code": "sso-code-123",
            "email": "fresh.student@example.edu",
        },
    )

    assert response.status_code == 501
    assert "SSO is deferred" in response.json()["detail"]


@pytest.mark.asyncio
async def test_auth_me_returns_authenticated_profile(async_client: AsyncClient) -> None:
    login = await _login(async_client, "student@example.edu")

    response = await async_client.get(
        "/api/v1/auth/me",
        headers=_bearer(login["access_token"]),
    )

    assert response.status_code == 200
    assert response.json() == {
        "id": "student-1",
        "displayName": "Demo Student",
        "role": "student",
        "demoAccount": True,
        "sessionState": "authenticated",
    }


@pytest.mark.asyncio
async def test_failed_login_records_structured_audit_event(async_client: AsyncClient) -> None:
    failed = await async_client.post(
        "/api/v1/auth/login",
        json={"username": "unknown@example.edu", "password": "wrong-password"},
    )
    assert failed.status_code == 401

    admin = await _login(async_client, "admin@example.edu")
    audit = await async_client.get(
        "/api/v1/admin/audit",
        headers=_bearer(admin["access_token"]),
    )

    assert audit.status_code == 200
    failure = next(event for event in audit.json() if event["action"] == "auth.login.failure")
    assert failure["result"] == "failure"
    assert failure["targetId"] == "local-demo-login"
    assert failure["counterKey"] == "auth.login.failure.count"
    assert "role:anonymous" in failure["eventTags"]


@pytest.mark.asyncio
async def test_student_qna_returns_citations_and_crisis_fallback(
    async_client: AsyncClient,
) -> None:
    login = await _login(async_client, "student@example.edu")

    cited = await async_client.post(
        "/api/v1/student/questions",
        headers=_bearer(login["access_token"]),
        json={"question": "How should I handle academic stress?"},
    )
    assert cited.status_code == 200
    cited_payload = cited.json()
    assert cited_payload["answer"].startswith("I can help you think through this.")
    assert cited_payload["resources"]
    cited_sources = {
        resource["source_knowledge_id"] for resource in cited_payload["resources"]
    }
    assert "knowledge-1" in cited_sources

    fallback = await async_client.post(
        "/api/v1/student/questions",
        headers=_bearer(login["access_token"]),
        json={"question": "I might harm myself tonight."},
    )
    assert fallback.status_code == 200
    fallback_payload = fallback.json()
    assert "immediate danger" in fallback_payload["answer"]
    assert "emergency services" in fallback_payload["answer"]


@pytest.mark.asyncio
async def test_resource_direct_link_resolves_source_knowledge(
    async_client: AsyncClient,
) -> None:
    login = await _login(async_client, "student@example.edu")

    listed = await async_client.get(
        "/api/v1/student/resources",
        headers=_bearer(login["access_token"]),
        params={"query": "stress"},
    )
    assert listed.status_code == 200
    resource = listed.json()[0]

    direct = await async_client.get(
        f"/api/v1/student/resources/{resource['id']}",
        headers=_bearer(login["access_token"]),
    )
    assert direct.status_code == 200
    assert direct.json() == resource


@pytest.mark.asyncio
async def test_conversation_history_preserves_message_order(
    async_client: AsyncClient,
) -> None:
    login = await _login(async_client, "student@example.edu")

    created = await async_client.post(
        "/api/v1/student/conversations",
        headers=_bearer(login["access_token"]),
        json={"title": "Check-in", "message": "I feel overwhelmed by coursework."},
    )
    assert created.status_code == 201
    conversation = created.json()
    assert len(conversation["messages"]) == 2
    assert [message["role"] for message in conversation["messages"]] == [
        "student",
        "assistant",
    ]

    appended = await async_client.post(
        f"/api/v1/student/conversations/{conversation['id']}/messages",
        headers=_bearer(login["access_token"]),
        json={"content": "I also missed a deadline."},
    )
    assert appended.status_code == 200
    updated = appended.json()
    assert len(updated["messages"]) == 4
    assert [message["role"] for message in updated["messages"]] == [
        "student",
        "assistant",
        "student",
        "assistant",
    ]

    history = await async_client.get(
        f"/api/v1/student/conversations/{conversation['id']}",
        headers=_bearer(login["access_token"]),
    )
    assert history.status_code == 200
    assert history.json()["messages"] == updated["messages"]

    listing = await async_client.get(
        "/api/v1/student/conversations",
        headers=_bearer(login["access_token"]),
    )
    assert listing.status_code == 200
    assert [item["id"] for item in listing.json()] == [conversation["id"]]


class _FakeChatProvider:
    def __init__(self, chunks: list[str], configured: bool = True) -> None:
        self.chunks = chunks
        self._configured = configured
        self.calls: list[list[ChatModelMessage]] = []
        self.options: list[ChatModelRunOptions | None] = []

    @property
    def configured(self) -> bool:
        return self._configured

    async def stream_reply(
        self,
        messages: list[ChatModelMessage],
        options: ChatModelRunOptions | None = None,
    ):
        self.calls.append(messages)
        self.options.append(options)
        for chunk in self.chunks:
            yield chunk


class _FakeEventProvider:
    def __init__(self, events: list[ChatModelStreamEvent], configured: bool = True) -> None:
        self.events = events
        self._configured = configured
        self.calls: list[list[ChatModelMessage]] = []
        self.options: list[ChatModelRunOptions | None] = []

    @property
    def configured(self) -> bool:
        return self._configured

    async def stream_events(
        self,
        messages: list[ChatModelMessage],
        options: ChatModelRunOptions | None = None,
    ):
        self.calls.append(messages)
        self.options.append(options)
        for event in self.events:
            yield event

    async def stream_reply(
        self,
        messages: list[ChatModelMessage],
        options: ChatModelRunOptions | None = None,
    ):
        self.calls.append(messages)
        self.options.append(options)
        for event in self.events:
            if event.type == "delta":
                yield event.data["content"]


class _SequencedEventProvider(_FakeEventProvider):
    def __init__(self, event_batches: list[list[ChatModelStreamEvent]]) -> None:
        super().__init__([])
        self.event_batches = event_batches

    async def stream_events(
        self,
        messages: list[ChatModelMessage],
        options: ChatModelRunOptions | None = None,
    ):
        self.calls.append(messages)
        self.options.append(options)
        index = min(len(self.calls) - 1, len(self.event_batches) - 1)
        for event in self.event_batches[index]:
            yield event


class _FailingEventProvider(_FakeEventProvider):
    async def stream_events(
        self,
        messages: list[ChatModelMessage],
        options: ChatModelRunOptions | None = None,
    ):
        self.calls.append(messages)
        self.options.append(options)
        yield ChatModelStreamEvent.delta("partial")
        raise ChatModelError("provider failed")


@pytest.mark.asyncio
async def test_student_chat_stream_fails_clearly_without_model_config(
    app,
    async_client: AsyncClient,
) -> None:
    app.dependency_overrides[chat_model_provider] = lambda: _FakeChatProvider([], configured=False)
    login = await _login(async_client, "student@example.edu")

    response = await async_client.post(
        "/api/v1/student/chat/stream",
        headers=_bearer(login["access_token"]),
        json={"message": "我最近学习压力很大。"},
    )

    assert response.status_code == 503
    assert "Qwen model configuration is missing" in response.json()["detail"]
    app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_student_chat_stream_writes_runtime_history(
    app,
    async_client: AsyncClient,
) -> None:
    provider = _FakeChatProvider(["可以先整理", "本周最紧急的任务。"])
    app.dependency_overrides[chat_model_provider] = lambda: provider
    login = await _login(async_client, "student@example.edu")

    response = await async_client.post(
        "/api/v1/student/chat/stream",
        headers=_bearer(login["access_token"]),
        json={"message": "我最近学习压力很大。"},
    )

    assert response.status_code == 200
    assert "event: conversation" in response.text
    assert "event: delta" in response.text
    assert "event: done" in response.text

    conversation = next(iter(store.conversations.values()))
    assert [message.role for message in conversation.messages] == ["student", "assistant"]
    assert conversation.messages[0].content == "我最近学习压力很大。"
    assert conversation.messages[1].content == "可以先整理本周最紧急的任务。"
    assert provider.calls[0][-1] == ChatModelMessage(
        role="user",
        content="我最近学习压力很大。",
    )
    app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_student_chat_stream_uses_readable_chinese_history_title(
    app,
    async_client: AsyncClient,
) -> None:
    provider = _FakeChatProvider(["可以先把复习任务拆成三段。"])
    app.dependency_overrides[chat_model_provider] = lambda: provider
    login = await _login(async_client, "student@example.edu")
    message = "我最近学习压力很大，\n不知道怎么安排复习和睡眠。还有一段很长的补充说明用于测试截断。"

    response = await async_client.post(
        "/api/v1/student/chat/stream",
        headers=_bearer(login["access_token"]),
        json={"message": message},
    )

    assert response.status_code == 200
    listing = await async_client.get(
        "/api/v1/student/conversations",
        headers=_bearer(login["access_token"]),
    )

    assert listing.status_code == 200
    title = listing.json()[0]["title"]
    assert "我最近学习压力很大" in title
    assert "\n" not in title
    assert "????" not in title
    assert len(title) <= 32
    app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_student_chat_stream_forwards_structured_model_events(
    app,
    async_client: AsyncClient,
) -> None:
    provider = _FakeEventProvider(
        [
            ChatModelStreamEvent.phase("searching"),
            ChatModelStreamEvent.source(
                {
                    "title": "Official notice",
                    "url": "https://example.edu/notice",
                    "snippet": "Campus notice summary",
                }
            ),
            ChatModelStreamEvent.reasoning("正在整理检索结果。"),
            ChatModelStreamEvent.delta("可以先查看官方通知。"),
        ]
    )
    app.dependency_overrides[chat_model_provider] = lambda: provider
    login = await _login(async_client, "student@example.edu")

    response = await async_client.post(
        "/api/v1/student/chat/stream",
        headers=_bearer(login["access_token"]),
        json={"message": "请联网搜索今天最新的学校通知。"},
    )

    assert response.status_code == 200
    assert "event: phase" in response.text
    assert "event: source" in response.text
    assert "https://example.edu/notice" in response.text
    assert "event: reasoning" in response.text
    assert "event: delta" in response.text

    conversation = next(iter(store.conversations.values()))
    assert conversation.messages[1].content == "可以先查看官方通知。"
    app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_student_chat_stream_wraps_events_in_standard_run_envelope(
    app,
    async_client: AsyncClient,
) -> None:
    provider = _FakeEventProvider(
        [
            ChatModelStreamEvent.phase("searching"),
            ChatModelStreamEvent.tool_started(
                "web_search",
                tool_call_id="search-1",
                title="Provider web search",
            ),
            ChatModelStreamEvent.tool_delta(
                "web_search",
                tool_call_id="search-1",
                detail="Search request accepted.",
            ),
            ChatModelStreamEvent.source(
                {
                    "title": "Official notice",
                    "type": "provider-source",
                    "url": "https://example.edu/notice",
                }
            ),
            ChatModelStreamEvent.tool_done(
                "web_search",
                tool_call_id="search-1",
                status="success",
                detail="Provider returned 1 source.",
                result_count=1,
            ),
            ChatModelStreamEvent.delta("Use the official notice."),
        ]
    )
    app.dependency_overrides[chat_model_provider] = lambda: provider
    login = await _login(async_client, "student@example.edu")

    response = await async_client.post(
        "/api/v1/student/chat/stream",
        headers=_bearer(login["access_token"]),
        json={"message": "Please search the latest school notice."},
    )

    assert response.status_code == 200
    assert "event: conversation" in response.text
    assert "event: delta" in response.text
    events = _standard_sse_events(response.text)
    payloads = [data for _, data in events]
    run_id = payloads[0]["run_id"]
    message_id = payloads[0]["message_id"]

    assert payloads[0]["schema_version"] == "chat.run.v1"
    assert payloads[0]["type"] == "run_started"
    assert payloads[0]["payload"]["conversationId"] == payloads[0]["conversationId"]
    assert all(data["run_id"] == run_id for data in payloads)
    assert all(data["message_id"] == message_id for data in payloads)
    assert [data["seq"] for data in payloads] == list(range(1, len(payloads) + 1))

    delta = next(data for event, data in events if event == "answer_delta")
    assert delta["type"] == "answer_delta"
    assert delta["payload"]["content"] == "Use the official notice."
    assert delta["content"] == "Use the official notice."

    source = next(data for event, data in events if event == "source")
    assert source["type"] == "source"
    assert source["payload"]["type"] == "provider-source"
    assert source["payload"]["url"] == "https://example.edu/notice"
    assert source["payload"]["hostname"] == "example.edu"
    assert source["payload"]["sourceQuality"] == "public_web"
    assert source["payload"]["trustLabel"] == "Public web source"
    assert source["url"] == "https://example.edu/notice"

    terminal_types = [
        data["type"]
        for _, data in events
        if data["type"] in {"done", "error", "aborted"}
    ]
    assert terminal_types == ["done"]
    usage_index = next(index for index, data in enumerate(payloads) if data["type"] == "usage")
    done_index = next(index for index, data in enumerate(payloads) if data["type"] == "done")
    assert usage_index < done_index
    app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_student_chat_stream_exposes_credible_source_citation_and_usage_counts(
    app,
    async_client: AsyncClient,
) -> None:
    provider = _FakeEventProvider(
        [
            ChatModelStreamEvent.tool_started(
                "web_search",
                tool_call_id="search-credible",
                title="Provider web search",
            ),
            ChatModelStreamEvent.source(
                {
                    "title": "Public student affairs notice",
                    "url": "https://example.edu/student-affairs",
                    "snippet": "Published student support notice.",
                }
            ),
            ChatModelStreamEvent.source(
                {
                    "title": "Duplicate public student affairs notice",
                    "url": "https://example.edu/student-affairs#section",
                    "snippet": "Duplicate provider result.",
                }
            ),
            ChatModelStreamEvent.citation(
                {
                    "citationId": "cite-1",
                    "marker": "[ref_1]",
                    "title": "Public student affairs notice",
                    "url": "https://example.edu/student-affairs",
                    "sourceIndex": 1,
                }
            ),
            ChatModelStreamEvent.tool_done(
                "web_search",
                tool_call_id="search-credible",
                status="success",
                detail="Provider returned 1 public source.",
                result_count=1,
            ),
            ChatModelStreamEvent.delta("Use the public notice and ask a counselor if unsure."),
        ]
    )
    app.dependency_overrides[chat_model_provider] = lambda: provider
    login = await _login(async_client, "student@example.edu")

    response = await async_client.post(
        "/api/v1/student/chat/stream",
        headers=_bearer(login["access_token"]),
        json={"message": "Please search public support guidance."},
    )

    assert response.status_code == 200
    events = _standard_sse_events(response.text)
    sources = [data for event, data in events if event == "source"]
    source = sources[0]
    citation = next(data for event, data in events if event == "citation")
    usage = next(data for event, data in events if event == "usage")
    notices = [data["payload"]["code"] for event, data in events if event == "notice"]

    assert len(sources) == 1
    assert source["payload"]["url"] == "https://example.edu/student-affairs"
    assert source["payload"]["sourceId"] == "source-1"
    assert source["payload"]["dedupeKey"] == "https://example.edu/student-affairs"
    assert source["payload"]["snippet"] == "Published student support notice."
    assert citation["payload"]["citationId"] == "cite-1"
    assert citation["payload"]["sourceIndex"] == 1
    assert citation["payload"]["sourceId"] == "source-1"
    assert citation["payload"]["url"] == source["payload"]["url"]
    assert usage["payload"]["source_count"] == 1
    assert usage["payload"]["tool_count"] == 1
    assert "no_external_sources" not in notices
    assert "no_external_tools" not in notices
    app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_student_chat_stream_emits_no_source_no_tool_notices(
    app,
    async_client: AsyncClient,
) -> None:
    provider = _FakeChatProvider(["Plain answer."])
    app.dependency_overrides[chat_model_provider] = lambda: provider
    login = await _login(async_client, "student@example.edu")

    response = await async_client.post(
        "/api/v1/student/chat/stream",
        headers=_bearer(login["access_token"]),
        json={"message": "I feel stressed today."},
    )

    assert response.status_code == 200
    notices = [
        data["payload"]["code"]
        for event, data in _standard_sse_events(response.text)
        if event == "notice"
    ]
    assert notices == ["no_external_sources", "no_external_tools"]
    assert "event: done" in response.text
    app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_student_chat_stream_passes_request_run_options(
    app,
    async_client: AsyncClient,
) -> None:
    provider = _FakeChatProvider(["Plain answer."])
    app.dependency_overrides[chat_model_provider] = lambda: provider
    login = await _login(async_client, "student@example.edu")

    response = await async_client.post(
        "/api/v1/student/chat/stream",
        headers=_bearer(login["access_token"]),
        json={
            "message": "Please search the latest school notice.",
            "webSearch": False,
            "reasoning": False,
            "profile": "student",
            "mode": "focus",
            "attachments": [{"id": "a1", "name": "note.pdf"}],
        },
    )

    assert response.status_code == 200
    assert provider.options[0] == ChatModelRunOptions(
        web_search=False,
        reasoning_enabled=False,
        profile="student",
        mode="focus",
    )
    notices = [
        data["payload"]["code"]
        for event, data in _standard_sse_events(response.text)
        if event == "notice"
    ]
    events = _standard_sse_events(response.text)
    assert any(event == "workflow_plan" for event, _ in events)
    assert any(
        event == "workflow_step_done"
        and data["payload"]["step_id"] == "sandbox-read"
        and data["payload"]["status"] == "skipped"
        for event, data in events
    )
    assert notices == ["no_external_sources", "no_external_tools"]
    app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_student_chat_stream_runs_inline_attachment_in_controlled_sandbox(
    app,
    async_client: AsyncClient,
) -> None:
    provider = _FakeChatProvider(["根据运行结果，程序输出了 hi。"])
    app.dependency_overrides[chat_model_provider] = lambda: provider
    login = await _login(async_client, "student@example.edu")

    response = await async_client.post(
        "/api/v1/student/chat/stream",
        headers=_bearer(login["access_token"]),
        json={
            "message": "请运行这个作业代码，解释结果。",
            "attachments": [
                {
                    "id": "a1",
                    "name": "homework.py",
                    "mimeType": "text/x-python",
                    "size": 11,
                    "content": "print('hi')",
                    "encoding": "text",
                }
            ],
        },
    )

    assert response.status_code == 200
    events = _standard_sse_events(response.text)
    assert any(event == "workflow_plan" for event, _ in events)
    assert any(
        event == "workflow_step_started" and data["payload"]["step_id"] == "sandbox-read"
        for event, data in events
    )
    assert any(
        event == "workflow_artifact"
        and data["payload"]["step_id"] == "sandbox-read"
        and data["payload"]["title"] == "homework.py"
        and "print('hi')" in data["payload"]["content"]
        for event, data in events
    )
    assert any(
        event == "tool_started" and data["payload"]["toolName"] == "read_uploaded_files"
        for event, data in events
    )
    assert any(
        event == "tool_started" and data["payload"]["toolName"] == "run_terminal"
        for event, data in events
    )
    assert any(
        event == "workflow_artifact"
        and data["payload"]["step_id"] == "sandbox-run"
        and "hi" in data["payload"]["content"]
        for event, data in events
    )
    assert any(
        event == "tool_done"
        and data["payload"]["toolName"] == "run_terminal"
        and data["payload"]["status"] == "success"
        for event, data in events
    )
    assert any(event.action == "student.chat.sandbox.run" for event in store.audit_events)
    assert provider.calls[0][-1].role == "user"
    assert "后端受控临时沙箱的真实读取/执行结果" in provider.calls[0][-1].content
    assert "python homework.py" in provider.calls[0][-1].content
    assert "hi" in provider.calls[0][-1].content
    app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_student_chat_stream_passes_read_markdown_attachment_to_model_context(
    app,
    async_client: AsyncClient,
) -> None:
    provider = _FakeChatProvider(["已根据资料整理。"])
    app.dependency_overrides[chat_model_provider] = lambda: provider
    login = await _login(async_client, "student@example.edu")

    response = await async_client.post(
        "/api/v1/student/chat/stream",
        headers=_bearer(login["access_token"]),
        json={
            "message": "请根据资料整理当前方案。",
            "attachments": [
                {
                    "id": "a1",
                    "name": "architecture.md",
                    "mimeType": "text/markdown",
                    "size": 48,
                    "content": "# AI 辅导员技术架构方案\n\n## 一、整体技术架构图\n",
                    "encoding": "text",
                }
            ],
        },
    )

    assert response.status_code == 200
    events = _standard_sse_events(response.text)
    assert any(
        event == "workflow_step_done"
        and data["payload"]["step_id"] == "sandbox-run"
        and data["payload"]["status"] == "skipped"
        for event, data in events
    )
    model_context = provider.calls[0][-1].content
    assert "已读取文件：architecture.md" in model_context
    assert "AI 辅导员技术架构方案" in model_context
    assert "沙箱没有产生可汇总的命令输出" not in model_context
    app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_student_chat_stream_persists_attachment_metadata_without_content(
    app,
    async_client: AsyncClient,
) -> None:
    provider = _FakeChatProvider(["已根据资料整理。"])
    app.dependency_overrides[chat_model_provider] = lambda: provider
    login = await _login(async_client, "student@example.edu")

    response = await async_client.post(
        "/api/v1/student/chat/stream",
        headers=_bearer(login["access_token"]),
        json={
            "message": "请根据资料整理当前方案。",
            "attachments": [
                {
                    "id": "a1",
                    "name": "architecture.md",
                    "mimeType": "text/markdown",
                    "size": 48,
                    "content": "# AI 辅导员技术架构方案\n",
                    "encoding": "text",
                }
            ],
        },
    )

    assert response.status_code == 200
    conversation_id = next(iter(store.conversations))
    history = await async_client.get(
        f"/api/v1/student/conversations/{conversation_id}",
        headers=_bearer(login["access_token"]),
    )

    assert history.status_code == 200
    student_message = history.json()["messages"][0]
    assert student_message["attachments"] == [
        {
            "id": "a1",
            "name": "architecture.md",
            "mimeType": "text/markdown",
            "size": 48,
            "encoding": "text",
        }
    ]
    assert "content" not in student_message["attachments"][0]
    app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_student_chat_stream_continues_once_after_provider_length_stop(
    app,
    async_client: AsyncClient,
) -> None:
    provider = _SequencedEventProvider(
        [
            [
                ChatModelStreamEvent.delta("第一部分，"),
                ChatModelStreamEvent.notice(
                    "model_output_truncated",
                    "Provider stopped because the configured output token budget was reached.",
                ),
            ],
            [ChatModelStreamEvent.delta("第二部分完成。")],
        ]
    )
    app.dependency_overrides[chat_model_provider] = lambda: provider
    login = await _login(async_client, "student@example.edu")

    response = await async_client.post(
        "/api/v1/student/chat/stream",
        headers=_bearer(login["access_token"]),
        json={"message": "请根据上传资料写一份完整总结。"},
    )

    assert response.status_code == 200
    events = _standard_sse_events(response.text)
    notices = [
        data["payload"]["code"]
        for event, data in events
        if event == "notice"
    ]
    assert "model_output_truncated" in notices
    assert "continuing_after_token_limit" in notices
    assert len(provider.calls) == 2
    assert provider.calls[1][-1] == ChatModelMessage(
        role="assistant",
        content="第一部分，",
        partial=True,
    )

    conversation = next(iter(store.conversations.values()))
    assert conversation.messages[1].content == "第一部分，第二部分完成。"
    app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_student_chat_stream_continues_multiple_times_until_provider_stops(
    app,
    async_client: AsyncClient,
) -> None:
    provider = _SequencedEventProvider(
        [
            [
                ChatModelStreamEvent.delta("第一段，"),
                ChatModelStreamEvent.notice(
                    "model_output_truncated",
                    "Provider stopped because the configured output token budget was reached.",
                ),
            ],
            [
                ChatModelStreamEvent.delta("第二段，"),
                ChatModelStreamEvent.notice(
                    "model_output_truncated",
                    "Provider stopped because the configured output token budget was reached.",
                ),
            ],
            [ChatModelStreamEvent.delta("第三段完成。")],
        ]
    )
    app.dependency_overrides[chat_model_provider] = lambda: provider
    login = await _login(async_client, "student@example.edu")

    response = await async_client.post(
        "/api/v1/student/chat/stream",
        headers=_bearer(login["access_token"]),
        json={"message": "请根据上传资料写一份较长的完整总结。"},
    )

    assert response.status_code == 200
    events = _standard_sse_events(response.text)
    continuation_notices = [
        data["payload"]
        for event, data in events
        if event == "notice" and data["payload"].get("code") == "continuing_after_token_limit"
    ]
    assert len(continuation_notices) == 2
    assert "1/3" in continuation_notices[0]["detail"]
    assert "2/3" in continuation_notices[1]["detail"]
    assert len(provider.calls) == 3
    assert provider.calls[1][-1] == ChatModelMessage(
        role="assistant",
        content="第一段，",
        partial=True,
    )
    assert provider.calls[2][-1] == ChatModelMessage(
        role="assistant",
        content="第一段，第二段，",
        partial=True,
    )

    conversation = next(iter(store.conversations.values()))
    assert conversation.messages[1].content == "第一段，第二段，第三段完成。"
    app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_student_chat_stream_stops_after_max_continuations(
    app,
    async_client: AsyncClient,
) -> None:
    truncated_batch = [
        ChatModelStreamEvent.delta("一段，"),
        ChatModelStreamEvent.notice(
            "model_output_truncated",
            "Provider stopped because the configured output token budget was reached.",
        ),
    ]
    provider = _SequencedEventProvider(
        [
            truncated_batch,
            truncated_batch,
            truncated_batch,
            truncated_batch,
            truncated_batch,
        ]
    )
    app.dependency_overrides[chat_model_provider] = lambda: provider
    login = await _login(async_client, "student@example.edu")

    response = await async_client.post(
        "/api/v1/student/chat/stream",
        headers=_bearer(login["access_token"]),
        json={"message": "请持续输出，直到 provider 多次报告长度上限。"},
    )

    assert response.status_code == 200
    events = _standard_sse_events(response.text)
    notices = [
        data["payload"]["code"]
        for event, data in events
        if event == "notice"
    ]
    assert notices.count("continuing_after_token_limit") == 3
    assert "max_output_continuations_reached" in notices
    assert len(provider.calls) == 4

    conversation = next(iter(store.conversations.values()))
    assert conversation.messages[1].content == "一段，一段，一段，一段，"
    app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_student_chat_stream_skips_oversized_inline_attachment(
    app,
    async_client: AsyncClient,
) -> None:
    provider = _FakeChatProvider(["附件过大，本轮没有运行代码。"])
    app.dependency_overrides[chat_model_provider] = lambda: provider
    app.dependency_overrides[get_settings] = lambda: Settings(
        chat_sandbox_max_attachment_bytes=4,
    )
    login = await _login(async_client, "student@example.edu")

    response = await async_client.post(
        "/api/v1/student/chat/stream",
        headers=_bearer(login["access_token"]),
        json={
            "message": "请运行这个作业代码。",
            "attachments": [
                {
                    "name": "too-large.py",
                    "content": "print('too large')",
                    "encoding": "text",
                }
            ],
        },
    )

    assert response.status_code == 200
    events = _standard_sse_events(response.text)
    assert any(
        event == "workflow_step_done"
        and data["payload"]["step_id"] == "sandbox-read"
        and data["payload"]["status"] == "skipped"
        for event, data in events
    )
    assert not any(
        event == "workflow_artifact" and "too large" in data["payload"].get("content", "")
        for event, data in events
    )
    app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_student_chat_stream_error_flow_has_single_standard_terminal(
    app,
    async_client: AsyncClient,
) -> None:
    provider = _FailingEventProvider([])
    app.dependency_overrides[chat_model_provider] = lambda: provider
    login = await _login(async_client, "student@example.edu")

    response = await async_client.post(
        "/api/v1/student/chat/stream",
        headers=_bearer(login["access_token"]),
        json={"message": "Please answer."},
    )

    assert response.status_code == 200
    events = _standard_sse_events(response.text)
    terminal_types = [
        data["type"]
        for _, data in events
        if data["type"] in {"done", "error", "aborted"}
    ]
    assert terminal_types == ["error"]
    assert "event: done" not in response.text
    app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_student_chat_stream_reuses_existing_conversation_context(
    app,
    async_client: AsyncClient,
) -> None:
    provider = _FakeChatProvider(["先把延期风险告诉任课老师。"])
    app.dependency_overrides[chat_model_provider] = lambda: provider
    login = await _login(async_client, "student@example.edu")

    first = await async_client.post(
        "/api/v1/student/chat/stream",
        headers=_bearer(login["access_token"]),
        json={"message": "我错过了一次作业截止时间。"},
    )
    assert first.status_code == 200
    conversation_id = next(iter(store.conversations))

    second = await async_client.post(
        "/api/v1/student/chat/stream",
        headers=_bearer(login["access_token"]),
        json={"conversationId": conversation_id, "message": "我应该怎么补救？"},
    )

    assert second.status_code == 200
    conversation = store.conversations[conversation_id]
    assert [message.role for message in conversation.messages] == [
        "student",
        "assistant",
        "student",
        "assistant",
    ]
    assert provider.calls[-1] == [
        ChatModelMessage(role="user", content="我错过了一次作业截止时间。"),
        ChatModelMessage(role="assistant", content="先把延期风险告诉任课老师。"),
        ChatModelMessage(role="user", content="我应该怎么补救？"),
    ]
    app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_student_chat_stream_limits_model_context(
    app,
    async_client: AsyncClient,
) -> None:
    provider = _FakeChatProvider(["最近一轮上下文已收到。"])
    app.dependency_overrides[chat_model_provider] = lambda: provider
    app.dependency_overrides[get_settings] = lambda: Settings(
        chat_model_context_message_limit=8,
    )
    login = await _login(async_client, "student@example.edu")

    first = await async_client.post(
        "/api/v1/student/chat/stream",
        headers=_bearer(login["access_token"]),
        json={"message": "第一轮问题"},
    )
    assert first.status_code == 200
    conversation_id = next(iter(store.conversations))

    for index in range(1, 5):
        response = await async_client.post(
            "/api/v1/student/chat/stream",
            headers=_bearer(login["access_token"]),
            json={"conversationId": conversation_id, "message": f"后续问题 {index}"},
        )
        assert response.status_code == 200

    assert len(provider.calls[-1]) == 8
    assert provider.calls[-1][0].content == "最近一轮上下文已收到。"
    assert provider.calls[-1][-1].content == "后续问题 4"
    app.dependency_overrides.clear()


def test_dashscope_payload_skips_web_search_for_simple_prompts() -> None:
    provider = DashScopeChatModelProvider(
        Settings(
            DASHSCOPE_API_KEY="test-key",
            DASHSCOPE_API_MODE="compatible",
            DASHSCOPE_MODEL="qwen3.5-flash",
            ENABLE_THINKING=False,
            chat_model_max_tokens=384,
            chat_model_web_search_enabled=True,
            chat_model_web_search_strategy="turbo",
        )
    )

    payload = provider._build_payload([ChatModelMessage(role="user", content="请快速回复。")])

    assert payload["model"] == "qwen3.5-flash"
    assert payload["max_tokens"] == 384
    assert payload["stream"] is True
    assert payload["enable_thinking"] is False
    assert "enable_search" not in payload
    assert "search_options" not in payload


def test_dashscope_payload_uses_roomier_default_completion_budget() -> None:
    provider = DashScopeChatModelProvider(
        Settings(
            DASHSCOPE_API_KEY="test-key",
            DASHSCOPE_API_MODE="compatible",
            DASHSCOPE_MODEL="qwen3.5-flash",
        )
    )

    payload = provider._build_payload([ChatModelMessage(role="user", content="Summarize a file.")])

    assert payload["max_tokens"] == 4096


def test_dashscope_compatible_payload_marks_partial_assistant_prefix() -> None:
    provider = DashScopeChatModelProvider(
        Settings(
            DASHSCOPE_API_KEY="test-key",
            DASHSCOPE_API_MODE="compatible",
            DASHSCOPE_MODEL="qwen3.5-flash",
        )
    )

    payload = provider._build_payload(
        [
            ChatModelMessage(role="user", content="Summarize the uploaded file."),
            ChatModelMessage(
                role="assistant",
                content="Partial answer prefix",
                partial=True,
            ),
        ]
    )

    assert payload["messages"][-1] == {
        "role": "assistant",
        "content": "Partial answer prefix",
        "partial": True,
    }


def test_dashscope_payload_skips_web_search_for_temporal_counseling_prompts() -> None:
    provider = DashScopeChatModelProvider(
        Settings(
            DASHSCOPE_API_KEY="test-key",
            DASHSCOPE_API_MODE="compatible",
            DASHSCOPE_MODEL="qwen3.5-flash",
            chat_model_web_search_enabled=True,
            chat_model_web_search_strategy="turbo",
        )
    )

    payload = provider._build_payload([ChatModelMessage(role="user", content="我今天心情不好。")])

    assert "enable_search" not in payload
    assert "search_options" not in payload

    career_stress_payload = provider._build_payload(
        [ChatModelMessage(role="user", content="我今年就业压力很大。")]
    )

    assert "enable_search" not in career_stress_payload
    assert "search_options" not in career_stress_payload


def test_dashscope_payload_enables_web_search_for_current_fact_prompts() -> None:
    provider = DashScopeChatModelProvider(
        Settings(
            DASHSCOPE_API_KEY="test-key",
            DASHSCOPE_API_MODE="compatible",
            DASHSCOPE_MODEL="qwen3.5-flash",
            ENABLE_THINKING=False,
            chat_model_max_tokens=384,
            chat_model_web_search_enabled=True,
            chat_model_web_search_strategy="turbo",
        )
    )

    payload = provider._build_payload(
        [ChatModelMessage(role="user", content="请联网搜索今天最新的学校通知。")]
    )

    assert payload["model"] == "qwen3.5-flash"
    assert payload["max_tokens"] == 384
    assert payload["stream"] is True
    assert payload["enable_thinking"] is False
    assert payload["enable_search"] is True
    assert payload["search_options"] == {
        "search_strategy": "turbo",
    }


def test_dashscope_payload_honors_explicit_web_search_override() -> None:
    provider = DashScopeChatModelProvider(
        Settings(
            DASHSCOPE_API_KEY="test-key",
            DASHSCOPE_API_MODE="compatible",
            DASHSCOPE_MODEL="qwen3.5-flash",
            chat_model_web_search_enabled=True,
            chat_model_web_search_strategy="turbo",
        )
    )

    disabled_payload = provider._build_payload(
        [ChatModelMessage(role="user", content="Please search the latest school notice.")],
        ChatModelRunOptions(web_search=False),
    )
    enabled_payload = provider._build_payload(
        [ChatModelMessage(role="user", content="Please reply without extra context.")],
        ChatModelRunOptions(web_search=True),
    )

    assert "enable_search" not in disabled_payload
    assert enabled_payload["enable_search"] is True
    assert enabled_payload["search_options"] == {"search_strategy": "turbo"}


def test_dashscope_generation_payload_enables_sources_and_citations() -> None:
    provider = DashScopeChatModelProvider(
        Settings(
            DASHSCOPE_API_KEY="test-key",
            DASHSCOPE_MODEL="qwen-plus",
            DASHSCOPE_API_MODE="generation",
            chat_model_max_tokens=384,
            chat_model_web_search_enabled=True,
            chat_model_web_search_strategy="turbo",
            chat_model_search_source_enabled=True,
            chat_model_search_citation_enabled=True,
            chat_model_search_prepend_results=True,
        )
    )

    payload = provider._build_generation_payload(
        [ChatModelMessage(role="user", content="请联网搜索今天最新的学校通知。")]
    )

    assert payload["model"] == "qwen-plus"
    assert payload["input"]["messages"][-1] == {
        "role": "user",
        "content": "请联网搜索今天最新的学校通知。",
    }
    assert payload["parameters"]["incremental_output"] is True
    assert payload["parameters"]["max_tokens"] == 384
    assert payload["parameters"]["enable_search"] is True
    assert payload["parameters"]["search_options"] == {
        "search_strategy": "turbo",
        "enable_source": True,
        "enable_citation": True,
        "citation_format": "[ref_<number>]",
        "prepend_search_result": True,
    }


def test_dashscope_generation_payload_marks_partial_assistant_prefix() -> None:
    provider = DashScopeChatModelProvider(
        Settings(
            DASHSCOPE_API_KEY="test-key",
            DASHSCOPE_MODEL="qwen-plus",
            DASHSCOPE_API_MODE="generation",
        )
    )

    payload = provider._build_generation_payload(
        [
            ChatModelMessage(role="user", content="Summarize the uploaded file."),
            ChatModelMessage(
                role="assistant",
                content="Partial answer prefix",
                partial=True,
            ),
        ]
    )

    assert payload["input"]["messages"][-1] == {
        "role": "assistant",
        "content": "Partial answer prefix",
        "partial": True,
    }


def test_dashscope_generation_payload_skips_sources_without_search() -> None:
    provider = DashScopeChatModelProvider(
        Settings(
            DASHSCOPE_API_KEY="test-key",
            DASHSCOPE_MODEL="qwen-plus",
            DASHSCOPE_API_MODE="generation",
            chat_model_web_search_enabled=True,
        )
    )

    payload = provider._build_generation_payload(
        [ChatModelMessage(role="user", content="我今天心情不好。")]
    )

    assert "enable_search" not in payload["parameters"]
    assert "search_options" not in payload["parameters"]


def test_dashscope_responses_payload_enables_reasoning_and_web_search() -> None:
    provider = DashScopeChatModelProvider(
        Settings(
            DASHSCOPE_API_KEY="test-key",
            DASHSCOPE_API_MODE="responses",
            DASHSCOPE_RESPONSES_MODEL="qwen3.7-max",
            chat_model_max_tokens=384,
        )
    )

    payload = provider._build_responses_payload(
        [ChatModelMessage(role="user", content="请联网搜索今天最新的学校通知。")],
        ChatModelRunOptions(web_search=True, reasoning_enabled=True, mode="focus"),
    )

    assert payload["model"] == "qwen3.7-max"
    assert payload["max_output_tokens"] == 384
    assert payload["stream"] is True
    assert payload["input"][-1] == {
        "role": "user",
        "content": "请联网搜索今天最新的学校通知。",
    }
    assert payload["reasoning"] == {"effort": "high", "summary": "auto"}
    assert payload["tools"] == [{"type": "web_search"}]


def test_dashscope_responses_payload_can_disable_reasoning() -> None:
    provider = DashScopeChatModelProvider(
        Settings(
            DASHSCOPE_API_KEY="test-key",
            DASHSCOPE_API_MODE="responses",
            DASHSCOPE_RESPONSES_MODEL="qwen3.7-max",
            ENABLE_THINKING=True,
            chat_model_web_search_enabled=True,
        )
    )

    payload = provider._build_responses_payload(
        [ChatModelMessage(role="user", content="我今天心情不好。")],
        ChatModelRunOptions(reasoning_enabled=False),
    )

    assert payload["reasoning"] == {"effort": "none", "summary": "auto"}
    assert "tools" not in payload


def test_dashscope_generation_uses_native_model_config() -> None:
    provider = DashScopeChatModelProvider(
        Settings(
            DASHSCOPE_API_KEY="test-key",
            DASHSCOPE_MODEL="qwen3.5-flash",
            DASHSCOPE_API_MODE="generation",
        )
    )

    payload = provider._build_generation_payload(
        [ChatModelMessage(role="user", content="你好")]
    )

    assert payload["model"] == "qwen-plus"


def test_dashscope_generation_parser_extracts_source_reasoning_and_delta() -> None:
    line = (
        'data: {"output": {"search_info": {"search_results": ['
        '{"index": 1, "title": "学校官网通知", "url": "https://example.edu/news", '
        '"snippet": "通知摘要"}]}, "choices": [{"message": {'
        '"reasoning_content": "正在核对来源。", "content": "请参考学校官网通知。"}}]}}'
    )

    events = DashScopeChatModelProvider._parse_generation_sse_line(line)

    assert events[0] == ChatModelStreamEvent.source(
        {
            "title": "学校官网通知",
            "displayTitle": "学校官网通知",
            "display_title": "学校官网通知",
            "url": "https://example.edu/news",
            "snippet": "通知摘要",
            "hostname": "example.edu",
            "sourceQuality": "public_web",
            "trustLabel": "Public web source",
            "index": 1,
        }
    )
    assert events[1] == ChatModelStreamEvent.reasoning("正在核对来源。")
    assert events[2] == ChatModelStreamEvent.delta("请参考学校官网通知。")


def test_dashscope_source_parser_filters_non_public_urls() -> None:
    line = (
        'data: {"output": {"search_info": {"search_results": ['
        '{"title": "Local debug URL", "url": "http://localhost:8000/private"}, '
        '{"title": "Private network URL", "url": "http://10.0.0.8/private"}, '
        '{"title": "Public notice", "url": "https://example.edu/news"}'
        ']}, "choices": [{"message": {"content": "See public notice."}}]}}'
    )

    events = DashScopeChatModelProvider._parse_generation_sse_line(line)

    assert [
        event.data["url"]
        for event in events
        if event.type == "source"
    ] == ["https://example.edu/news"]


def test_dashscope_source_parser_uses_readable_title_fallback() -> None:
    line = (
        'data: {"output": {"search_info": {"search_results": ['
        '{"url": "https://news.example.edu/student-support/current-guide.html"}'
        ']}, "choices": [{"message": {"content": "See guide."}}]}}'
    )

    events = DashScopeChatModelProvider._parse_generation_sse_line(line)

    source = next(event.data for event in events if event.type == "source")
    assert source["title"] == "news.example.edu / current guide"
    assert source["displayTitle"] == "news.example.edu / current guide"
    assert source["title"] != "Untitled source"


def test_dashscope_generation_parser_extracts_real_citation_fields() -> None:
    line = (
        'data: {"output": {"choices": [{"message": {'
        '"citations": [{"marker": "[ref_1]", "title": "Notice", '
        '"url": "https://example.edu/news", "source_index": 1}], '
        '"content": "See [ref_1]."}}]}}'
    )

    events = DashScopeChatModelProvider._parse_generation_sse_line(line)

    assert events == [
        ChatModelStreamEvent.citation(
            {
                "marker": "[ref_1]",
                "title": "Notice",
                "url": "https://example.edu/news",
                "sourceIndex": 1,
            }
        ),
        ChatModelStreamEvent.delta("See [ref_1]."),
    ]


def test_dashscope_parser_reports_provider_length_stop() -> None:
    compatible_line = 'data: {"choices": [{"finish_reason": "length", "delta": {}}]}'
    generation_line = 'data: {"output": {"choices": [{"finish_reason": "max_tokens"}]}}'

    expected = [
        ChatModelStreamEvent.notice(
            "model_output_truncated",
            "Provider stopped because the configured output token budget was reached.",
        )
    ]

    assert DashScopeChatModelProvider._parse_compatible_sse_line(compatible_line) == expected
    assert DashScopeChatModelProvider._parse_generation_sse_line(generation_line) == expected


def test_dashscope_responses_parser_extracts_reasoning_tool_source_and_delta() -> None:
    reasoning_line = (
        'data: {"type": "response.reasoning_summary_text.delta", '
        '"delta": "正在拆解问题。"}'
    )
    search_line = (
        'data: {"type": "response.web_search_call.searching", '
        '"item_id": "ws_1"}'
    )
    source_line = (
        'data: {"type": "response.output_item.done", "item": {'
        '"id": "ws_1", "type": "web_search_call", "action": {"sources": ['
        '{"title": "学校官网通知", "url": "https://example.edu/news", '
        '"snippet": "通知摘要"}]}}}'
    )
    delta_line = 'data: {"type": "response.output_text.delta", "delta": "请参考学校官网通知。"}'

    assert DashScopeChatModelProvider._parse_responses_sse_line(reasoning_line) == [
        ChatModelStreamEvent.reasoning("正在拆解问题。")
    ]
    assert DashScopeChatModelProvider._parse_responses_sse_line(search_line) == [
        ChatModelStreamEvent.phase("searching"),
        ChatModelStreamEvent.tool_delta(
            "web_search",
            tool_call_id="ws_1",
            detail="Responses API is searching the web.",
        ),
    ]
    assert DashScopeChatModelProvider._parse_responses_sse_line(source_line) == [
        ChatModelStreamEvent.source(
            {
                "title": "学校官网通知",
                "displayTitle": "学校官网通知",
                "display_title": "学校官网通知",
                "url": "https://example.edu/news",
                "snippet": "通知摘要",
                "hostname": "example.edu",
                "sourceQuality": "public_web",
                "trustLabel": "Public web source",
            }
        ),
        ChatModelStreamEvent.tool_done(
            "web_search",
            tool_call_id="ws_1",
            status="success",
            detail="Responses API returned 1 source(s).",
            result_count=1,
        ),
    ]
    assert DashScopeChatModelProvider._parse_responses_sse_line(delta_line) == [
        ChatModelStreamEvent.delta("请参考学校官网通知。")
    ]


def test_dashscope_responses_message_done_keeps_references_without_duplicate_text() -> None:
    line = (
        'data: {"type": "response.output_item.done", "item": {'
        '"type": "message", "content": [{"type": "output_text", "text": "完整答案", '
        '"annotations": [{"type": "url_citation", "title": "Notice", '
        '"url": "https://example.edu/news"}]}]}}'
    )

    events = DashScopeChatModelProvider._parse_responses_sse_line(line)

    assert ChatModelStreamEvent.delta("完整答案") not in events
    assert events == [
        ChatModelStreamEvent.source(
            {
                "title": "Notice",
                "displayTitle": "Notice",
                "display_title": "Notice",
                "url": "https://example.edu/news",
                "hostname": "example.edu",
                "sourceQuality": "public_web",
                "trustLabel": "Public web source",
            }
        ),
        ChatModelStreamEvent.citation(
            {
                "title": "Notice",
                "url": "https://example.edu/news",
            }
        ),
    ]


def test_dashscope_generation_parser_surfaces_provider_errors() -> None:
    line = (
        'data: {"code": "InvalidParameter", "message": "url error, please check url", '
        '"request_id": "request-1"}'
    )

    events = DashScopeChatModelProvider._parse_generation_sse_line(line)

    assert events == [
        ChatModelStreamEvent(
            "provider_error",
            {
                "message": "url error, please check url",
                "code": "InvalidParameter",
                "requestId": "request-1",
            },
        )
    ]


def test_dashscope_compatible_parser_extracts_reasoning_and_delta() -> None:
    line = (
        'data: {"choices": [{"delta": {'
        '"reasoning_content": "正在拆解问题。", "content": "可以先列出任务。"}}]}'
    )

    events = DashScopeChatModelProvider._parse_compatible_sse_line(line)

    assert events == [
        ChatModelStreamEvent.reasoning("正在拆解问题。"),
        ChatModelStreamEvent.delta("可以先列出任务。"),
    ]


@pytest.mark.asyncio
async def test_knowledge_base_supports_create_update_delete(
    async_client: AsyncClient,
) -> None:
    login = await _login(async_client, "admin@example.edu")

    baseline = await async_client.get(
        "/api/v1/admin/knowledge",
        headers=_bearer(login["access_token"]),
    )
    assert baseline.status_code == 200
    assert len(baseline.json()) == 2

    created = await async_client.post(
        "/api/v1/admin/knowledge",
        headers=_bearer(login["access_token"]),
        json={
            "title": "Exam coping guide",
            "content": "Plan breaks, sleep, and use campus support.",
            "category": "wellbeing",
            "tags": ["exam", "stress"],
            "status": "draft",
        },
    )
    assert created.status_code == 201
    knowledge = created.json()
    assert knowledge["updated_by"] == "admin-1"
    assert knowledge["status"] == "draft"

    updated = await async_client.put(
        f"/api/v1/admin/knowledge/{knowledge['id']}",
        headers=_bearer(login["access_token"]),
        json={
            "title": "Exam coping guide",
            "content": "Plan breaks, sleep, and use campus support early.",
            "category": "wellbeing",
            "tags": ["exam", "stress", "support"],
            "status": "published",
        },
    )
    assert updated.status_code == 200
    assert updated.json()["status"] == "published"
    assert updated.json()["tags"] == ["exam", "stress", "support"]

    deleted = await async_client.delete(
        f"/api/v1/admin/knowledge/{knowledge['id']}",
        headers=_bearer(login["access_token"]),
    )
    assert deleted.status_code == 204

    after = await async_client.get(
        "/api/v1/admin/knowledge",
        headers=_bearer(login["access_token"]),
    )
    assert after.status_code == 200
    assert len(after.json()) == 2
    assert knowledge["id"] not in {item["id"] for item in after.json()}


@pytest.mark.asyncio
async def test_role_isolation_blocks_cross_role_access(async_client: AsyncClient) -> None:
    student = await _login(async_client, "student@example.edu")
    counselor = await _login(async_client, "counselor@example.edu")

    student_admin = await async_client.get(
        "/api/v1/admin/stats",
        headers=_bearer(student["access_token"]),
    )
    assert student_admin.status_code == 403

    student_counselor = await async_client.post(
        "/api/v1/counselor/assistance",
        headers=_bearer(student["access_token"]),
        json={"student_id": "student-1", "concern": "stress"},
    )
    assert student_counselor.status_code == 403

    counselor_admin = await async_client.get(
        "/api/v1/admin/knowledge",
        headers=_bearer(counselor["access_token"]),
    )
    assert counselor_admin.status_code == 403

    unauthenticated_me = await async_client.get("/api/v1/auth/me")
    assert unauthenticated_me.status_code == 401


@pytest.mark.asyncio
async def test_counselor_assistance_returns_crisis_guidance(async_client: AsyncClient) -> None:
    counselor = await _login(async_client, "counselor@example.edu")

    response = await async_client.post(
        "/api/v1/counselor/assistance",
        headers=_bearer(counselor["access_token"]),
        json={
            "student_id": "student-1",
            "concern": "The student mentioned suicide and immediate harm.",
            "context": "Urgent triage request",
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["risk_level"] == "urgent"
    assert "campus crisis protocol" in payload["suggested_response"]
    assert isinstance(payload["resources"], list)


@pytest.mark.asyncio
async def test_audit_trail_records_login_and_operational_events(
    async_client: AsyncClient,
) -> None:
    admin = await _login(async_client, "admin@example.edu")
    counselor = await _login(async_client, "counselor@example.edu")
    await _login(async_client, "student@example.edu")

    created = await async_client.post(
        "/api/v1/admin/knowledge",
        headers=_bearer(admin["access_token"]),
        json={
            "title": "Audit trail note",
            "content": "This entry exists to prove the audit stream.",
            "category": "reference",
            "tags": ["audit"],
            "status": "published",
        },
    )
    assert created.status_code == 201

    assistance = await async_client.post(
        "/api/v1/counselor/assistance",
        headers=_bearer(counselor["access_token"]),
        json={"student_id": "student-1", "concern": "stress"},
    )
    assert assistance.status_code == 200

    audit = await async_client.get(
        "/api/v1/admin/audit",
        headers=_bearer(admin["access_token"]),
    )
    assert audit.status_code == 200
    events = audit.json()
    actions = [event["action"] for event in events]
    assert "counselor.assistance.generate" in actions
    assert "knowledge.create" in actions
    assert "auth.login.success" in actions
    assert all("eventTags" in event for event in events)
    assert all("counterKey" in event for event in events)


@pytest.mark.asyncio
async def test_basic_stats_reflect_in_memory_activity(async_client: AsyncClient) -> None:
    admin = await _login(async_client, "admin@example.edu")
    student = await _login(async_client, "student@example.edu")

    created = await async_client.post(
        "/api/v1/admin/knowledge",
        headers=_bearer(admin["access_token"]),
        json={
            "title": "Stats note",
            "content": "Used to validate counters.",
            "category": "general",
            "tags": ["stats"],
            "status": "published",
        },
    )
    assert created.status_code == 201

    conversation = await async_client.post(
        "/api/v1/student/conversations",
        headers=_bearer(student["access_token"]),
        json={"title": "Stats conversation", "message": "Need a check-in."},
    )
    assert conversation.status_code == 201

    stats = await async_client.get(
        "/api/v1/admin/stats",
        headers=_bearer(admin["access_token"]),
    )
    assert stats.status_code == 200
    assert stats.json() == {
        "users": 3,
        "knowledge_items": 3,
        "published_knowledge_items": 3,
        "conversations": 1,
        "messages": 2,
        "audit_events": 3,
    }

    assert len(store.conversations) == 1
