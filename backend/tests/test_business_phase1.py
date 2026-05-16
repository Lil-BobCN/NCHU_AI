"""Acceptance tests for the Phase 1 business API surface."""
from __future__ import annotations

import pytest
from httpx import AsyncClient

from app.services.business import store


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
        "email": "student@example.edu",
        "name": "Student One",
        "role": "student",
    }


@pytest.mark.asyncio
async def test_mock_sso_callback_issues_token(async_client: AsyncClient) -> None:
    response = await async_client.post(
        "/api/v1/auth/sso/callback",
        json={
            "provider": "campus-sso",
            "code": "sso-code-123",
            "email": "fresh.student@example.edu",
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["provider"] == "campus-sso"
    assert payload["token_type"] == "bearer"
    assert payload["user"]["email"] == "fresh.student@example.edu"
    assert payload["user"]["role"] == "student"
    assert payload["access_token"]


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
        "email": "student@example.edu",
        "name": "Student One",
        "role": "student",
    }


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
    actions = [event["action"] for event in audit.json()]
    assert "counselor.assistance" in actions
    assert "knowledge.create" in actions
    assert "auth.login" in actions


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
