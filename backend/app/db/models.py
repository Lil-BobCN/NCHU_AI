from datetime import datetime
from sqlalchemy import (
    BigInteger,
    Boolean,
    DateTime,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
    func,
)
from sqlalchemy.dialects.postgresql import ARRAY, JSONB, TSVECTOR, UUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class TimestampMixin:
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )


class Admin(Base, TimestampMixin):
    __tablename__ = "admins"

    id: Mapped[str] = mapped_column(UUID(as_uuid=False), primary_key=True, server_default=func.uuid_generate_v4())
    username: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    display_name: Mapped[str] = mapped_column(String(64), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default="true")
    last_login_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class Document(Base, TimestampMixin):
    __tablename__ = "documents"

    id: Mapped[str] = mapped_column(UUID(as_uuid=False), primary_key=True, server_default=func.uuid_generate_v4())
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    file_name: Mapped[str] = mapped_column(String(255), nullable=False)
    file_ext: Mapped[str] = mapped_column(String(32), nullable=False)
    mime_type: Mapped[str | None] = mapped_column(String(128), nullable=True)
    file_size: Mapped[int] = mapped_column(BigInteger, nullable=False)
    file_hash: Mapped[str] = mapped_column(String(128), nullable=False)
    storage_bucket: Mapped[str] = mapped_column(String(128), nullable=False)
    storage_object_key: Mapped[str] = mapped_column(String(512), nullable=False)
    knowledge_base: Mapped[str] = mapped_column(String(64), nullable=False, server_default="default")
    source_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    preview_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    download_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String(32), nullable=False, server_default="uploaded")
    parse_quality_score: Mapped[float | None] = mapped_column(Numeric(5, 2), nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_by: Mapped[str | None] = mapped_column(UUID(as_uuid=False), nullable=True)
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class KnowledgeBaseVersion(Base):
    __tablename__ = "knowledge_base_versions"

    scope: Mapped[str] = mapped_column(String(64), primary_key=True, server_default="default")
    version: Mapped[int] = mapped_column(BigInteger, nullable=False, server_default="1")
    changed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    reason: Mapped[str | None] = mapped_column(String(128), nullable=True)
    document_id: Mapped[str | None] = mapped_column(
        UUID(as_uuid=False), ForeignKey("documents.id", ondelete="SET NULL"), nullable=True
    )


class DocumentJob(Base, TimestampMixin):
    __tablename__ = "document_jobs"

    id: Mapped[str] = mapped_column(UUID(as_uuid=False), primary_key=True, server_default=func.uuid_generate_v4())
    document_id: Mapped[str] = mapped_column(UUID(as_uuid=False), ForeignKey("documents.id", ondelete="CASCADE"), nullable=False)
    job_type: Mapped[str] = mapped_column(String(32), nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False, server_default="pending")
    progress: Mapped[int] = mapped_column(Integer, nullable=False, server_default="0")
    message: Mapped[str | None] = mapped_column(Text, nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    retry_count: Mapped[int] = mapped_column(Integer, nullable=False, server_default="0")
    params: Mapped[dict] = mapped_column(JSONB, nullable=False, server_default="{}")
    result: Mapped[dict] = mapped_column(JSONB, nullable=False, server_default="{}")
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class DocumentParseResult(Base, TimestampMixin):
    __tablename__ = "document_parse_results"

    id: Mapped[str] = mapped_column(UUID(as_uuid=False), primary_key=True, server_default=func.uuid_generate_v4())
    document_id: Mapped[str] = mapped_column(UUID(as_uuid=False), ForeignKey("documents.id", ondelete="CASCADE"), unique=True, nullable=False)
    parser_name: Mapped[str] = mapped_column(String(64), nullable=False)
    parser_version: Mapped[str | None] = mapped_column(String(64), nullable=True)
    content_text: Mapped[str] = mapped_column(Text, nullable=False)
    content_md: Mapped[str | None] = mapped_column(Text, nullable=True)
    content_object_key: Mapped[str | None] = mapped_column(String(512), nullable=True)
    page_count: Mapped[int | None] = mapped_column(Integer, nullable=True)
    quality_score: Mapped[float | None] = mapped_column(Numeric(5, 2), nullable=True)
    parse_meta: Mapped[dict] = mapped_column(JSONB, nullable=False, server_default="{}")


class DocumentChunk(Base, TimestampMixin):
    __tablename__ = "document_chunks"

    id: Mapped[str] = mapped_column(UUID(as_uuid=False), primary_key=True, server_default=func.uuid_generate_v4())
    document_id: Mapped[str] = mapped_column(UUID(as_uuid=False), ForeignKey("documents.id", ondelete="CASCADE"), nullable=False)
    parent_chunk_id: Mapped[str | None] = mapped_column(UUID(as_uuid=False), ForeignKey("document_chunks.id", ondelete="SET NULL"), nullable=True)
    chunk_no: Mapped[int] = mapped_column(Integer, nullable=False)
    chunk_type: Mapped[str] = mapped_column(String(32), nullable=False, server_default="text")
    content: Mapped[str] = mapped_column(Text, nullable=False)
    content_hash: Mapped[str] = mapped_column(String(128), nullable=False)
    token_count: Mapped[int | None] = mapped_column(Integer, nullable=True)
    char_count: Mapped[int] = mapped_column(Integer, nullable=False)
    page_start: Mapped[int | None] = mapped_column(Integer, nullable=True)
    page_end: Mapped[int | None] = mapped_column(Integer, nullable=True)
    section_path: Mapped[str | None] = mapped_column(Text, nullable=True)
    metadata_: Mapped[dict] = mapped_column("metadata", JSONB, nullable=False, server_default="{}")
    search_vector: Mapped[str | None] = mapped_column(TSVECTOR, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default="true")


class QaPair(Base, TimestampMixin):
    __tablename__ = "qa_pairs"

    id: Mapped[str] = mapped_column(UUID(as_uuid=False), primary_key=True, server_default=func.uuid_generate_v4())
    question: Mapped[str] = mapped_column(Text, nullable=False)
    answer: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False, server_default="enabled")
    source_document_id: Mapped[str | None] = mapped_column(UUID(as_uuid=False), ForeignKey("documents.id", ondelete="SET NULL"), nullable=True)
    source_chunk_ids: Mapped[list[str] | None] = mapped_column(ARRAY(UUID(as_uuid=False)), nullable=True)
    source_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    tags: Mapped[list[str] | None] = mapped_column(ARRAY(Text), nullable=True)
    version: Mapped[int] = mapped_column(Integer, nullable=False, server_default="1")
    created_by: Mapped[str | None] = mapped_column(UUID(as_uuid=False), nullable=True)
    updated_by: Mapped[str | None] = mapped_column(UUID(as_uuid=False), nullable=True)
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class QaPairEmbedding(Base):
    __tablename__ = "qa_pair_embeddings"

    id: Mapped[str] = mapped_column(UUID(as_uuid=False), primary_key=True, server_default=func.uuid_generate_v4())
    qa_pair_id: Mapped[str] = mapped_column(UUID(as_uuid=False), ForeignKey("qa_pairs.id", ondelete="CASCADE"), unique=True, nullable=False)
    embedding_model: Mapped[str] = mapped_column(String(128), nullable=False)
    content_hash: Mapped[str] = mapped_column(String(128), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)


class Conversation(Base, TimestampMixin):
    __tablename__ = "conversations"

    id: Mapped[str] = mapped_column(UUID(as_uuid=False), primary_key=True, server_default=func.uuid_generate_v4())
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    created_by: Mapped[str | None] = mapped_column(UUID(as_uuid=False), nullable=True)
    summary: Mapped[str] = mapped_column(Text, nullable=False, server_default="")
    context_state: Mapped[dict] = mapped_column(JSONB, nullable=False, server_default="{}")
    message_count: Mapped[int] = mapped_column(Integer, nullable=False, server_default="0")
    last_message_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class ConversationMessage(Base):
    __tablename__ = "conversation_messages"

    id: Mapped[str] = mapped_column(UUID(as_uuid=False), primary_key=True, server_default=func.uuid_generate_v4())
    conversation_id: Mapped[str] = mapped_column(UUID(as_uuid=False), ForeignKey("conversations.id", ondelete="CASCADE"), nullable=False)
    role: Mapped[str] = mapped_column(String(32), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    rewritten_query: Mapped[str | None] = mapped_column(Text, nullable=True)
    retrieval_trace: Mapped[dict] = mapped_column(JSONB, nullable=False, server_default="{}")
    citations: Mapped[list] = mapped_column(JSONB, nullable=False, server_default="[]")
    suggested_questions: Mapped[list] = mapped_column(JSONB, nullable=False, server_default="[]")
    latency_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)
    model_name: Mapped[str | None] = mapped_column(String(128), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    deleted_by: Mapped[str | None] = mapped_column(UUID(as_uuid=False), nullable=True)


class RetrievalLog(Base):
    __tablename__ = "retrieval_logs"

    id: Mapped[str] = mapped_column(UUID(as_uuid=False), primary_key=True, server_default=func.uuid_generate_v4())
    conversation_id: Mapped[str | None] = mapped_column(UUID(as_uuid=False), ForeignKey("conversations.id", ondelete="SET NULL"), nullable=True)
    message_id: Mapped[str | None] = mapped_column(UUID(as_uuid=False), ForeignKey("conversation_messages.id", ondelete="SET NULL"), nullable=True)
    raw_query: Mapped[str] = mapped_column(Text, nullable=False)
    rewritten_query: Mapped[str | None] = mapped_column(Text, nullable=True)
    recall_results: Mapped[list] = mapped_column(JSONB, nullable=False, server_default="[]")
    rerank_results: Mapped[list] = mapped_column(JSONB, nullable=False, server_default="[]")
    final_context: Mapped[list] = mapped_column(JSONB, nullable=False, server_default="[]")
    citations: Mapped[list] = mapped_column(JSONB, nullable=False, server_default="[]")
    suggested_questions: Mapped[list] = mapped_column(JSONB, nullable=False, server_default="[]")
    answer: Mapped[str | None] = mapped_column(Text, nullable=True)
    answer_quality: Mapped[dict] = mapped_column(JSONB, nullable=False, server_default="{}")
    model_name: Mapped[str | None] = mapped_column(String(128), nullable=True)
    embedding_model: Mapped[str | None] = mapped_column(String(128), nullable=True)
    rerank_model: Mapped[str | None] = mapped_column(String(128), nullable=True)
    latency_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)


class AnswerFeedback(Base, TimestampMixin):
    __tablename__ = "answer_feedbacks"

    id: Mapped[str] = mapped_column(UUID(as_uuid=False), primary_key=True, server_default=func.uuid_generate_v4())
    conversation_id: Mapped[str] = mapped_column(UUID(as_uuid=False), ForeignKey("conversations.id", ondelete="CASCADE"), nullable=False)
    user_message_id: Mapped[str | None] = mapped_column(UUID(as_uuid=False), ForeignKey("conversation_messages.id", ondelete="SET NULL"), nullable=True)
    assistant_message_id: Mapped[str] = mapped_column(UUID(as_uuid=False), ForeignKey("conversation_messages.id", ondelete="CASCADE"), nullable=False)
    retrieval_log_id: Mapped[str | None] = mapped_column(UUID(as_uuid=False), ForeignKey("retrieval_logs.id", ondelete="SET NULL"), nullable=True)
    error_type: Mapped[str] = mapped_column(String(32), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False, server_default="")
    question_snapshot: Mapped[str] = mapped_column(Text, nullable=False, server_default="")
    answer_snapshot: Mapped[str] = mapped_column(Text, nullable=False, server_default="")
    citations_snapshot: Mapped[list] = mapped_column(JSONB, nullable=False, server_default="[]")
    status: Mapped[str] = mapped_column(String(32), nullable=False, server_default="open")
    created_by: Mapped[str | None] = mapped_column(UUID(as_uuid=False), nullable=True)


class EvaluationCase(Base, TimestampMixin):
    __tablename__ = "evaluation_cases"

    id: Mapped[str] = mapped_column(UUID(as_uuid=False), primary_key=True, server_default=func.uuid_generate_v4())
    question: Mapped[str] = mapped_column(Text, nullable=False)
    expected_answer: Mapped[str | None] = mapped_column(Text, nullable=True)
    expected_document_ids: Mapped[list[str] | None] = mapped_column(ARRAY(UUID(as_uuid=False)), nullable=True)
    expected_chunk_ids: Mapped[list[str] | None] = mapped_column(ARRAY(UUID(as_uuid=False)), nullable=True)
    tags: Mapped[list[str] | None] = mapped_column(ARRAY(Text), nullable=True)
    difficulty: Mapped[str | None] = mapped_column(String(32), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default="true")


class EvaluationRun(Base):
    __tablename__ = "evaluation_runs"

    id: Mapped[str] = mapped_column(UUID(as_uuid=False), primary_key=True, server_default=func.uuid_generate_v4())
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    config: Mapped[dict] = mapped_column(JSONB, nullable=False, server_default="{}")
    metrics: Mapped[dict] = mapped_column(JSONB, nullable=False, server_default="{}")
    status: Mapped[str] = mapped_column(String(32), nullable=False, server_default="running")
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)


class EvaluationResult(Base):
    __tablename__ = "evaluation_results"

    id: Mapped[str] = mapped_column(UUID(as_uuid=False), primary_key=True, server_default=func.uuid_generate_v4())
    run_id: Mapped[str] = mapped_column(UUID(as_uuid=False), ForeignKey("evaluation_runs.id", ondelete="CASCADE"), nullable=False)
    case_id: Mapped[str] = mapped_column(UUID(as_uuid=False), ForeignKey("evaluation_cases.id", ondelete="CASCADE"), nullable=False)
    answer: Mapped[str | None] = mapped_column(Text, nullable=True)
    hit_top3: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    hit_top5: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    answer_score: Mapped[float | None] = mapped_column(Numeric(5, 2), nullable=True)
    citation_score: Mapped[float | None] = mapped_column(Numeric(5, 2), nullable=True)
    suggested_question_score: Mapped[float | None] = mapped_column(Numeric(5, 2), nullable=True)
    failure_reason: Mapped[str | None] = mapped_column(String(64), nullable=True)
    trace: Mapped[dict] = mapped_column(JSONB, nullable=False, server_default="{}")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
