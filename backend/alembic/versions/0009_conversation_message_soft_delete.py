"""add soft delete metadata to conversation messages

Revision ID: 0009_message_soft_delete
Revises: 0008_document_batch_ops
Create Date: 2026-07-05
"""

from alembic import op


revision = "0009_message_soft_delete"
down_revision = "0008_document_batch_ops"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        """
        ALTER TABLE conversation_messages
        ADD COLUMN IF NOT EXISTS deleted_at timestamptz NULL
        """
    )
    op.execute(
        """
        ALTER TABLE conversation_messages
        ADD COLUMN IF NOT EXISTS deleted_by uuid NULL
        """
    )
    op.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_messages_visible_conversation_id
        ON conversation_messages(conversation_id, created_at)
        WHERE deleted_at IS NULL
        """
    )


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS idx_messages_visible_conversation_id")
    op.execute("ALTER TABLE conversation_messages DROP COLUMN IF EXISTS deleted_by")
    op.execute("ALTER TABLE conversation_messages DROP COLUMN IF EXISTS deleted_at")
