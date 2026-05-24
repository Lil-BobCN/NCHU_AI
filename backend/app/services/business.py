"""In-memory Phase 1 business services for the AI counselor API."""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from uuid import uuid4


def utc_now() -> datetime:
    """Return a timezone-aware UTC timestamp."""
    return datetime.now(UTC)


@dataclass(slots=True)
class User:
    id: str
    email: str
    display_name: str
    role: str
    password: str
    demo_account: bool = True
    session_state: str = "authenticated"


@dataclass(slots=True)
class TokenSession:
    token: str
    user_id: str
    issued_at: datetime
    provider: str


@dataclass(slots=True)
class KnowledgeItem:
    id: str
    title: str
    content: str
    category: str
    tags: list[str]
    status: str
    updated_by: str
    created_at: datetime
    updated_at: datetime


@dataclass(slots=True)
class Resource:
    id: str
    title: str
    summary: str
    category: str
    tags: list[str]
    source_knowledge_id: str


@dataclass(slots=True)
class Message:
    id: str
    role: str
    content: str
    created_at: datetime
    resources: list[Resource] = field(default_factory=list)


@dataclass(slots=True)
class Conversation:
    id: str
    student_id: str
    title: str
    messages: list[Message]
    created_at: datetime
    updated_at: datetime


@dataclass(slots=True)
class AuditEvent:
    id: str
    actor_id: str
    actor_role: str
    action: str
    target_type: str
    target_id: str
    result: str
    event_tags: list[str]
    counter_key: str | None
    created_at: datetime


