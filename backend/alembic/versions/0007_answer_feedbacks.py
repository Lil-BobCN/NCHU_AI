"""add answer feedbacks

Revision ID: 0007_answer_feedbacks
Revises: 0006_quarantine_encoded_docs
Create Date: 2026-06-24
"""

from alembic import op


revision = "0007_answer_feedbacks"
down_revision = "0006_quarantine_encoded_docs"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        """
        CREATE TABLE IF NOT EXISTS answer_feedbacks (
          id uuid PRIMARY KEY DEFAULT uuid_generate_v4(),
          conversation_id uuid NOT NULL REFERENCES conversations(id) ON DELETE CASCADE,
          user_message_id uuid NULL REFERENCES conversation_messages(id) ON DELETE SET NULL,
          assistant_message_id uuid NOT NULL REFERENCES conversation_messages(id) ON DELETE CASCADE,
          retrieval_log_id uuid NULL REFERENCES retrieval_logs(id) ON DELETE SET NULL,
          error_type varchar(32) NOT NULL,
          description text NOT NULL DEFAULT '',
          question_snapshot text NOT NULL DEFAULT '',
          answer_snapshot text NOT NULL DEFAULT '',
          citations_snapshot jsonb NOT NULL DEFAULT '[]',
          status varchar(32) NOT NULL DEFAULT 'open',
          created_by uuid NULL,
          created_at timestamptz NOT NULL DEFAULT now(),
          updated_at timestamptz NOT NULL DEFAULT now()
        )
        """
    )
    op.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_answer_feedbacks_conversation_status
        ON answer_feedbacks(conversation_id, status)
        """
    )
    op.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_answer_feedbacks_assistant_message
        ON answer_feedbacks(assistant_message_id)
        """
    )
    op.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_answer_feedbacks_created_at
        ON answer_feedbacks(created_at DESC)
        """
    )


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS answer_feedbacks CASCADE")
