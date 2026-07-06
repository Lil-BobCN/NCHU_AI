from __future__ import annotations

from pathlib import Path
import sys
import unittest

from pydantic import ValidationError
from sqlalchemy import select
from sqlalchemy.dialects import postgresql


BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from app.api.v1.feedback import ALLOWED_ERROR_TYPES, AnswerFeedbackCreate, answer_feedback_cancel_filters  # noqa: E402
from app.db.models import AnswerFeedback  # noqa: E402


class FeedbackApiTests(unittest.TestCase):
    def test_feedback_payload_accepts_supported_error_types(self) -> None:
        for error_type in ALLOWED_ERROR_TYPES:
            payload = AnswerFeedbackCreate(
                conversation_id="conversation-1",
                assistant_message_id="message-1",
                error_type=error_type,
                description="  说明  ",
            )

            self.assertEqual(payload.error_type, error_type)
            self.assertEqual(payload.description, "说明")

    def test_feedback_payload_accepts_empty_description(self) -> None:
        payload = AnswerFeedbackCreate(
            conversation_id="conversation-1",
            assistant_message_id="message-1",
            error_type="answer_wrong",
        )

        self.assertEqual(payload.description, "")

    def test_feedback_payload_rejects_unsupported_error_type(self) -> None:
        with self.assertRaises(ValidationError):
            AnswerFeedbackCreate(
                conversation_id="conversation-1",
                assistant_message_id="message-1",
                error_type="bad_type",
                description="",
            )

    def test_answer_feedback_cancel_filters_target_only_open_feedback(self) -> None:
        statement = select(AnswerFeedback).where(*answer_feedback_cancel_filters("message-1", "conversation-1"))

        compiled = str(statement.compile(dialect=postgresql.dialect()))
        params = statement.compile(dialect=postgresql.dialect()).params

        self.assertIn("answer_feedbacks.assistant_message_id = ", compiled)
        self.assertIn("answer_feedbacks.conversation_id = ", compiled)
        self.assertIn("answer_feedbacks.status = ", compiled)
        self.assertIn("open", params.values())


if __name__ == "__main__":
    unittest.main()
