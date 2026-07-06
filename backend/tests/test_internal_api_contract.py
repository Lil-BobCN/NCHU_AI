from __future__ import annotations

from pathlib import Path
import sys
import unittest

from sqlalchemy.dialects import postgresql


BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from app.api.deps import CurrentUser  # noqa: E402
from app.api.v1.internal import (  # noqa: E402
    InternalChatRetractRequest,
    _can_access_conversation,
    _conversation_filters,
    _java_session_to_uuid,
    _serialize_job,
    _serialize_message,
)
from app.db.models import AnswerFeedback, Conversation, ConversationMessage, DocumentJob  # noqa: E402


class InternalApiContractTests(unittest.TestCase):
    def test_serialize_job_uses_java_polling_job_id_field(self) -> None:
        job = DocumentJob(document_id="doc-1", job_type="document_full_pipeline", status="pending", progress=0)
        job.id = "job-1"
        job.message = "已加入处理队列"
        job.error_message = None
        job.result = {}
        job.created_at = None
        job.updated_at = None

        data = _serialize_job(job)

        self.assertEqual(data["job_id"], "job-1")
        self.assertEqual(data["rag_doc_id"], "doc-1")
        self.assertEqual(data["job_type"], "document_full_pipeline")

    def test_assistant_message_feedback_is_nested_for_java_contract(self) -> None:
        message = ConversationMessage(conversation_id="conv-1", role="assistant", content="answer")
        message.id = "msg-1"
        message.rewritten_query = "query"
        message.retrieval_trace = {}
        message.citations = []
        message.suggested_questions = []
        message.created_at = None
        feedback = AnswerFeedback(
            conversation_id="conv-1",
            assistant_message_id="msg-1",
            error_type="answer_wrong",
            description="不准确",
            status="open",
        )
        feedback.id = "fb-1"

        data = _serialize_message(message, feedback)

        self.assertEqual(data["feedback"]["id"], "fb-1")
        self.assertEqual(data["feedback"]["error_type"], "answer_wrong")
        self.assertEqual(data["feedback"]["status"], "open")

    def test_internal_retract_request_supports_java_session_mapping(self) -> None:
        payload = InternalChatRetractRequest(
            session_id="java-session-1",
            user_message_id="user-message-1",
            assistant_message_id="assistant-message-1",
        )

        self.assertEqual(payload.session_id, "java-session-1")
        self.assertEqual(
            _java_session_to_uuid("java-session-1"),
            _java_session_to_uuid("java-session-1"),
        )

    def test_conversation_filter_matches_java_user_and_owner_uuid(self) -> None:
        filters = _conversation_filters(
            created_by="java-user-1",
            owner_id="9a66f24f-4700-42b5-888c-5e0752d7bff1",
        )

        sql = " ".join(
            str(item.compile(dialect=postgresql.dialect(), compile_kwargs={"literal_binds": True}))
            for item in filters
        )

        self.assertIn("java-user-1", sql)
        self.assertIn("9a66f24f-4700-42b5-888c-5e0752d7bff1", sql)
        self.assertIn("conversations.created_by", sql)

    def test_conversation_access_accepts_owner_context_metadata(self) -> None:
        conversation = Conversation(title="测试会话")
        conversation.id = "conv-1"
        conversation.created_by = "11111111-1111-1111-1111-111111111111"
        conversation.context_state = {
            "owner_id": "9a66f24f-4700-42b5-888c-5e0752d7bff1",
            "created_by": "java-user-1",
        }
        current_user = CurrentUser(
            id="9a66f24f-4700-42b5-888c-5e0752d7bff1",
            user_id="java-user-1",
            login_id="sys_user:java-user-1",
        )

        self.assertTrue(_can_access_conversation(conversation, current_user))


if __name__ == "__main__":
    unittest.main()
