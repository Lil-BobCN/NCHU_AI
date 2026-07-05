from __future__ import annotations

from pathlib import Path
import asyncio
from datetime import datetime, timezone
import json
import sys
import unittest


BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from app.services.chat_service import ChatService, SMALLTALK_WELCOME  # noqa: E402


class ChatServiceFollowupTests(unittest.TestCase):
    def test_answer_cache_key_changes_with_corpus_version(self) -> None:
        service = ChatService()
        retrieval = {
            "answer_context": [
                {
                    "chunk_id": "chunk-1",
                    "document_id": "doc-1",
                    "document_title": "doc.pdf",
                    "content": "same context",
                }
            ],
            "corpus_version": {"knowledge_base_version": 1},
        }
        updated_retrieval = {
            **retrieval,
            "corpus_version": {"knowledge_base_version": 2},
        }

        self.assertNotEqual(
            service._answer_cache_key("same question", retrieval),
            service._answer_cache_key("same question", updated_retrieval),
        )

    def test_answer_prompts_include_numbering_rules(self) -> None:
        service = ChatService()

        basic_prompt = service._build_messages("测试流程", [], [])[0]["content"]
        memory_prompt = service._build_messages_with_memory("测试流程", [], [], "")[0]["content"]

        for prompt in (basic_prompt, memory_prompt):
            self.assertIn("流程步骤编号规则", prompt)
            self.assertIn("不要把多个主步骤都写成 1", prompt)
            self.assertIn("引用法规条文、原文序号、年份、金额、页码时必须保留原样", prompt)

    def test_concrete_new_topic_is_not_rewritten_with_history(self) -> None:
        service = ChatService()

        self.assertFalse(service._looks_like_followup("差旅网上审批流程是咋样的"))
        self.assertFalse(service._looks_like_followup("网上差旅审批操作流程是什么"))

    def test_explicit_or_underspecified_followup_still_uses_history(self) -> None:
        service = ChatService()

        self.assertTrue(service._looks_like_followup("这个怎么处理"))
        self.assertTrue(service._looks_like_followup("甲方是谁"))
        self.assertTrue(service._looks_like_followup("付款方式是什么"))

    def test_pending_confirmation_uses_resume_query(self) -> None:
        service = ChatService()
        state = {
            "active_task": {
                "topic": "奖学金申报说明文档",
                "user_goal": "针对奖学金申报说明文档，梳理家庭情况内容",
                "resume_query": "针对奖学金申报说明文档，梳理家庭情况内容",
            },
            "pending_action": {
                "type": "confirm_continue",
                "assistant_question": "是否需要我继续按家庭情况维度梳理？",
                "resume_query": "针对奖学金申报说明文档，梳理家庭情况内容",
            },
        }

        resolution = asyncio.run(service._resolve_context("可以", [], "", state))

        self.assertEqual(resolution["intent"], "confirm_pending")
        self.assertEqual(resolution["resolved_query"], "针对奖学金申报说明文档，梳理家庭情况内容")
        self.assertTrue(resolution["uses_context_state"])
        self.assertTrue(resolution["clear_pending"])

    def test_new_topic_after_pending_does_not_confirm_old_task(self) -> None:
        service = ChatService()
        state = {
            "active_task": {
                "topic": "奖学金申报说明文档",
                "user_goal": "针对奖学金申报说明文档，梳理家庭情况内容",
                "resume_query": "针对奖学金申报说明文档，梳理家庭情况内容",
            },
            "pending_action": {
                "type": "confirm_continue",
                "assistant_question": "是否需要我继续按家庭情况维度梳理？",
                "resume_query": "针对奖学金申报说明文档，梳理家庭情况内容",
            },
        }

        resolution = asyncio.run(service._resolve_context("可以，那转学需要准备什么", [], "", state))

        self.assertEqual(resolution["intent"], "new_topic")
        self.assertEqual(resolution["resolved_query"], "可以，那转学需要准备什么")
        self.assertTrue(resolution["clear_pending"])

    def test_context_state_sets_pending_when_answer_requests_confirmation(self) -> None:
        service = ChatService()
        state = service._refresh_context_state(
            {},
            "帮我梳理奖学金家庭情况",
            "针对奖学金申报说明文档，梳理家庭情况内容",
            "我可以继续按家庭情况、经济来源、特殊困难三部分整理，是否需要继续？",
            [{"document_title": "奖学金申报说明文档"}],
            {"intent": "new_topic", "reason": "standalone question"},
        )

        self.assertEqual(state["active_task"]["topic"], "奖学金申报说明文档")
        self.assertEqual(
            state["pending_action"]["resume_query"],
            "针对奖学金申报说明文档，梳理家庭情况内容",
        )

    def test_contextual_retrieval_query_reinforces_followup_with_active_topic(self) -> None:
        service = ChatService()
        query = service._build_contextual_retrieval_query(
            "还需要哪些材料？",
            "奖学金申请还需要哪些材料？",
            {
                "active_task": {
                    "topic": "奖学金申请政策",
                    "user_goal": "梳理奖学金申请条件和材料",
                    "target_documents": ["奖学金申请说明.pdf"],
                    "resume_query": "奖学金申请条件和材料",
                }
            },
            {"intent": "followup", "uses_history": True, "uses_context_state": True},
        )

        self.assertIn("上下文主题：奖学金申请政策", query)
        self.assertIn("目标文档：奖学金申请说明.pdf", query)
        self.assertIn("当前追问：还需要哪些材料？", query)
        self.assertIn("完整检索意图：奖学金申请还需要哪些材料？", query)

    def test_contextual_retrieval_query_skips_explicit_new_topic(self) -> None:
        service = ChatService()
        query = service._build_contextual_retrieval_query(
            "转学需要准备什么？",
            "转学需要准备什么？",
            {"active_task": {"topic": "奖学金申请政策"}},
            {"intent": "new_topic", "uses_history": False, "uses_context_state": False},
        )

        self.assertEqual(query, "转学需要准备什么？")

    def test_retrieval_constraints_preserve_followup_topic(self) -> None:
        service = ChatService()
        constraints = service._build_retrieval_constraints(
            "还需要哪些材料？",
            "奖学金申请还需要哪些材料？",
            "上下文主题：奖学金申请政策\n目标文档：奖学金申请说明.pdf\n当前追问：还需要哪些材料？",
            {
                "active_task": {
                    "topic": "奖学金申请政策",
                    "user_goal": "梳理奖学金申请条件和材料",
                    "target_documents": ["奖学金申请说明.pdf"],
                    "resume_query": "奖学金申请条件和材料",
                }
            },
            {"intent": "followup", "uses_history": True, "uses_context_state": True},
        )

        self.assertTrue(constraints["is_followup"])
        self.assertEqual(constraints["constraint_strength"], "strict")
        self.assertEqual(constraints["active_topic"], "奖学金申请政策")
        self.assertEqual(constraints["target_documents"], ["奖学金申请说明.pdf"])

    def test_retrieval_constraints_do_not_bind_explicit_new_topic(self) -> None:
        service = ChatService()
        constraints = service._build_retrieval_constraints(
            "转学需要准备什么？",
            "转学需要准备什么？",
            "转学需要准备什么？",
            {"active_task": {"topic": "奖学金申请政策", "target_documents": ["奖学金申请说明.pdf"]}},
            {"intent": "new_topic", "uses_history": False, "uses_context_state": False},
        )

        self.assertFalse(constraints["is_followup"])
        self.assertEqual(constraints["constraint_strength"], "none")

    def test_discard_stream_turn_removes_messages_and_clears_empty_conversation(self) -> None:
        service = ChatService()
        db = FakeDiscardSession(
            messages=[
                FakeMessage("user-1", "conv-1", "user", "发错的问题"),
                FakeMessage("assistant-1", "conv-1", "assistant", ""),
            ]
        )

        result = asyncio.run(service._discard_stream_turn(db, "conv-1", "user-1", "assistant-1"))

        self.assertEqual(db.messages, [])
        self.assertIn("user-1", result["discarded_message_ids"])
        self.assertIn("assistant-1", result["discarded_message_ids"])
        self.assertTrue(result["deleted_conversation"])
        self.assertFalse(result["reset_memory"])
        self.assertEqual(db.deleted_logs_for, ["user-1"])
        self.assertEqual(db.conversation_values["message_count"], 0)
        self.assertEqual(db.conversation_values["summary"], "")
        self.assertEqual(db.conversation_values["context_state"], {})
        self.assertIsNotNone(db.conversation_values["deleted_at"])

    def test_discard_completed_turn_resets_memory_to_avoid_context_pollution(self) -> None:
        service = ChatService()
        db = FakeDiscardSession(
            messages=[
                FakeMessage("old-user", "conv-1", "user", "之前的问题"),
                FakeMessage("old-assistant", "conv-1", "assistant", "之前的回答"),
                FakeMessage("user-2", "conv-1", "user", "发错的问题"),
                FakeMessage("assistant-2", "conv-1", "assistant", "半截回答"),
            ]
        )

        result = asyncio.run(service._discard_stream_turn(db, "conv-1", "user-2", "assistant-2"))

        self.assertEqual([item.id for item in db.messages], ["old-user", "old-assistant"])
        self.assertFalse(result["deleted_conversation"])
        self.assertTrue(result["reset_memory"])
        self.assertEqual(db.conversation_values["message_count"], 2)
        self.assertEqual(db.conversation_values["summary"], "")
        self.assertEqual(db.conversation_values["context_state"], {})
        self.assertIsNone(db.conversation_values["deleted_at"])

    def test_direct_qa_hit_streams_standard_answer_without_model_generation(self) -> None:
        service = ChatService()
        service.retrieval_service = FakeDirectQaRetrievalService()
        service.model_service = FakeNoModelService()
        db = FakeChatStreamSession()

        async def consume() -> list[str]:
            events = []
            async for event in service.stream_chat(
                db,
                "申请奖学金需要准备哪些材料",
                None,
                enable_suggested_questions=False,
            ):
                events.append(event)
            return events

        events = asyncio.run(consume())
        answer = ""
        direct_payload = None
        citations = None
        for event in events:
            if event.startswith("event: answer_cache"):
                direct_payload = json.loads(event.split("data: ", 1)[1])
            if event.startswith("event: delta"):
                answer += json.loads(event.split("data: ", 1)[1]).get("content", "")
            if event.startswith("event: citations"):
                citations = json.loads(event.split("data: ", 1)[1]).get("citations")

        self.assertEqual(answer, "标准答案：准备申请表、成绩证明和家庭经济困难说明。")
        self.assertEqual(direct_payload["type"], "direct_qa")
        self.assertEqual(citations[0]["qa_pair_id"], "qa-1")
        self.assertEqual(citations[0]["tags"], ["奖学金"])
        self.assertFalse(service.model_service.stream_called)
        self.assertTrue(db.retrieval_logs)
        self.assertTrue(db.retrieval_logs[0].answer.startswith("标准答案"))


    def test_smalltalk_greeting_bypasses_retrieval_and_citations(self) -> None:
        service = ChatService()
        service.retrieval_service = FakeNoRetrievalService()
        service.model_service = FakeNoModelService()
        db = FakeChatStreamSession()

        async def consume() -> list[str]:
            events = []
            async for event in service.stream_chat(
                db,
                "你好",
                None,
                enable_suggested_questions=False,
            ):
                events.append(event)
            return events

        events = asyncio.run(consume())
        answer = ""
        citations = None
        event_names = [event.split("\n", 1)[0].replace("event: ", "") for event in events]
        for event in events:
            if event.startswith("event: delta"):
                answer += json.loads(event.split("data: ", 1)[1]).get("content", "")
            if event.startswith("event: citations"):
                citations = json.loads(event.split("data: ", 1)[1]).get("citations")

        self.assertEqual(answer, SMALLTALK_WELCOME)
        self.assertEqual(citations, [])
        self.assertNotIn("retrieval_start", event_names)
        self.assertNotIn("retrieval_done", event_names)
        self.assertFalse(service.model_service.stream_called)
        self.assertTrue(db.retrieval_logs)
        self.assertEqual(db.retrieval_logs[0].recall_results, [])
        self.assertEqual(db.retrieval_logs[0].citations, [])


