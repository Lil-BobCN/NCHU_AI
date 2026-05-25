"""Acceptance tests for the Phase 1 business API surface."""
from __future__ import annotations

import pytest
from httpx import AsyncClient

from app.api.v1.deps import chat_model_provider
from app.services.business import store
from app.services.chat_model import ChatModelMessage


async def _login(async_client: AsyncClient, username: str, password: str = "password") -> dict:
    response = await async_client.post(
        "/api/v1/auth/login",
        json={"username": username, "password": password},
    )
    assert response.status_code == 200
    return response.json()


def _bearer(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


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

    @property
    def configured(self) -> bool:
        return self._configured

    async def stream_reply(self, messages: list[ChatModelMessage]):
        self.calls.append(messages)
        for chunk in self.chunks:
            yield chunk


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
