import asyncio
import hashlib
import json
import re
import time
from collections.abc import AsyncGenerator
from datetime import datetime, timezone

from sqlalchemy import delete, func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.json_utils import to_jsonable
from app.db.models import Conversation, ConversationMessage, RetrievalLog
from app.services.model_service import ModelService
from app.services.redis_service import RedisService
from app.services.retrieval_service import RetrievalService
from app.services.conversation_title import (
    DEFAULT_CONVERSATION_TITLE,
    auto_title_from_question,
    should_auto_title_conversation,
)


RECENT_HISTORY_ROUNDS = 12
RECENT_HISTORY_MESSAGE_LIMIT = RECENT_HISTORY_ROUNDS * 2
HISTORY_ITEM_CHAR_LIMIT = 1800
SUMMARY_MAX_CHARS = 2400
SUMMARY_SEED_MESSAGE_LIMIT = 120
SMALLTALK_WELCOME = (
    "您好，我是学校 RAG 智能问答助手。您可以直接提问校内政策、办事流程、材料要求、联系方式等问题，"
    "我会根据知识库资料为您查找并回答。"
)
NO_RELEVANT_CONTEXT_ANSWER = "资料中未找到与该问题匹配的明确依据，暂时无法基于现有知识库回答。请补充相关资料后再提问。"


