from __future__ import annotations

from pathlib import Path
import sys
import unittest

from pydantic import ValidationError


BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from app.api.v1.qa_pairs import (  # noqa: E402
    QaPairCreate,
    QaPairUpdate,
    QaStatusUpdate,
    normalize_tag,
    normalize_tags,
)


class QaPairsApiTests(unittest.TestCase):
    def test_create_payload_rejects_blank_question_or_answer(self) -> None:
        with self.assertRaises(ValidationError):
            QaPairCreate(question="   ", answer="standard answer")

        with self.assertRaises(ValidationError):
            QaPairCreate(question="question", answer="   ")

    def test_update_payload_rejects_blank_question_or_answer(self) -> None:
        with self.assertRaises(ValidationError):
            QaPairUpdate(question="   ")

        with self.assertRaises(ValidationError):
            QaPairUpdate(answer="   ")

    def test_status_payload_rejects_unknown_status(self) -> None:
        with self.assertRaises(ValidationError):
            QaStatusUpdate(status="archived")

    def test_tags_are_trimmed_deduplicated_and_filter_tag_is_normalized(self) -> None:
        self.assertEqual(normalize_tag("  scholarship   policy  "), "scholarship policy")
        self.assertEqual(
            normalize_tags([" scholarship ", "", "finance", "scholarship"]),
            ["scholarship", "finance"],
        )

        payload = QaPairCreate(
            question="  when is recruitment talk  ",
            answer="line 1\nline 2\n",
            tags=[" campus ", "campus", " jobs "],
        )

        self.assertEqual(payload.question, "when is recruitment talk")
        self.assertEqual(payload.answer, "line 1\nline 2")
        self.assertEqual(payload.tags, ["campus", "jobs"])


if __name__ == "__main__":
    unittest.main()