class FakeMessage:
    def __init__(self, message_id: str, conversation_id: str, role: str, content: str) -> None:
        self.id = message_id
        self.conversation_id = conversation_id
        self.role = role
        self.content = content
        self.created_at = datetime.now(timezone.utc)


class FakeScalarResult:
    def __init__(self, value: object) -> None:
        self.value = value

    def scalar(self) -> object:
        return self.value


class FakeScalarsResult:
    def __init__(self, values: list[object]) -> None:
        self.values = values

    def scalars(self):
        return self.values


class FakeDiscardSession:
    def __init__(self, messages: list[FakeMessage]) -> None:
        self.messages = messages
        self.deleted_logs_for: list[str] = []
        self.conversation_values: dict = {}

    async def scalar(self, statement) -> object:
        statement_text = str(statement)
        params = self._statement_params(statement)
        if "conversation_messages.content" in statement_text:
            message_id = self._first_param(params, "id")
            for item in self.messages:
                if item.id == message_id:
                    return item.content
            return None
        if "count(*)" in statement_text:
            conversation_id = self._first_param(params, "conversation_id")
            return sum(1 for item in self.messages if item.conversation_id == conversation_id)
        if "SELECT conversation_messages.created_at" in statement_text:
            conversation_id = self._first_param(params, "conversation_id")
            matched = [item for item in self.messages if item.conversation_id == conversation_id]
            return max((item.created_at for item in matched), default=None)
        return None

    async def execute(self, statement):
        statement_text = str(statement)
        params = self._statement_params(statement)
        if statement_text.startswith("DELETE FROM retrieval_logs"):
            message_id = self._first_param(params, "message_id")
            if message_id:
                self.deleted_logs_for.append(message_id)
            return FakeScalarResult(None)
        if statement_text.startswith("DELETE FROM conversation_messages"):
            ids = self._message_id_set(params)
            self.messages = [item for item in self.messages if item.id not in ids]
            return FakeScalarResult(None)
        if statement_text.startswith("UPDATE conversations"):
            self.conversation_values = self._extract_update_values(statement)
            return FakeScalarResult(None)
        return FakeScalarResult(None)

    async def commit(self) -> None:
        return None

    def _statement_params(self, statement) -> dict:
        return dict(statement.compile().params)

    def _first_param(self, params: dict, prefix: str) -> object:
        for key, value in params.items():
            if key == prefix or key.startswith(f"{prefix}_"):
                return value
        return None

    def _message_id_set(self, params: dict) -> set[str]:
        for key, value in params.items():
            if key == "id" or key.startswith("id_"):
                if isinstance(value, (list, tuple, set)):
                    return {str(item) for item in value}
                if value:
                    return {str(value)}
        return set()

    def _extract_update_values(self, statement) -> dict:
        values = {}
        for key, bind in statement._values.items():
            name = getattr(key, "key", str(key))
            values[name] = getattr(bind, "value", bind)
        return values