class BusinessStore:
    """Small in-memory business layer used until persistent services land."""

    def __init__(self) -> None:
        self.users: dict[str, User] = {
            "student-1": User(
                id="student-1",
                email="student@example.edu",
                display_name="Demo Student",
                role="student",
                password="password",
            ),
            "counselor-1": User(
                id="counselor-1",
                email="counselor@example.edu",
                display_name="Demo Counselor",
                role="counselor",
                password="password",
            ),
            "admin-1": User(
                id="admin-1",
                email="admin@example.edu",
                display_name="Demo Admin",
                role="admin",
                password="password",
            ),
        }
        now = utc_now()
        self.knowledge: dict[str, KnowledgeItem] = {
            "knowledge-1": KnowledgeItem(
                id="knowledge-1",
                title="Managing Academic Stress",
                content=(
                    "Students under academic stress should start with sleep, food, "
                    "workload triage, and an appointment with a counselor when distress persists."
                ),
                category="wellbeing",
                tags=["stress", "academic"],
                status="published",
                updated_by="admin-1",
                created_at=now,
                updated_at=now,
            ),
            "knowledge-2": KnowledgeItem(
                id="knowledge-2",
                title="Campus Counseling Intake",
                content=(
                    "Students can request a counseling intake for anxiety, mood concerns, "
                    "relationship stress, adjustment issues, or urgent support routing."
                ),
                category="services",
                tags=["intake", "support"],
                status="published",
                updated_by="admin-1",
                created_at=now,
                updated_at=now,
            ),
        }
        self.tokens: dict[str, TokenSession] = {}
        self.conversations: dict[str, Conversation] = {}
        self.audit_events: list[AuditEvent] = []

    def reset(self) -> None:
        """Reset the in-memory store to its seeded state."""
        self.__init__()

    def authenticate_local(self, username: str, password: str) -> TokenSession | None:
        user = next(
            (item for item in self.users.values() if item.email == username or item.id == username),
            None,
        )
        if user is None or user.password != password:
            self.record_audit(
                "anonymous",
                "auth.login.failure",
                "auth",
                "local-demo-login",
                result="failure",
                event_tags=["auth:local"],
                counter_key="auth.login.failure.count",
            )
            return None
        return self._issue_token(user.id, "local")

    def authenticate_sso(
        self,
        provider: str,
        external_subject: str,
        email: str | None,
    ) -> TokenSession:
        user = next((item for item in self.users.values() if item.email == email), None)
        if user is None:
            user_id = f"sso-{uuid4().hex[:8]}"
            user = User(
                id=user_id,
                email=email or f"{external_subject}@{provider}.local",
                display_name=email.split("@", 1)[0] if email else external_subject,
                role="student",
                password="",
                demo_account=True,
            )
            self.users[user_id] = user
        return self._issue_token(user.id, provider)

    def user_for_token(self, token: str) -> User | None:
        session = self.tokens.get(token)
        if session is None:
            return None
        return self.users.get(session.user_id)

    def answer_question(self, student_id: str, question: str) -> Message:
        resources = self.search_resources(question)
        summary = (
            resources[0].summary
            if resources
            else "please contact counseling services for support."
        )
        guidance = (
            "I can help you think through this. Based on the current campus guidance, "
            f"{summary}"
        )
        if "harm" in question.lower() or "suicide" in question.lower():
            guidance = (
                "If there is immediate danger, contact local emergency services now. "
                "For urgent counseling support, reach the campus counseling center immediately."
            )
        return Message(
            id=f"msg-{uuid4().hex}",
            role="assistant",
            content=guidance,
            created_at=utc_now(),
            resources=resources,
        )

    def search_resources(self, query: str = "", category: str | None = None) -> list[Resource]:
        terms = {part.lower() for part in query.split() if part.strip()}
        resources: list[Resource] = []
        for item in self.knowledge.values():
            if item.status != "published":
                continue
            if category and item.category != category:
                continue
            haystack = " ".join([item.title, item.content, item.category, *item.tags]).lower()
            if terms and not any(term in haystack for term in terms):
                continue
            resources.append(
                Resource(
                    id=f"resource-{item.id}",
                    title=item.title,
                    summary=item.content,
                    category=item.category,
                    tags=list(item.tags),
                    source_knowledge_id=item.id,
                )
            )
        return resources

    def create_conversation(self, student_id: str, title: str, message: str | None) -> Conversation:
        now = utc_now()
        messages: list[Message] = []
        if message:
            messages.append(
                Message(id=f"msg-{uuid4().hex}", role="student", content=message, created_at=now)
            )
            messages.append(self.answer_question(student_id, message))
        conversation = Conversation(
            id=f"conv-{uuid4().hex}",
            student_id=student_id,
            title=title,
            messages=messages,
            created_at=now,
            updated_at=utc_now(),
        )
        self.conversations[conversation.id] = conversation
        return conversation

    def add_student_message(self, conversation: Conversation, content: str) -> Conversation:
        conversation.messages.append(
            Message(id=f"msg-{uuid4().hex}", role="student", content=content, created_at=utc_now())
        )
        conversation.messages.append(self.answer_question(conversation.student_id, content))
        conversation.updated_at = utc_now()
        return conversation

    def create_knowledge(
        self,
        actor_id: str,
        title: str,
        content: str,
        category: str,
        tags: list[str],
        status: str,
    ) -> KnowledgeItem:
        now = utc_now()
        item = KnowledgeItem(
            id=f"knowledge-{uuid4().hex}",
            title=title,
            content=content,
            category=category,
            tags=tags,
            status=status,
            updated_by=actor_id,
            created_at=now,
            updated_at=now,
        )
        self.knowledge[item.id] = item
        self.record_audit(
            actor_id,
            "knowledge.create",
            "knowledge",
            item.id,
            event_tags=["resource:knowledge"],
            counter_key="knowledge.write.count",
        )
        return item

    def update_knowledge(
        self,
        actor_id: str,
        item: KnowledgeItem,
        title: str,
        content: str,
        category: str,
        tags: list[str],
        status: str,
    ) -> KnowledgeItem:
        item.title = title
        item.content = content
        item.category = category
        item.tags = tags
        item.status = status
        item.updated_by = actor_id
        item.updated_at = utc_now()
        self.record_audit(
            actor_id,
            "knowledge.update",
            "knowledge",
            item.id,
            event_tags=["resource:knowledge"],
            counter_key="knowledge.write.count",
        )
        return item

    def delete_knowledge(self, actor_id: str, item_id: str) -> None:
        del self.knowledge[item_id]
        self.record_audit(
            actor_id,
            "knowledge.delete",
            "knowledge",
            item_id,
            event_tags=["resource:knowledge"],
            counter_key="knowledge.write.count",
        )

    def record_audit(
        self,
        actor_id: str,
        action: str,
        target_type: str,
        target_id: str,
        result: str = "success",
        event_tags: list[str] | None = None,
        counter_key: str | None = None,
    ) -> None:
        actor = self.users.get(actor_id)
        actor_role = actor.role if actor else "anonymous"
        tags = ["demo", f"role:{actor_role}", f"result:{result}", *(event_tags or [])]
        self.audit_events.append(
            AuditEvent(
                id=f"audit-{uuid4().hex}",
                actor_id=actor_id,
                actor_role=actor_role,
                action=action,
                target_type=target_type,
                target_id=target_id,
                result=result,
                event_tags=list(dict.fromkeys(tags)),
                counter_key=counter_key or f"{action}.count",
                created_at=utc_now(),
            )
        )

    def stats(self) -> dict[str, int]:
        return {
            "users": len(self.users),
            "knowledge_items": len(self.knowledge),
            "published_knowledge_items": sum(
                1 for item in self.knowledge.values() if item.status == "published"
            ),
            "conversations": len(self.conversations),
            "messages": sum(len(item.messages) for item in self.conversations.values()),
            "audit_events": len(self.audit_events),
        }

    def _issue_token(self, user_id: str, provider: str) -> TokenSession:
        session = TokenSession(
            token=f"phase1-{uuid4().hex}",
            user_id=user_id,
            issued_at=utc_now(),
            provider=provider,
        )
        self.tokens[session.token] = session
        self.record_audit(
            user_id,
            "auth.login.success",
            "user",
            user_id,
            event_tags=[f"auth:{provider}"],
            counter_key="auth.login.success.count",
        )
        return session


store = BusinessStore()
