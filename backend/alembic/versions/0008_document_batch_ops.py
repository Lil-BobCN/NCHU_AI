"""add document batch operation metadata

Revision ID: 0008_document_batch_ops
Revises: 0007_answer_feedbacks
Create Date: 2026-06-26
"""

from alembic import op


revision = "0008_document_batch_ops"
down_revision = "0007_answer_feedbacks"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        """
        ALTER TABLE documents
        ADD COLUMN IF NOT EXISTS knowledge_base varchar(64) NOT NULL DEFAULT 'default'
        """
    )
    op.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_documents_knowledge_base
        ON documents(knowledge_base)
        """
    )


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS idx_documents_knowledge_base")
    op.execute("ALTER TABLE documents DROP COLUMN IF EXISTS knowledge_base")