class ChatService:
    def __init__(self) -> None:
        self.settings = get_settings()
        self.model_service = ModelService()
        self.redis_service = RedisService()
        self.retrieval_service = RetrievalService()

    async def stream_chat(
        self,
        db: AsyncSession,
        question: str,
        conversation_id: str | None,
        enable_suggested_questions: bool = True,
        top_k: int | None = None,
        rerank_top_k: int | None = None,
        document_ids: list[str] | None = None,
        enable_rewrite: bool = True,
    ) -> AsyncGenerator[str, None]:
        started = time.perf_counter()
        conversation: Conversation | None = None
        user_message: ConversationMessage | None = None
        assistant_message: ConversationMessage | None = None
        try:
            conversation = await self._get_or_create_conversation(db, conversation_id, question)
            await self._auto_title_conversation_if_needed(db, conversation, question)
            conversation_summary = (conversation.summary or "").strip()
            context_state = self._normalize_context_state(getattr(conversation, "context_state", None))
            summary_seed = []
            if not conversation_summary:
                summary_seed = await self._load_summary_seed(db, str(conversation.id))
            history = await self._load_recent_history(db, str(conversation.id))
            is_smalltalk = self._is_smalltalk_greeting(question)
            context_resolution = (
                self._smalltalk_context_resolution(question)
                if is_smalltalk
                else await self._resolve_context(
                question,
                history,
                conversation_summary,
                context_state,
                enable_rewrite=enable_rewrite,
                )
            )
            resolved_query = context_resolution["resolved_query"]
            retrieval_query = self._build_contextual_retrieval_query(
                question,
                resolved_query,
                context_state,
                context_resolution,
            )
            retrieval_reinforced = retrieval_query != resolved_query
            retrieval_constraints = self._build_retrieval_constraints(
                question,
                resolved_query,
                retrieval_query,
                context_state,
                context_resolution,
            )
            context_resolution = {
                **context_resolution,
                "retrieval_query": retrieval_query,
                "retrieval_query_reinforced": retrieval_reinforced,
                "retrieval_constraints": retrieval_constraints,
            }
            uses_history = bool(context_resolution.get("uses_history"))
            rewritten_with_history = retrieval_query != question.strip()
            user_message = ConversationMessage(
                conversation_id=conversation.id,
                role="user",
                content=question,
                rewritten_query=retrieval_query,
            )
            db.add(user_message)
            await db.commit()
            await db.refresh(user_message)

            assistant_message = ConversationMessage(
                conversation_id=conversation.id,
                role="assistant",
                content="",
                model_name=self.settings.chat_model,
            )
            db.add(assistant_message)
            await db.commit()
            await db.refresh(assistant_message)

            yield self._sse(
                "message_start",
                {
                    "conversation_id": str(conversation.id),
                    "conversation_title": conversation.title,
                    "user_message_id": str(user_message.id),
                    "assistant_message_id": str(assistant_message.id),
                    "history_count": len(history),
                    "history_rounds": self._history_round_count(history),
                    "has_summary": bool(conversation_summary),
                    "context_resolution": context_resolution,
                },
            )

            if is_smalltalk:
                retrieval = self._empty_retrieval_trace(
                    question,
                    resolved_query,
                    retrieval_query,
                    retrieval_reinforced,
                    retrieval_constraints,
                    history,
                    conversation_summary,
                    context_resolution,
                    context_state,
                )
                citations: list[dict] = []
                suggested_questions: list[dict] = []
                answer = self._sanitize_answer(SMALLTALK_WELCOME)
                async for event in self._stream_delta_text(answer):
                    yield event
                yield self._sse("citations", {"citations": citations})
                yield self._sse("suggested_questions", {"questions": suggested_questions})

                latency_ms = int((time.perf_counter() - started) * 1000)
                assistant_message.content = answer
                assistant_message.retrieval_trace = to_jsonable(retrieval)
                assistant_message.citations = to_jsonable(citations)
                assistant_message.suggested_questions = to_jsonable(suggested_questions)
                assistant_message.latency_ms = latency_ms
                db.add(
                    RetrievalLog(
                        conversation_id=conversation.id,
                        message_id=user_message.id,
                        raw_query=question,
                        rewritten_query=retrieval_query,
                        recall_results=[],
                        rerank_results=[],
                        final_context=[],
                        citations=[],
                        suggested_questions=[],
                        answer=answer,
                        model_name=self.settings.chat_model,
                        embedding_model=self.settings.embedding_model,
                        rerank_model=self.settings.rerank_model,
                        latency_ms=latency_ms,
                    )
                )
                now = datetime.now(timezone.utc)
                await db.execute(
                    update(Conversation)
                    .where(Conversation.id == conversation.id)
                    .values(
                        message_count=Conversation.message_count + 2,
                        summary="",
                        context_state={},
                        last_message_at=now,
                        updated_at=now,
                    )
                )
                await db.commit()
                yield self._sse("message_end", {"message_id": str(assistant_message.id), "latency_ms": latency_ms})
                return

            yield self._sse(
                "retrieval_start",
                {
                    "query": retrieval_query,
                    "resolved_query": resolved_query,
                    "uses_history": uses_history,
                    "rewritten_with_history": rewritten_with_history,
                    "retrieval_query_reinforced": retrieval_reinforced,
                    "context_intent": context_resolution.get("intent"),
                    "context_constraints": retrieval_constraints,
                },
            )
            direct_qa_hit = await self.retrieval_service.find_direct_qa_answer(
                db,
                resolved_query,
                document_ids=document_ids,
                context_constraints=retrieval_constraints,
            )
            if direct_qa_hit:
                direct_qa_context = [to_jsonable(direct_qa_hit)]
                retrieval = {
                    "raw_query": retrieval_query,
                    "rewritten_query": resolved_query,
                    "original_query": question,
                    "recall_results": direct_qa_context,
                    "rerank_results": direct_qa_context,
                    "final_context": direct_qa_context,
                    "answer_context": direct_qa_context,
                    "citations": to_jsonable(self.retrieval_service._citations([direct_qa_hit])),
                    "retrieval_options": {
                        "document_ids": document_ids or None,
                        "direct_qa_hit": True,
                        "context_constraints": retrieval_constraints,
                    },
                    "direct_qa_hit": True,
                    "direct_qa": to_jsonable(direct_qa_hit),
                }
            else:
                retrieval = to_jsonable(
                    await self.retrieval_service.search(
                        db,
                        retrieval_query,
                        top_k=top_k,
                        rerank_top_k=rerank_top_k,
                        document_ids=document_ids,
                        context_constraints=retrieval_constraints,
                    )
                )
                retrieval["direct_qa_hit"] = False
            retrieval["original_query"] = question
            retrieval["resolved_query"] = resolved_query
            retrieval["retrieval_query"] = retrieval_query
            retrieval["retrieval_query_reinforced"] = retrieval_reinforced
            retrieval["context_constraints"] = retrieval_constraints
            retrieval["history_count"] = len(history)
            retrieval["conversation_summary"] = conversation_summary
            retrieval["context_resolution"] = context_resolution
            retrieval["context_state"] = context_state
            answer_context = retrieval.get("answer_context") or retrieval["final_context"]
            yield self._sse(
                "retrieval",
                {
                    "recall_count": len(retrieval["recall_results"]),
                    "rerank_count": len(retrieval["rerank_results"]),
                },
            )
            yield self._sse(
                "retrieval_done",
                {
                    "recall_count": len(retrieval["recall_results"]),
                    "rerank_count": len(retrieval["rerank_results"]),
                    "citation_count": len(retrieval["citations"]),
                },
            )

            answer_parts: list[str] = []
            used_fallback = False
            cached_answer = None
            no_effective_context = not retrieval.get("direct_qa_hit") and not answer_context
            if not retrieval.get("direct_qa_hit") and not no_effective_context:
                cached_answer = await self._get_cached_answer(question, retrieval, history, conversation_summary)
            if cached_answer:
                answer_parts.append(cached_answer)
                yield self._sse("answer_cache", {"hit": True})
                async for event in self._stream_delta_text(cached_answer):
                    yield event
            elif retrieval.get("direct_qa_hit"):
                answer = str((retrieval.get("direct_qa") or {}).get("qa_answer") or "").strip()
                if answer:
                    answer_parts.append(answer)
                    yield self._sse(
                        "answer_cache",
                        {
                            "hit": True,
                            "type": "direct_qa",
                            "qa_pair_id": (retrieval.get("direct_qa") or {}).get("qa_pair_id"),
                        },
                    )
                    async for event in self._stream_delta_text(answer):
                        yield event
            elif no_effective_context:
                used_fallback = True
                retrieval["no_match"] = True
                retrieval["no_match_reason"] = retrieval.get("no_match_reason") or "no_effective_answer_context"
                answer_parts.append(NO_RELEVANT_CONTEXT_ANSWER)
                async for event in self._stream_delta_text(NO_RELEVANT_CONTEXT_ANSWER):
                    yield event
            else:
                messages = self._build_messages_with_memory(
                    question,
                    answer_context,
                    history,
                    conversation_summary,
                    context_state,
                    context_resolution,
                )
                try:
                    async for delta in self.model_service.stream_answer(messages):
                        answer_parts.append(delta)
                        async for event in self._stream_delta_text(delta):
                            yield event
                except Exception:
                    used_fallback = True
                    fallback = self._fallback_answer(answer_context)
                    answer_parts.append(fallback)
                    async for event in self._stream_delta_text(fallback):
                        yield event

            answer = "".join(answer_parts).strip()
            answer = self._sanitize_answer(answer)
            if answer and not cached_answer and not used_fallback and not retrieval.get("direct_qa_hit"):
                await self._set_cached_answer(question, retrieval, history, conversation_summary, answer)
            citations = to_jsonable(
                self.retrieval_service.citations_for_answer(retrieval_query, answer, answer_context)
            )
            suggested_questions = []
            if enable_suggested_questions:
                suggested_questions = to_jsonable(
                    await self._suggest_questions(question, answer, answer_context)
                )

            yield self._sse("citations", {"citations": citations})
            yield self._sse("suggested_questions", {"questions": suggested_questions})

            latency_ms = int((time.perf_counter() - started) * 1000)
            assistant_message.content = answer
            assistant_message.retrieval_trace = to_jsonable(retrieval)
            assistant_message.citations = to_jsonable(citations)
            assistant_message.suggested_questions = to_jsonable(suggested_questions)
            assistant_message.latency_ms = latency_ms
            updated_summary = await self._refresh_conversation_summary(
                conversation_summary,
                summary_seed,
                question,
                answer,
            )
            updated_context_state = self._refresh_context_state(
                context_state,
                question,
                resolved_query,
                answer,
                answer_context,
                context_resolution,
            )
            db.add(
                RetrievalLog(
                    conversation_id=conversation.id,
                    message_id=user_message.id,
                    raw_query=question,
                    rewritten_query=retrieval_query,
                    recall_results=to_jsonable(retrieval["recall_results"]),
                    rerank_results=to_jsonable(retrieval["rerank_results"]),
                    final_context=to_jsonable(answer_context),
                    citations=to_jsonable(citations),
                    suggested_questions=to_jsonable(suggested_questions),
                    answer=answer,
                    model_name=self.settings.chat_model,
                    embedding_model=self.settings.embedding_model,
                    rerank_model=self.settings.rerank_model,
                    latency_ms=latency_ms,
                )
            )
            now = datetime.now(timezone.utc)
            await db.execute(
                update(Conversation)
                .where(Conversation.id == conversation.id)
                .values(
                    message_count=Conversation.message_count + 2,
                    summary=updated_summary,
                    context_state=to_jsonable(updated_context_state),
                    last_message_at=now,
                    updated_at=now,
                )
            )
            await db.commit()
            yield self._sse("message_end", {"message_id": str(assistant_message.id), "latency_ms": latency_ms})
        except (asyncio.CancelledError, GeneratorExit):
            if conversation is not None:
                await self._discard_stream_turn(
                    db,
                    str(conversation.id),
                    str(user_message.id) if user_message is not None else None,
                    str(assistant_message.id) if assistant_message is not None else None,
                )
            raise

    async def chat_once(
        self,
        db: AsyncSession,
        question: str,
        conversation_id: str | None,
        enable_suggested_questions: bool = True,
        top_k: int | None = None,
        rerank_top_k: int | None = None,
        document_ids: list[str] | None = None,
        enable_rewrite: bool = True,
    ) -> dict:
        answer = ""
        citations = []
        suggested = []
        user_message_id: str | None = None
        retrieval_trace: dict | None = None
        async for event in self.stream_chat(
            db,
            question,
            conversation_id,
            enable_suggested_questions,
            top_k,
            rerank_top_k,
            document_ids,
            enable_rewrite,
        ):
            if event.startswith("event: delta"):
                payload = json.loads(event.split("data: ", 1)[1])
                answer += payload.get("content", "")
            elif event.startswith("event: citations"):
                payload = json.loads(event.split("data: ", 1)[1])
                citations = payload.get("citations", [])
            elif event.startswith("event: suggested_questions"):
                payload = json.loads(event.split("data: ", 1)[1])
                suggested = payload.get("questions", [])
            elif event.startswith("event: message_start"):
                payload = json.loads(event.split("data: ", 1)[1])
                user_message_id = payload.get("user_message_id")
        if user_message_id:
            log = await db.scalar(
                select(RetrievalLog)
                .where(RetrievalLog.message_id == user_message_id)
                .order_by(RetrievalLog.created_at.desc())
            )
            if log:
                retrieval_trace = {
                    "raw_query": log.raw_query,
                    "rewritten_query": log.rewritten_query,
                    "recall_results": log.recall_results,
                    "rerank_results": log.rerank_results,
                    "final_context": log.final_context,
                    "citations": log.citations,
                    "latency_ms": log.latency_ms,
                }
        return {
            "answer": answer,
            "citations": citations,
            "suggested_questions": suggested,
            "retrieval_trace": retrieval_trace or {},
        }

    async def retract_turn(
        self,
        db: AsyncSession,
        conversation_id: str,
        user_message_id: str,
        assistant_message_id: str,
    ) -> dict:
        return await self._discard_stream_turn(
            db,
            conversation_id,
            user_message_id,
            assistant_message_id,
        )

    async def _discard_stream_turn(
        self,
        db: AsyncSession,
        conversation_id: str,
        user_message_id: str | None,
        assistant_message_id: str | None,
    ) -> dict:
        now = datetime.now(timezone.utc)
        message_ids = [message_id for message_id in (user_message_id, assistant_message_id) if message_id]
        had_completed_assistant = False

        if assistant_message_id:
            assistant_content = await db.scalar(
                select(ConversationMessage.content).where(
                    ConversationMessage.conversation_id == conversation_id,
                    ConversationMessage.id == assistant_message_id,
                    ConversationMessage.role == "assistant",
                )
            )
            had_completed_assistant = bool((assistant_content or "").strip())

        if user_message_id:
            await db.execute(delete(RetrievalLog).where(RetrievalLog.message_id == user_message_id))

        if message_ids:
            await db.execute(
                delete(ConversationMessage).where(
                    ConversationMessage.conversation_id == conversation_id,
                    ConversationMessage.id.in_(message_ids),
                )
            )

        remaining_count = (
            await db.scalar(
                select(func.count())
                .select_from(ConversationMessage)
                .where(ConversationMessage.conversation_id == conversation_id)
            )
        ) or 0
        latest_message_at = await db.scalar(
            select(ConversationMessage.created_at)
            .where(ConversationMessage.conversation_id == conversation_id)
            .order_by(ConversationMessage.created_at.desc())
            .limit(1)
        )

        values = {
            "message_count": remaining_count,
            "last_message_at": latest_message_at,
            "updated_at": now,
            "deleted_at": now if remaining_count == 0 else None,
        }
        if remaining_count == 0 or had_completed_assistant:
            values["summary"] = ""
            values["context_state"] = {}

        await db.execute(update(Conversation).where(Conversation.id == conversation_id).values(**values))
        await db.commit()
        return {
            "conversation_id": conversation_id,
            "discarded_message_ids": message_ids,
            "deleted_conversation": remaining_count == 0,
            "reset_memory": bool(had_completed_assistant),
        }

    async def _get_or_create_conversation(
        self, db: AsyncSession, conversation_id: str | None, question: str
    ) -> Conversation:
        if conversation_id:
            conversation = await db.scalar(
                select(Conversation).where(Conversation.id == conversation_id, Conversation.deleted_at.is_(None))
            )
            if conversation:
                return conversation
        title = auto_title_from_question(question)
        conversation = Conversation(title=title)
        db.add(conversation)
        await db.commit()
        await db.refresh(conversation)
        return conversation

    async def _auto_title_conversation_if_needed(
        self, db: AsyncSession, conversation: Conversation, question: str
    ) -> None:
        if not should_auto_title_conversation(conversation.title, conversation.message_count):
            return
        title = auto_title_from_question(question)
        if title == DEFAULT_CONVERSATION_TITLE:
            return
        now = datetime.now(timezone.utc)
        conversation.title = title
        conversation.updated_at = now
        await db.execute(
            update(Conversation)
            .where(Conversation.id == conversation.id)
            .values(title=title, updated_at=now)
        )
        await db.commit()

    async def _load_recent_history(
        self, db: AsyncSession, conversation_id: str, limit: int = RECENT_HISTORY_MESSAGE_LIMIT
    ) -> list[dict]:
        rows = await db.execute(
            select(ConversationMessage)
            .where(ConversationMessage.conversation_id == conversation_id)
            .order_by(ConversationMessage.created_at.desc())
            .limit(limit)
        )
        messages = list(rows.scalars())
        history: list[dict] = []
        for item in reversed(messages):
            content = (item.content or "").strip()
            if not content or item.role not in {"user", "assistant"}:
                continue
            history.append({"role": item.role, "content": self._clip(content, HISTORY_ITEM_CHAR_LIMIT)})
        return history

    async def _load_summary_seed(
        self, db: AsyncSession, conversation_id: str, limit: int = SUMMARY_SEED_MESSAGE_LIMIT
    ) -> list[dict]:
        rows = await db.execute(
            select(ConversationMessage)
            .where(ConversationMessage.conversation_id == conversation_id)
            .order_by(ConversationMessage.created_at.desc())
            .limit(limit)
        )
        messages = list(rows.scalars())
        seed: list[dict] = []
        for item in reversed(messages):
            content = (item.content or "").strip()
            if not content or item.role not in {"user", "assistant"}:
                continue
            seed.append({"role": item.role, "content": self._clip(content, HISTORY_ITEM_CHAR_LIMIT)})
        return seed

    def _normalize_context_state(self, state: object) -> dict:
        if not isinstance(state, dict):
            return {"active_task": {}, "pending_action": {}, "last_resolution": {}}
        return {
            "active_task": state.get("active_task") if isinstance(state.get("active_task"), dict) else {},
            "pending_action": state.get("pending_action") if isinstance(state.get("pending_action"), dict) else {},
            "last_resolution": state.get("last_resolution") if isinstance(state.get("last_resolution"), dict) else {},
        }

    def _is_smalltalk_greeting(self, question: str) -> bool:
        compact = re.sub(r"[\s!！?？。,.，～~、]+", "", (question or "").strip().lower())
        if not compact or len(compact) > 12:
            return False
        greetings = {
            "你好",
            "您好",
            "你好吗",
            "您好呀",
            "你好呀",
            "早",
            "早上好",
            "上午好",
            "中午好",
            "下午好",
            "晚上好",
            "嗨",
            "哈喽",
            "hello",
            "hi",
            "hey",
        }
        return compact in greetings

    def _smalltalk_context_resolution(self, question: str) -> dict:
        clean_question = question.strip()
        return {
            "intent": "smalltalk",
            "resolved_query": clean_question,
            "uses_history": False,
            "uses_context_state": False,
            "clear_pending": True,
            "reason": "smalltalk greeting bypasses retrieval",
        }

    def _empty_retrieval_trace(
        self,
        question: str,
        resolved_query: str,
        retrieval_query: str,
        retrieval_reinforced: bool,
        retrieval_constraints: dict,
        history: list[dict],
        conversation_summary: str,
        context_resolution: dict,
        context_state: dict,
    ) -> dict:
        return {
            "raw_query": retrieval_query,
            "rewritten_query": resolved_query,
            "original_query": question,
            "resolved_query": resolved_query,
            "retrieval_query": retrieval_query,
            "retrieval_query_reinforced": retrieval_reinforced,
            "recall_results": [],
            "rerank_results": [],
            "final_context": [],
            "answer_context": [],
            "citations": [],
            "retrieval_options": {
                "smalltalk_bypass": True,
                "context_constraints": retrieval_constraints,
            },
            "direct_qa_hit": False,
            "context_constraints": retrieval_constraints,
            "history_count": len(history),
            "conversation_summary": conversation_summary,
            "context_resolution": context_resolution,
            "context_state": context_state,
        }

    async def _resolve_context(
        self,
        question: str,
        history: list[dict],
        conversation_summary: str,
        context_state: dict,
        enable_rewrite: bool = True,
    ) -> dict:
        clean_question = question.strip()
        if not clean_question:
            return {
                "intent": "empty",
                "resolved_query": "",
                "uses_history": False,
                "uses_context_state": False,
                "clear_pending": False,
                "reason": "empty question",
            }

        active_task = context_state.get("active_task") or {}
        pending_action = context_state.get("pending_action") or {}

        if pending_action and self._is_pending_rejection(clean_question):
            return {
                "intent": "cancel_pending",
                "resolved_query": clean_question,
                "uses_history": False,
                "uses_context_state": True,
                "clear_pending": True,
                "reason": "user rejected pending action",
            }

        if pending_action and self._is_pending_confirmation(clean_question):
            resume_query = self._resume_query_from_state(active_task, pending_action, clean_question)
            return {
                "intent": "confirm_pending",
                "resolved_query": resume_query,
                "uses_history": True,
                "uses_context_state": True,
                "clear_pending": True,
                "reason": "user confirmed pending action",
            }

        if self._has_new_topic_signal(clean_question) and not self._looks_like_followup(clean_question):
            return {
                "intent": "new_topic",
                "resolved_query": clean_question,
                "uses_history": False,
                "uses_context_state": False,
                "clear_pending": bool(pending_action),
                "reason": "question has explicit new topic signal",
            }

        if active_task and self._is_short_context_reply(clean_question):
            resume_query = self._resume_query_from_state(active_task, pending_action, clean_question)
            return {
                "intent": "continue_active_task",
                "resolved_query": resume_query,
                "uses_history": True,
                "uses_context_state": True,
                "clear_pending": bool(pending_action),
                "reason": "short reply continues active task",
            }

        has_memory = bool(history or conversation_summary or active_task or pending_action)
        should_resolve = bool(enable_rewrite and has_memory and self._is_context_dependent(clean_question))
        if should_resolve:
            llm_resolution = await self._resolve_context_with_llm(
                clean_question,
                history,
                conversation_summary,
                context_state,
            )
            if llm_resolution:
                return llm_resolution

            resolved_query = await self._build_retrieval_query_with_memory(
                clean_question,
                history,
                conversation_summary,
                context_state,
            )
            return {
                "intent": "followup",
                "resolved_query": resolved_query,
                "uses_history": resolved_query != clean_question,
                "uses_context_state": bool(active_task or pending_action),
                "clear_pending": bool(pending_action),
                "reason": "fallback memory rewrite",
            }

        return {
            "intent": "new_topic",
            "resolved_query": clean_question,
            "uses_history": False,
            "uses_context_state": False,
            "clear_pending": bool(pending_action),
            "reason": "standalone question",
        }

    async def _resolve_context_with_llm(
        self,
        question: str,
        history: list[dict],
        conversation_summary: str,
        context_state: dict,
    ) -> dict | None:
        memory_text = self._format_memory(conversation_summary, history[-RECENT_HISTORY_MESSAGE_LIMIT:], 500)
        state_text = self._format_context_state(context_state)
        if not (memory_text or state_text):
            return None
        messages = [
            {
                "role": "system",
                "content": (
                    "你是对话上下文解析器。判断当前用户输入是新问题、追问、确认上一轮 pending action、修改任务还是取消任务。"
                    "只输出 JSON，不要输出解释。字段：intent、resolved_query、uses_history、uses_context_state、clear_pending、reason。"
                    "如果是确认上一轮 pending action，resolved_query 必须使用 pending_action.resume_query 或 active_task.resume_query。"
                    "如果是新主题，resolved_query 直接使用当前用户输入。"
                ),
            },
            {
                "role": "user",
                "content": (
                    f"当前上下文状态：\n{state_text or '无'}\n\n"
                    f"会话记忆：\n{memory_text or '无'}\n\n"
                    f"当前用户输入：{question}\n\n"
                    "请输出 JSON。"
                ),
            },
        ]
        try:
            raw = (await self.model_service.complete_text(messages)).strip()
            start = raw.find("{")
            end = raw.rfind("}")
            if start >= 0 and end > start:
                raw = raw[start : end + 1]
            parsed = json.loads(raw)
        except Exception:
            return None
        if not isinstance(parsed, dict):
            return None

        intent = str(parsed.get("intent") or "followup").strip() or "followup"
        resolved_query = str(parsed.get("resolved_query") or question).strip()
        if len(resolved_query) < 2:
            return None
        return {
            "intent": intent,
            "resolved_query": resolved_query,
            "uses_history": bool(parsed.get("uses_history")),
            "uses_context_state": bool(parsed.get("uses_context_state")),
            "clear_pending": bool(parsed.get("clear_pending")),
            "reason": str(parsed.get("reason") or "llm context resolution")[:200],
        }

    def _format_context_state(self, context_state: dict) -> str:
        active_task = context_state.get("active_task") or {}
        pending_action = context_state.get("pending_action") or {}
        parts = []
        if active_task:
            parts.append(
                "active_task:\n"
                f"- topic: {active_task.get('topic') or '未设置'}\n"
                f"- user_goal: {active_task.get('user_goal') or '未设置'}\n"
                f"- target_documents: {', '.join(active_task.get('target_documents') or []) or '无'}\n"
                f"- resume_query: {active_task.get('resume_query') or '未设置'}"
            )
        if pending_action:
            parts.append(
                "pending_action:\n"
                f"- type: {pending_action.get('type') or '未设置'}\n"
                f"- assistant_question: {pending_action.get('assistant_question') or '未设置'}\n"
                f"- resume_query: {pending_action.get('resume_query') or '未设置'}"
            )
        return "\n\n".join(parts)

    def _resume_query_from_state(self, active_task: dict, pending_action: dict, question: str) -> str:
        for source in (pending_action, active_task):
            for key in ("resume_query", "user_goal", "topic"):
                value = str(source.get(key) or "").strip()
                if value:
                    return value
        return question.strip()

    def _build_contextual_retrieval_query(
        self,
        question: str,
        resolved_query: str,
        context_state: dict,
        context_resolution: dict,
    ) -> str:
        resolved = (resolved_query or question).strip()
        if not self._should_reinforce_context_topic(question, context_state, context_resolution):
            return resolved

        active_task = context_state.get("active_task") or {}
        target_documents = active_task.get("target_documents") if isinstance(active_task.get("target_documents"), list) else []
        context_items = [
            ("上下文主题", active_task.get("topic")),
            ("目标文档", "、".join(str(item).strip() for item in target_documents if str(item).strip())),
            ("历史任务", active_task.get("user_goal")),
            ("任务续接", active_task.get("resume_query")),
        ]
        lines: list[str] = []
        seen: set[str] = set()
        for label, value in context_items:
            text = self._clip(str(value or "").strip(), 220)
            if not text:
                continue
            normalized = "".join(text.split())
            if normalized in seen:
                continue
            seen.add(normalized)
            lines.append(f"{label}：{text}")

        clean_question = question.strip()
        if clean_question and "".join(clean_question.split()) not in seen:
            lines.append(f"当前追问：{self._clip(clean_question, 220)}")
        if resolved and "".join(resolved.split()) not in seen:
            lines.append(f"完整检索意图：{self._clip(resolved, 320)}")

        if not lines:
            return resolved
        return self._clip("\n".join(lines), 1200)

    def _build_retrieval_constraints(
        self,
        question: str,
        resolved_query: str,
        retrieval_query: str,
        context_state: dict,
        context_resolution: dict,
    ) -> dict:
        active_task = context_state.get("active_task") or {}
        intent = str(context_resolution.get("intent") or "").strip()
        is_followup = self._should_reinforce_context_topic(question, context_state, context_resolution)
        target_documents = active_task.get("target_documents") if isinstance(active_task.get("target_documents"), list) else []
        target_documents = [
            self._clip(str(item).strip(), 220)
            for item in target_documents
            if str(item or "").strip()
        ][:5]
        active_topic = self._clip(str(active_task.get("topic") or "").strip(), 220)
        user_goal = self._clip(str(active_task.get("user_goal") or "").strip(), 320)
        resume_query = self._clip(str(active_task.get("resume_query") or "").strip(), 320)
        constraint_terms = []
        for value in (active_topic, user_goal, resume_query, *target_documents):
            normalized = "".join(str(value or "").split())
            if normalized and normalized not in constraint_terms:
                constraint_terms.append(normalized)
        strength = "none"
        if is_followup and (active_topic or user_goal or target_documents):
            strength = "strict" if intent in {"followup", "continue_active_task", "confirm_pending", "modify_task"} else "soft"
        return {
            "original_query": question.strip(),
            "resolved_query": (resolved_query or question).strip(),
            "retrieval_query": (retrieval_query or resolved_query or question).strip(),
            "intent": intent or "unknown",
            "is_followup": is_followup,
            "uses_history": bool(context_resolution.get("uses_history")),
            "uses_context_state": bool(context_resolution.get("uses_context_state")),
            "active_topic": active_topic or None,
            "user_goal": user_goal or None,
            "resume_query": resume_query or None,
            "target_documents": target_documents,
            "constraint_terms": constraint_terms,
            "constraint_strength": strength,
        }

    def _should_reinforce_context_topic(
        self,
        question: str,
        context_state: dict,
        context_resolution: dict,
    ) -> bool:
        active_task = context_state.get("active_task") or {}
        if not active_task:
            return False
        intent = str(context_resolution.get("intent") or "").strip()
        if intent in {"empty", "new_topic", "cancel_pending"}:
            return False
        if context_resolution.get("uses_context_state") or context_resolution.get("uses_history"):
            return True
        if intent in {"followup", "continue_active_task", "confirm_pending", "modify_task"}:
            return True
        return self._is_context_dependent(question)

    def _is_pending_confirmation(self, question: str) -> bool:
        compact = "".join(question.split())
        if not compact or len(compact) > 16:
            return False
        if self._is_pending_rejection(compact):
            return False
        if any(marker in compact for marker in ("什么", "哪些", "怎么", "如何", "为何", "为什么", "吗", "？", "?")):
            return False
        return any(
            marker in compact
            for marker in (
                "确认",
                "可以",
                "好的",
                "好",
                "继续",
                "按这个",
                "就这样",
                "是的",
                "对",
                "嗯",
                "行",
                "帮我整理",
                "生成吧",
            )
        )

    def _is_pending_rejection(self, question: str) -> bool:
        compact = "".join(question.split())
        return any(marker in compact for marker in ("取消", "不用", "不要", "先不", "不是", "不需要", "换一个"))

    def _is_short_context_reply(self, question: str) -> bool:
        compact = "".join(question.split())
        if len(compact) > 18:
            return False
        if self._has_new_topic_signal(compact):
            return False
        return any(marker in compact for marker in ("继续", "接着", "按这个", "整理", "生成", "展开", "详细点", "补充"))

    def _has_new_topic_signal(self, question: str) -> bool:
        compact = "".join(question.split())
        context_prefixes = ("这个", "那个", "上述", "上面", "其中", "对应", "继续", "接着", "按")
        if compact.startswith(context_prefixes):
            return False
        markers = ("什么", "哪些", "怎么", "如何", "为何", "为什么", "是否", "吗", "？", "?", "准备", "流程", "申请", "办理")
        return len(compact) > 10 and any(marker in compact for marker in markers)

    def _is_context_dependent(self, question: str) -> bool:
        return (
            self._looks_like_followup(question)
            or self._is_short_context_reply(question)
        )

    async def _build_retrieval_query_with_memory(
        self, question: str, history: list[dict], conversation_summary: str, context_state: dict | None = None
    ) -> str:
        clean_question = question.strip()
        active_text = self._format_context_state(context_state or {})
        if not (history or conversation_summary or active_text) or not self._is_context_dependent(clean_question):
            return clean_question

        memory_text = self._format_memory(conversation_summary, history[-RECENT_HISTORY_MESSAGE_LIMIT:], 500)
        if active_text:
            memory_text = f"{active_text}\n\n{memory_text}" if memory_text else active_text
        if not memory_text:
            return clean_question

        messages = [
            {
                "role": "system",
                "content": (
                    "你是检索查询改写助手。根据会话摘要和最近对话，把当前追问改写成独立、完整的检索查询。"
                    "只输出改写后的查询文本，不要解释。"
                ),
            },
            {
                "role": "user",
                "content": (
                    f"会话记忆：\n{memory_text}\n\n"
                    f"当前追问：{clean_question}\n\n"
                    "改写要求：补全指代对象，保留关键实体、金额、日期、合同主体和业务术语。"
                ),
            },
        ]
        try:
            rewritten = await self.model_service.complete_text(messages)
            rewritten = rewritten.strip().strip('"').strip("'").strip('"')
            if rewritten and len(rewritten) >= 4:
                return rewritten
        except Exception:
            pass

        recent_user_questions = [
            item["content"]
            for item in history
            if item.get("role") == "user" and item.get("content")
        ][-3:]
        if conversation_summary:
            return f"会话摘要：{self._clip(conversation_summary, 500)}\n当前问题：{clean_question}"
        if recent_user_questions:
            context = "\n".join(f"上文问题：{self._clip(item, 220)}" for item in recent_user_questions)
            return f"{context}\n当前问题：{clean_question}"
        return clean_question

    def _build_messages_with_memory(
        self,
        question: str,
        contexts: list[dict],
        history: list[dict],
        conversation_summary: str,
        context_state: dict | None = None,
        context_resolution: dict | None = None,
    ) -> list[dict]:
        context_text = "\n\n".join(
            [
                (
                    f"[来源{i + 1}] 文档：{item.get('document_title') or '未知文档'}；"
                    f"页码：{item.get('page_start') or '未知'}；"
                    f"章节：{item.get('section_path') or '无'}；"
                    f"URL：{item.get('url') or '无'}\n"
                    f"{item.get('content') or ''}"
                )
                for i, item in enumerate(contexts)
            ]
        )
        system = (
            "你是学校 RAG 智能问答助手。回答要自然、友好、有解释感，像在帮用户读懂资料或合同条款，"
            "不要像日志或检索系统输出。回答时按以下优先级选择依据："
            "1. 如果用户询问本次会话、上一轮、之前的问题或历史回答，"
            "可以直接依据会话摘要和最近对话原文回答。"
            "2. 如果会话历史中已有明确答案，也可以引用历史回答，但要说明这是基于本次会话历史。"
            "3. 如果会话历史不足以回答当前资料类问题，必须依据检索资料回答。"
            "4. 如果检索资料也没有明确依据，必须说明资料中未找到明确依据，不得编造。"
            "正文先给明确结论，再用一两句话解释原因。"
            "回答必须使用 Markdown 结构化排版：复杂回答用二级标题（##）划分模块，模块内用有序或无序列表；"
            "关键结论、时间、金额、条件等只用少量加粗突出。不要把整段正文都加粗。"
            "不同模块之间保留空行，避免条目和正文粘连。"
            "流程步骤编号规则：同一流程的主步骤必须使用连续阿拉伯数字有序列表（例如 1. 2. 3. 或 1、2、3、）递增，"
            "不要把多个主步骤都写成 1；如果是多组独立流程，应先用小标题分组，每组再从 1 开始。"
            "子步骤使用无序列表或 1.1、1.2 这类层级编号。"
            "引用法规条文、原文序号、年份、金额、页码时必须保留原样，不要把它们改写成流程步骤编号。"
            "不要在正文里写“根据检索资料”“来源1”“第几页”这类引用标记，前端会单独展示参考来源。"
            "除非用户追问出处，否则不要主动展开来源位置。"
        )
        system += (
            "如果用户询问参赛要求、规则、条件、流程、报名办法等内容，必须检查同一活动标题后面连续的编号列表；"
            "只要上下文中出现这些编号条目，就要完整提取，不要回答“未明确列出”。"
        )
        system += (
            "如果用户询问政策、制度、办理流程、申请条件、所需材料、资格限制等内容，必须按政策办理类问题处理："
            "优先覆盖适用对象/办理条件、所需材料、办理流程、不得办理或限制情形、特殊情形、后续公示备案或归档要求、"
            "跨部门或跨地区事项、时间要求和注意事项。"
            "检索资料中出现“不得、不予、不能、特殊情形、公示、备案、跨省、户口迁移、公安机关”等政策限制或后续要求时，"
            "必须明确列出；如果某一维度资料没有明确依据，要写明资料中未找到明确依据，不得补编。"
        )
        messages = [{"role": "system", "content": system}]
        context_packet = self._format_answer_context_packet(context_state or {}, context_resolution or {})
        if context_packet:
            messages.append(
                {
                    "role": "system",
                    "content": context_packet,
                }
            )
        if conversation_summary:
            messages.append(
                {
                    "role": "system",
                    "content": f"会话摘要，可用于理解和回答历史相关问题：\n{self._clip(conversation_summary, SUMMARY_MAX_CHARS)}",
                }
            )
        for item in history[-RECENT_HISTORY_MESSAGE_LIMIT:]:
            messages.append({"role": item["role"], "content": self._clip(item["content"], HISTORY_ITEM_CHAR_LIMIT)})
        user = f"检索资料：\n{context_text or '无可用资料'}\n\n当前用户问题：{question}"
        messages.append({"role": "user", "content": user})
        return messages

    def _format_answer_context_packet(self, context_state: dict, context_resolution: dict) -> str:
        state_text = self._format_context_state(context_state)
        resolution_text = ""
        if context_resolution:
            resolution_text = (
                f"本轮上下文解析：intent={context_resolution.get('intent') or 'unknown'}；"
                f"resolved_query={context_resolution.get('resolved_query') or ''}；"
                f"reason={context_resolution.get('reason') or ''}"
            )
        if not (state_text or resolution_text):
            return ""
        return (
            "以下是服务端整理的对话上下文包。回答时优先遵守 resolved_query 所表达的完整任务；"
            "如果当前用户只是确认、继续或承接上一轮，不要把短句当成独立问题。\n\n"
            f"{state_text}\n\n{resolution_text}"
        ).strip()

    def _refresh_context_state(
        self,
        previous_state: dict,
        question: str,
        resolved_query: str,
        answer: str,
        contexts: list[dict],
        context_resolution: dict,
    ) -> dict:
        now = datetime.now(timezone.utc).isoformat()
        previous_state = self._normalize_context_state(previous_state)
        clear_pending = bool(context_resolution.get("clear_pending"))
        intent = str(context_resolution.get("intent") or "")

        target_documents = self._context_document_titles(contexts)
        active_task = dict(previous_state.get("active_task") or {})
        if resolved_query.strip() and intent not in {"empty", "cancel_pending"}:
            active_task = {
                "topic": self._infer_task_topic(resolved_query, target_documents),
                "user_goal": resolved_query.strip(),
                "target_documents": target_documents,
                "resume_query": resolved_query.strip(),
                "updated_at": now,
            }

        pending_action: dict = {}
        if self._answer_requests_confirmation(answer):
            pending_action = {
                "type": "confirm_continue",
                "assistant_question": self._clip(answer.strip(), 500),
                "resume_query": (resolved_query or question).strip(),
                "created_at": now,
            }
        elif not clear_pending and intent not in {"new_topic", "cancel_pending"}:
            pending_action = previous_state.get("pending_action") or {}

        return {
            "active_task": active_task,
            "pending_action": pending_action,
            "last_resolution": {
                "raw_query": question,
                "resolved_query": resolved_query,
                "intent": intent or "unknown",
                "reason": context_resolution.get("reason") or "",
                "updated_at": now,
            },
        }

    def _context_document_titles(self, contexts: list[dict]) -> list[str]:
        titles: list[str] = []
        for item in contexts:
            title = str(item.get("document_title") or item.get("document_name") or "").strip()
            if title and title not in titles:
                titles.append(title)
            if len(titles) >= 5:
                break
        return titles

    def _infer_task_topic(self, resolved_query: str, target_documents: list[str]) -> str:
        if target_documents:
            return target_documents[0]
        return self._clip(resolved_query.strip(), 80)

    def _answer_requests_confirmation(self, answer: str) -> bool:
        compact = "".join(answer.split())
        if not compact:
            return False
        return any(
            marker in compact
            for marker in (
                "是否需要",
                "要不要",
                "需要我继续",
                "我可以继续",
                "可以继续",
                "确认后",
                "请确认",
                "是否继续",
                "是否按",
            )
        )

    async def _refresh_conversation_summary(
        self,
        previous_summary: str,
        summary_seed: list[dict],
        question: str,
        answer: str,
    ) -> str:
        if not (question.strip() or answer.strip()):
            return previous_summary
        if not self.settings.chat_summary_model_enabled:
            return self._fallback_summary(previous_summary, summary_seed, question, answer)

        seed_text = ""
        if not previous_summary and summary_seed:
            seed_text = self._format_history_items(summary_seed, per_item_limit=700)

        messages = [
            {
                "role": "system",
                "content": (
                    "你是会话摘要助手。维护一份可长期使用的会话摘要。"
                    "摘要要保留用户已经问过的问题、助手给出的关键结论、明确的合同/资料对象、用户偏好和未解决事项。"
                    "不要编造，不要加入无依据内容，控制在 1200 字以内。"
                ),
            },
            {
                "role": "user",
                "content": (
                    f"已有摘要：\n{previous_summary or '无'}\n\n"
                    f"已有历史原文种子：\n{seed_text or '无'}\n\n"
                    f"新增一轮：\n用户：{self._clip(question, 1000)}\n助手：{self._clip(answer, 1400)}\n\n"
                    "请输出更新后的会话摘要。"
                ),
            },
        ]
        try:
            summary = (await self.model_service.complete_text(messages)).strip()
            if summary:
                return self._clip(summary, SUMMARY_MAX_CHARS)
        except Exception:
            pass
        return self._fallback_summary(previous_summary, summary_seed, question, answer)

    def _fallback_summary(
        self, previous_summary: str, summary_seed: list[dict], question: str, answer: str
    ) -> str:
        parts = []
        if previous_summary:
            parts.append(previous_summary)
        elif summary_seed:
            parts.append(self._format_history_items(summary_seed, per_item_limit=360))
        parts.append(
            "最近一轮："
            f"用户问：{self._clip(question, 360)}；"
            f"助手答：{self._clip(answer, 520)}"
        )
        return self._clip("\n".join(part for part in parts if part), SUMMARY_MAX_CHARS)

    def _format_memory(self, conversation_summary: str, history: list[dict], per_item_limit: int = 500) -> str:
        parts = []
        if conversation_summary:
            parts.append(f"会话摘要：\n{self._clip(conversation_summary, SUMMARY_MAX_CHARS)}")
        if history:
            parts.append(f"最近 {self._history_round_count(history)} 轮原文：\n{self._format_history_items(history, per_item_limit)}")
        return "\n\n".join(parts)

    def _format_history_items(self, history: list[dict], per_item_limit: int = 500) -> str:
        labels = {"user": "用户", "assistant": "助手"}
        lines = []
        for item in history:
            role = labels.get(item.get("role", ""), item.get("role", "消息"))
            content = self._clip(str(item.get("content") or ""), per_item_limit)
            if content:
                lines.append(f"{role}：{content}")
        return "\n".join(lines)

    def _history_round_count(self, history: list[dict]) -> int:
        return min(RECENT_HISTORY_ROUNDS, sum(1 for item in history if item.get("role") == "user"))

    async def _build_retrieval_query(self, question: str, history: list[dict]) -> str:
        clean_question = question.strip()
        if not history or not self._looks_like_followup(clean_question):
            return clean_question
        recent_history = [
            item for item in history[-4:]
            if item.get("role") in {"user", "assistant"} and item.get("content")
        ]
        if not recent_history:
            return clean_question
        # 用 LLM 将追问改写成独立检索问题
        try:
            history_text = "\n".join(
                f"{'用户' if item['role'] == 'user' else '助手'}：{self._clip(item['content'], 500)}"
                for item in recent_history
            )
            prompt = (
                "你是一个检索查询改写助手。\n"
                "根据对话历史和当前追问，生成一个独立、完整的检索查询，"
                "用于在知识库中搜索相关资料。\n"
                "要求：\n"
                "1. 补全指代（如\"它\"\"该\"\"这些\"等，替换为具体对象）\n"
                "2. 保留关键专业术语和专有名词\n"
                "3. 直接输出改写后的查询，不要解释\n\n"
                f"对话历史：\n{history_text}\n\n"
                f"当前追问：{clean_question}\n\n"
                "改写后的查询："
            )
            rewritten = await self.model_service.complete_text([
                {"role": "system", "content": "你是检索查询改写专家，只输出改写后的查询文本。"},
                {"role": "user", "content": prompt},
            ])
            rewritten = rewritten.strip().strip('"').strip("'").strip('"')
            if rewritten and len(rewritten) >= 4:
                return rewritten
        except Exception:
            pass
        # LLM 改写失败时回退到拼接方案
        recent_user_questions = [
            item["content"]
            for item in history
            if item.get("role") == "user" and item.get("content")
        ][-2:]
        if not recent_user_questions:
            return clean_question
        context = "\n".join(f"上文问题：{self._clip(item, 220)}" for item in recent_user_questions)
        return f"{context}\n当前问题：{clean_question}"

    def _looks_like_followup(self, question: str) -> bool:
        compact = "".join(question.split())
        explicit_followup_markers = (
            "这个",
            "那个",
            "它",
            "该",
            "上述",
            "上面",
            "刚才",
            "继续",
            "其中",
            "分别",
            "呢",
            "这些",
        )
        if any(marker in compact for marker in explicit_followup_markers):
            return True

        underspecified_markers = (
            "合同",
            "金额",
            "付款",
            "甲方",
            "乙方",
            "违约",
            "质保",
        )
        if not any(marker in compact for marker in underspecified_markers):
            return False

        # Only short, underspecified questions should borrow history. A question
        # with a concrete topic such as "差旅网上审批流程" must search as-is.
        topic_markers = (
            "流程",
            "操作",
            "审批",
            "报名",
            "缴费",
            "申请",
            "通知",
            "办法",
            "规定",
            "制度",
            "项目",
            "系统",
            "活动",
            "比赛",
            "测试",
            "讲座",
            "课程",
            "学分",
            "学位",
            "专业",
            "学院",
            "学校",
            "南昌航空大学",
        )
        if any(marker in compact for marker in topic_markers):
            return False

        return len(compact) <= 18

    def _build_messages(self, question: str, contexts: list[dict], history: list[dict]) -> list[dict]:
        context_text = "\n\n".join(
            [
                (
                    f"[来源{i + 1}] 文档：{item.get('document_title') or '未知文档'}；"
                    f"页码：{item.get('page_start') or '未知'}；"
                    f"章节：{item.get('section_path') or '无'}；"
                    f"URL：{item.get('url') or '无'}\n"
                    f"{item.get('content') or ''}"
                )
                for i, item in enumerate(contexts)
            ]
        )
        system = (
            "你是学校 RAG 智能问答助手。必须严格基于给定资料回答，不能编造。"
            "如果资料中没有明确依据，请直接说明资料中未找到明确依据。"
            "如果资料中存在金额、日期、主体、条款等信息，优先给出明确结论，"
            "并说明依据来自哪份资料、页码或章节。"
            "历史对话只能用于理解当前追问，不得替代资料依据。"
            "回答要清晰、简洁，并与资料保持一致。"
            "回答必须使用 Markdown 结构化排版：复杂回答用二级标题（##）划分模块，模块内用有序或无序列表；"
            "关键结论、时间、金额、条件等只用少量加粗突出。不要把整段正文都加粗。"
            "不同模块之间保留空行，避免条目和正文粘连。"
            "流程步骤编号规则：同一流程的主步骤必须使用连续阿拉伯数字有序列表（例如 1. 2. 3. 或 1、2、3、）递增，"
            "不要把多个主步骤都写成 1；如果是多组独立流程，应先用小标题分组，每组再从 1 开始。"
            "子步骤使用无序列表或 1.1、1.2 这类层级编号。"
            "引用法规条文、原文序号、年份、金额、页码时必须保留原样，不要把它们改写成流程步骤编号。"
        )
        system += (
            "如果用户询问参赛要求、规则、条件、流程、报名办法等内容，必须检查同一活动标题后面连续的编号列表；"
            "只要上下文中出现这些编号条目，就要完整提取，不要回答“未明确列出”。"
        )
        messages = [{"role": "system", "content": system}]
        for item in history[-8:]:
            messages.append({"role": item["role"], "content": self._clip(item["content"], 1800)})
        user = f"资料：\n{context_text or '无可用资料'}\n\n当前用户问题：{question}"
        messages.append({"role": "user", "content": user})
        return messages

    def _fallback_answer(self, contexts: list[dict]) -> str:
        if not contexts:
            return "资料中未找到明确依据，暂时无法回答这个问题。"
        first = contexts[0]
        return (
            f"根据已检索到的资料，相关内容主要来自《{first.get('document_title') or '未知文档'}》。"
            "请查看下方参考来源确认原文。"
        )

    def _sanitize_answer(self, text: str) -> str:
        if not text:
            return ""
        sanitized = re.sub(
            r"[\U0001F000-\U0001FAFF\U00002700-\U000027BF\U00002600-\U000026FF]",
            "",
            text,
        )
        sanitized = sanitized.replace("\ufeff", "").replace("\u200b", "")
        sanitized = re.sub(r"[ \t]+\n", "\n", sanitized)
        sanitized = re.sub(r"\n{4,}", "\n\n\n", sanitized)
        return sanitized.strip()

    def _clip(self, text: str, limit: int) -> str:
        if len(text) <= limit:
            return text
        return text[:limit].rstrip() + "..."

    async def _suggest_questions(
        self, question: str, answer: str, contexts: list[dict]
    ) -> list[dict]:
        if not contexts:
            return []
        defaults = [
            {"question": "这个问题对应的原文条款是什么？"},
            {"question": "这份资料里是否还有相关限制条件？"},
            {"question": "如果需要办理或执行，下一步需要准备什么？"},
        ]
        if not self.settings.chat_suggested_questions_model_enabled:
            return defaults[: min(3, len(contexts))]
        context_titles = "、".join(
            sorted({str(item.get("document_title")) for item in contexts if item.get("document_title")})
        )
        messages = [
            {
                "role": "system",
                "content": (
                    "基于当前问答和资料，生成最多 3 个用户可能继续追问的问题。"
                    "只输出 JSON 数组，字段为 question。"
                ),
            },
            {
                "role": "user",
                "content": f"用户问题：{question}\n回答：{answer}\n资料文档：{context_titles}",
            },
        ]
        try:
            raw = await self.model_service.complete_text(messages)
            parsed = json.loads(raw)
            if isinstance(parsed, list):
                return [{"question": str(item.get("question", ""))} for item in parsed if item.get("question")][:3]
        except Exception:
            pass
        return defaults[: min(3, len(contexts))]

    async def _get_cached_answer(
        self, question: str, retrieval: dict, history: list[dict], conversation_summary: str
    ) -> str | None:
        if not self._answer_cache_allowed(retrieval, history, conversation_summary):
            return None
        try:
            cached = await self.redis_service.get_json(self._answer_cache_key(question, retrieval))
        except Exception:
            return None
        if isinstance(cached, dict) and isinstance(cached.get("answer"), str):
            return cached["answer"]
        if isinstance(cached, str):
            return cached
        return None

    async def _set_cached_answer(
        self, question: str, retrieval: dict, history: list[dict], conversation_summary: str, answer: str
    ) -> None:
        if not self._answer_cache_allowed(retrieval, history, conversation_summary):
            return
        ttl = max(1, self.settings.answer_cache_ttl_seconds)
        try:
            await self.redis_service.set_json(
                self._answer_cache_key(question, retrieval),
                {"answer": answer},
                ttl=ttl,
            )
        except Exception:
            return

    def _answer_cache_allowed(self, retrieval: dict, history: list[dict], conversation_summary: str) -> bool:
        return (
            self.settings.answer_cache_enabled
            and not history
            and not conversation_summary
            and bool(retrieval.get("answer_context") or retrieval.get("final_context"))
        )

    def _answer_cache_key(self, question: str, retrieval: dict) -> str:
        contexts = retrieval.get("answer_context") or retrieval.get("final_context") or []
        context_payload = [
            {
                "chunk_id": item.get("chunk_id"),
                "qa_pair_id": item.get("qa_pair_id"),
                "document_id": item.get("document_id"),
                "document_title": item.get("document_title"),
                "section_path": item.get("section_path"),
                "page_start": item.get("page_start"),
                "page_end": item.get("page_end"),
                "content": item.get("content"),
            }
            for item in contexts
        ]
        payload = {
            "version": 6,
            "chat_model": self.settings.chat_model,
            "question": question,
            "context": context_payload,
            "corpus_version": retrieval.get("corpus_version"),
        }
        digest = hashlib.sha256(
            json.dumps(to_jsonable(payload), ensure_ascii=False, sort_keys=True).encode("utf-8")
        ).hexdigest()
        return f"answer:{digest}"

    def _sse(self, event: str, data: dict) -> str:
        return f"event: {event}\ndata: {json.dumps(to_jsonable(data), ensure_ascii=False)}\n\n"

    async def _stream_delta_text(self, text: str) -> AsyncGenerator[str, None]:
        if not text:
            return
        delay = max(0, self.settings.stream_char_delay_ms) / 1000
        if delay <= 0:
            yield self._sse("delta", {"content": self._sanitize_answer(text)})
            return
        for char in self._sanitize_answer(text):
            yield self._sse("delta", {"content": char})
            await asyncio.sleep(delay)
