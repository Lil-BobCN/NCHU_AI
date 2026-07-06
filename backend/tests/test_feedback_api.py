from __future__ import annotations

from pathlib import Path
import sys
import unittest

from pydantic import ValidationError


BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from app.api.v1.feedback import ALLOWED_ERROR_TYPES, AnswerFeedbackCreate  # noqa: E402


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


if __name__ == "__main__":
    unittest.main()
