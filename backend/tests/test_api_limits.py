from __future__ import annotations

from pathlib import Path
import sys
import unittest


BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from pydantic import ValidationError  # noqa: E402
from sqlalchemy import select  # noqa: E402
from sqlalchemy.dialects import postgresql  # noqa: E402

from app.api.v1.chat import ChatRequest  # noqa: E402
from app.api.v1.qa_pairs import QaPairCreate, QaPairUpdate, qa_pair_duplicate_question_filters, qa_pair_list_filters  # noqa: E402
from app.api.v1.retrieval import SearchRequest  # noqa: E402
from app.core.config import get_settings  # noqa: E402
from app.db.models import QaPair  # noqa: E402


class ApiLimitTests(unittest.TestCase):
    def test_chat_request_rejects_oversized_top_k(self) -> None:
        settings = get_settings()

        with self.assertRaises(ValidationError):
            ChatRequest(question="测试问题", top_k=settings.chat_max_top_k + 1)

    def test_chat_request_strips_question(self) -> None:
        payload = ChatRequest(question="  测试问题  ")

        self.assertEqual(payload.question, "测试问题")

    def test_retrieval_request_rejects_oversized_rerank_top_k(self) -> None:
        settings = get_settings()

        with self.assertRaises(ValidationError):
            SearchRequest(query="测试问题", rerank_top_k=settings.retrieval_max_rerank_top_k + 1)

    def test_qa_pair_create_requires_question_and_answer(self) -> None:
        with self.assertRaises(ValidationError):
            QaPairCreate(question="   ", answer="有效答案")

        with self.assertRaises(ValidationError):
            QaPairCreate(question="有效问题", answer="   ")

    def test_qa_pair_create_strips_question_and_answer(self) -> None:
        payload = QaPairCreate(question="  有效问题  ", answer="  有效答案  ", tags=[])

        self.assertEqual(payload.question, "有效问题")
        self.assertEqual(payload.answer, "有效答案")
        self.assertEqual(payload.tags, [])

    def test_qa_pair_update_rejects_blank_question_or_answer(self) -> None:
        with self.assertRaises(ValidationError):
            QaPairUpdate(question="   ")

        with self.assertRaises(ValidationError):
            QaPairUpdate(answer="   ")

    def test_qa_pair_update_allows_optional_tags(self) -> None:
        payload = QaPairUpdate(tags=[])

        self.assertEqual(payload.tags, [])

    def test_qa_pair_list_filters_use_exact_tag_array_contains(self) -> None:
        statement = select(QaPair).where(*qa_pair_list_filters(tag=" 奖学金 "))

        compiled = str(statement.compile(dialect=postgresql.dialect()))

        self.assertIn("qa_pairs.tags @>", compiled)
        self.assertIn("qa_pairs.deleted_at IS NULL", compiled)

    def test_qa_pair_duplicate_question_filter_uses_exact_question_match(self) -> None:
        statement = select(QaPair).where(*qa_pair_duplicate_question_filters("完全一致的问题"))

        compiled = str(statement.compile(dialect=postgresql.dialect()))

        self.assertIn("qa_pairs.question = ", compiled)
        self.assertIn("qa_pairs.deleted_at IS NULL", compiled)


if __name__ == "__main__":
    unittest.main()
