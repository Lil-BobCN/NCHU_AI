from __future__ import annotations

from pathlib import Path
import sys
import unittest


BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from pydantic import ValidationError  # noqa: E402

from app.api.v1.chat import ChatRequest  # noqa: E402
from app.api.v1.internal import AccessScope, InternalChatRequest, UserContext  # noqa: E402
from app.api.v1.retrieval import SearchRequest  # noqa: E402
from app.core.config import get_settings  # noqa: E402


class ApiLimitTests(unittest.TestCase):
    def test_chat_request_rejects_oversized_top_k(self) -> None:
        settings = get_settings()

        with self.assertRaises(ValidationError):
            ChatRequest(question="测试问题", top_k=settings.chat_max_top_k + 1)

    def test_chat_request_strips_question(self) -> None:
        payload = ChatRequest(question="  测试问题  ")

        self.assertEqual(payload.question, "测试问题")

    def test_internal_chat_request_rejects_oversized_question(self) -> None:
        settings = get_settings()

        with self.assertRaises(ValidationError):
            InternalChatRequest(
                question="x" * (settings.chat_max_question_chars + 1),
                user_context=UserContext(user_id="1001"),
                access_scope=AccessScope(scope_mode="all_public"),
            )

    def test_retrieval_request_rejects_oversized_rerank_top_k(self) -> None:
        settings = get_settings()

        with self.assertRaises(ValidationError):
            SearchRequest(query="测试问题", rerank_top_k=settings.retrieval_max_rerank_top_k + 1)


if __name__ == "__main__":
    unittest.main()
