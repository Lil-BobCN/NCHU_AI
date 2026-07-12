"""add internal query performance indexes

Revision ID: 0010_internal_performance_indexes
Revises: 0009_document_access_scope
Create Date: 2026-07-12
"""

from alembic import op


revision = "0010_internal_performance_indexes"
down_revision = "0009_document_access_scope"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("CREATE INDEX IF NOT EXISTS idx_documents_knowledge_base ON documents(knowledge_base)")
    op.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_documents_visible_indexed_scope
        ON documents(knowledge_base, publish_scope, publish_dept_id, created_at DESC)
        WHERE deleted_at IS NULL AND visible_in_chat = true AND status = 'indexed'
        """
    )
    op.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_chunks_document_chunk_no_active
        ON document_chunks(document_id, chunk_no)
        WHERE is_active = true
        """
    )
    op.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_chunks_content_trgm
        ON document_chunks USING GIN(content gin_trgm_ops)
        """
    )
    op.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_conversations_active_owner_updated
        ON conversations(created_by, updated_at DESC)
        WHERE deleted_at IS NULL
        """
    )
    op.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_conversations_context_state
        ON conversations USING GIN(context_state)
        """
    )
    op.execute("CREATE INDEX IF NOT EXISTS idx_retrieval_logs_message_id ON retrieval_logs(message_id)")
    op.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_answer_feedbacks_user_message
        ON answer_feedbacks(user_message_id)
        """
    )
    op.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_answer_feedbacks_retrieval_log
        ON answer_feedbacks(retrieval_log_id)
        """
    )


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS idx_answer_feedbacks_retrieval_log")
    op.execute("DROP INDEX IF EXISTS idx_answer_feedbacks_user_message")
    op.execute("DROP INDEX IF EXISTS idx_retrieval_logs_message_id")
    op.execute("DROP INDEX IF EXISTS idx_conversations_context_state")
    op.execute("DROP INDEX IF EXISTS idx_conversations_active_owner_updated")
    op.execute("DROP INDEX IF EXISTS idx_chunks_content_trgm")
    op.execute("DROP INDEX IF EXISTS idx_chunks_document_chunk_no_active")
    op.execute("DROP INDEX IF EXISTS idx_documents_visible_indexed_scope")
    op.execute("DROP INDEX IF EXISTS idx_documents_knowledge_base")
