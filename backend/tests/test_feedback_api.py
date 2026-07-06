from __future__ import annotations

import asyncio
from datetime import datetime, timezone
from pathlib import Path
import sys
import unittest

from pydantic import ValidationError
from sqlalchemy import select
from sqlalchemy.dialects import postgresql


BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from app.api.v1.feedback import (  # noqa: E402
    ALLOWED_ERROR_TYPES,
    AnswerFeedbackCreate,
    _feedback_assistant_message_id_filter,
    _feedback_id_filter,
    router,
    submit_answer_feedback,
)
from app.db.models import AnswerFeedback  # noqa: E402


class FakeMessage:
    id = "11111111-1111-1111-1111-111111111111"
    conversation_id = "22222222-2222-2222-2222-222222222222"
    role = "assistant"
    content = "回答"
    citations = []
    created_at = datetime.now(timezone.utc)


class FakeUserMessage:
    id = "33333333-3333-3333-3333-333333333333"
    content = "问题"


class FakeAdmin:
    id = "44444444-4444-4444-4444-444444444444"


class FakeDb:
    def __init__(self) -> None:
        self.scalar_values = [FakeMessage(), FakeUserMessage(), None, None, 1]
        self.added = None

    async def scalar(self, _statement):
        return self.scalar_values.pop(0)

    def add(self, item):
        self.added = item

    async def flush(self):
        return None

    async def commit(self):
        return None


class FeedbackApiTests(unittest.TestCase):
    def test_feedback_payload_accepts_supported_error_types(self) -> None:
        for error_type in ALLOWED_ERROR_TYPES:
            payload = AnswerFeedbackCreate(
                assistant_message_id="message-1",
                error_type=error_type,
                description="  说明  ",
            )

            self.assertEqual(payload.error_type, error_type)
            self.assertEqual(payload.description, "说明")

    def test_feedback_payload_rejects_unsupported_error_type(self) -> None:
        with self.assertRaises(ValidationError):
            AnswerFeedbackCreate(
                assistant_message_id="message-1",
                error_type="bad_type",
                description="",
            )

    def test_cancel_feedback_route_is_registered(self) -> None:
        paths = {route.path for route in router.routes}

        self.assertIn("/feedback/answers/{feedback_id}/cancel", paths)

    def test_feedback_id_filters_cast_uuid_columns_to_string(self) -> None:
        dialect = postgresql.dialect()

        by_id = str(select(AnswerFeedback).where(_feedback_id_filter("feedback-1")).compile(dialect=dialect))
        by_assistant = str(
            select(AnswerFeedback)
            .where(_feedback_assistant_message_id_filter("message-1"))
            .compile(dialect=dialect)
        )

        self.assertIn("CAST(answer_feedbacks.id AS VARCHAR)", by_id)
        self.assertIn("CAST(answer_feedbacks.assistant_message_id AS VARCHAR)", by_assistant)

    def test_submit_feedback_generates_id_without_database_default(self) -> None:
        db = FakeDb()
        payload = AnswerFeedbackCreate(
            assistant_message_id=FakeMessage.id,
            error_type="other",
            description="说明",
        )

        response = asyncio.run(submit_answer_feedback(payload, db, FakeAdmin()))

        self.assertEqual(response["code"], 0)
        self.assertIsInstance(db.added, AnswerFeedback)
        self.assertTrue(db.added.id)
        self.assertEqual(response["data"]["id"], db.added.id)


if __name__ == "__main__":
    unittest.main()
