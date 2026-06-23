from __future__ import annotations

import asyncio
import unittest
from datetime import datetime, timezone

from pathlib import Path
import sys


BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from app.db.models import Conversation  # noqa: E402
from app.api.v1.conversations import backfill_default_conversation_titles  # noqa: E402
from app.services.chat_service import ChatService  # noqa: E402
from app.services.conversation_title import (  # noqa: E402
    DEFAULT_CONVERSATION_TITLE,
    auto_title_from_question,
    should_auto_title_conversation,
    validate_manual_conversation_title,
)


class ConversationTitleTests(unittest.TestCase):
    def test_auto_title_compacts_and_truncates_question(self) -> None:
        title = auto_title_from_question("  转学政策需要准备什么材料，以及有哪些不得转学情形？  ")

        self.assertEqual(title, "转学政策需要准备什么材料，以及有哪...")

    def test_manual_title_must_not_be_empty(self) -> None:
        with self.assertRaises(ValueError):
            validate_manual_conversation_title("   ")

    def test_default_empty_conversation_can_be_auto_titled(self) -> None:
        self.assertTrue(should_auto_title_conversation(DEFAULT_CONVERSATION_TITLE, 0))
        self.assertTrue(should_auto_title_conversation("", 0))

    def test_non_default_title_or_non_empty_conversation_is_not_auto_titled(self) -> None:
        self.assertFalse(should_auto_title_conversation("奖学金咨询", 0))
        self.assertFalse(should_auto_title_conversation(DEFAULT_CONVERSATION_TITLE, 2))

    def test_chat_service_auto_titles_default_empty_conversation(self) -> None:
        service = ChatService()
        db = FakeTitleSession()
        conversation = Conversation(title=DEFAULT_CONVERSATION_TITLE)
        conversation.id = "conv-1"
        conversation.message_count = 0

        asyncio.run(service._auto_title_conversation_if_needed(db, conversation, "转学政策需要准备什么材料"))

        self.assertEqual(conversation.title, "转学政策需要准备什么材料")
        self.assertEqual(db.updated_values["title"], "转学政策需要准备什么材料")
        self.assertEqual(db.commit_count, 1)

    def test_chat_service_preserves_manual_title(self) -> None:
        service = ChatService()
        db = FakeTitleSession()
        conversation = Conversation(title="我的转学咨询")
        conversation.id = "conv-1"
        conversation.message_count = 0

        asyncio.run(service._auto_title_conversation_if_needed(db, conversation, "转学政策需要准备什么材料"))

        self.assertEqual(conversation.title, "我的转学咨询")
        self.assertEqual(db.updated_values, {})
        self.assertEqual(db.commit_count, 0)

    def test_backfill_default_title_uses_first_user_question(self) -> None:
        db = FakeBackfillSession({"conv-1": "奖学金申请需要准备哪些材料"})
        default_conversation = Conversation(title=DEFAULT_CONVERSATION_TITLE)
        default_conversation.id = "conv-1"
        custom_conversation = Conversation(title="保留手动标题")
        custom_conversation.id = "conv-2"

        asyncio.run(backfill_default_conversation_titles(db, [default_conversation, custom_conversation]))

        self.assertEqual(default_conversation.title, "奖学金申请需要准备哪些材料")
        self.assertEqual(custom_conversation.title, "保留手动标题")
        self.assertEqual(db.updated_titles, ["奖学金申请需要准备哪些材料"])
        self.assertEqual(db.commit_count, 1)


class FakeTitleSession:
    def __init__(self) -> None:
        self.updated_values: dict = {}
        self.commit_count = 0

    async def execute(self, statement):
        if str(statement).startswith("UPDATE conversations"):
            self.updated_values = {}
            for key, bind in statement._values.items():
                name = getattr(key, "key", str(key))
                value = getattr(bind, "value", bind)
                if isinstance(value, datetime):
                    value = value.astimezone(timezone.utc)
                self.updated_values[name] = value
        return None

    async def commit(self) -> None:
        self.commit_count += 1


class FakeBackfillSession:
    def __init__(self, first_questions: dict[str, str]) -> None:
        self.first_questions = first_questions
        self.updated_titles: list[str] = []
        self.commit_count = 0

    async def scalar(self, statement):
        params = dict(statement.compile().params)
        conversation_id = self._first_param(params, "conversation_id")
        return self.first_questions.get(str(conversation_id))

    async def execute(self, statement):
        if str(statement).startswith("UPDATE conversations"):
            for key, bind in statement._values.items():
                if getattr(key, "key", str(key)) == "title":
                    self.updated_titles.append(getattr(bind, "value", bind))
        return None

    async def commit(self) -> None:
        self.commit_count += 1

    def _first_param(self, params: dict, prefix: str) -> object:
        for key, value in params.items():
            if key == prefix or key.startswith(f"{prefix}_"):
                return value
        return None


if __name__ == "__main__":
    unittest.main()
