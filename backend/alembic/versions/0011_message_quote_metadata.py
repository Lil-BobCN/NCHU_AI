"""add quoted message metadata

Revision ID: 0011_message_quote_metadata
Revises: 0010_feedback_cancel_audit
Create Date: 2026-07-07
"""

from alembic import op


revision = "0011_message_quote_metadata"
down_revision = "0010_feedback_cancel_audit"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # 记录用户消息引用的 AI 回复编号；原回复被清理时保留用户消息本身，因此外键使用 SET NULL。
    op.execute(
        """
        ALTER TABLE conversation_messages
        ADD COLUMN IF NOT EXISTS quoted_message_id uuid NULL
        REFERENCES conversation_messages(id) ON DELETE SET NULL
        """
    )
    # 保存引用内容快照，避免历史会话刷新后只能看到用户追加问题，看不到当时引用的上下文。
    op.execute(
        """
        ALTER TABLE conversation_messages
        ADD COLUMN IF NOT EXISTS quoted_message_content text NOT NULL DEFAULT ''
        """
    )


def downgrade() -> None:
    op.execute("ALTER TABLE conversation_messages DROP COLUMN IF EXISTS quoted_message_content")
    op.execute("ALTER TABLE conversation_messages DROP COLUMN IF EXISTS quoted_message_id")