class FakeNoModelService:
    def __init__(self) -> None:
        self.stream_called = False

    async def stream_answer(self, messages):
        self.stream_called = True
        yield "不应该生成"

    async def complete_text(self, messages) -> str:
        return ""


class FakeDirectQaRetrievalService:
    async def find_direct_qa_answer(self, db, query, document_ids=None, context_constraints=None):
        return {
            "qa_pair_id": "qa-1",
            "qa_question": "申请奖学金需要准备哪些材料",
            "qa_answer": "标准答案：准备申请表、成绩证明和家庭经济困难说明。",
            "document_id": None,
            "document_title": None,
            "document_name": None,
            "section_path": "QA问答对",
            "page_start": None,
            "page_end": None,
            "url": "http://example.local/qa",
            "tags": ["奖学金"],
            "source": "qa_direct_exact",
            "score": 1.0,
        }

    async def search(self, *args, **kwargs):
        raise AssertionError("direct QA hit should skip document retrieval")

    def _citations(self, results):
        return [
            {
                "document_id": str(item["document_id"]) if item.get("document_id") else None,
                "document_title": item["document_title"],
                "document_name": item["document_name"],
                "chunk_id": None,
                "qa_pair_id": item.get("qa_pair_id"),
                "page_start": None,
                "page_end": None,
                "section_path": item["section_path"],
                "url": item["url"],
                "tags": item.get("tags") or [],
                "images": [],
            }
            for item in results
            if item.get("document_id") or item.get("qa_pair_id")
        ]

    def citations_for_answer(self, query, answer, contexts):
        return []


class FakeNoRetrievalService:
    async def find_direct_qa_answer(self, *args, **kwargs):
        raise AssertionError("smalltalk should skip direct QA")

    async def search(self, *args, **kwargs):
        raise AssertionError("smalltalk should skip retrieval")

    def citations_for_answer(self, *args, **kwargs):
        raise AssertionError("smalltalk should skip citations")


class FakeChatStreamSession:
    def __init__(self) -> None:
        self.conversation = None
        self.messages = []
        self.retrieval_logs = []

    def add(self, item) -> None:
        from app.db.models import Conversation, ConversationMessage, RetrievalLog

        if isinstance(item, Conversation):
            if not getattr(item, "id", None):
                item.id = "conv-1"
            if getattr(item, "summary", None) is None:
                item.summary = ""
            if getattr(item, "context_state", None) is None:
                item.context_state = {}
            self.conversation = item
        elif isinstance(item, ConversationMessage):
            if not getattr(item, "id", None):
                item.id = f"msg-{len(self.messages) + 1}"
            self.messages.append(item)
        elif isinstance(item, RetrievalLog):
            self.retrieval_logs.append(item)

    async def commit(self) -> None:
        return None

    async def refresh(self, item) -> None:
        if not getattr(item, "id", None):
            item.id = "generated-id"

    async def scalar(self, statement):
        return None

    async def execute(self, statement):
        statement_text = str(statement)
        if statement_text.startswith("UPDATE conversations"):
            if self.conversation is not None:
                for key, bind in statement._values.items():
                    name = getattr(key, "key", str(key))
                    setattr(self.conversation, name, getattr(bind, "value", bind))
            return FakeScalarResult(None)
        if "FROM conversation_messages" in statement_text:
            return FakeScalarsResult([])
        return FakeScalarResult(None)


if __name__ == "__main__":
    unittest.main()
