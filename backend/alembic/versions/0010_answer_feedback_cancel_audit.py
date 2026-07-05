"""add answer feedback cancel audit metadata

Revision ID: 0010_feedback_cancel_audit
Revises: 0009_message_soft_delete
Create Date: 2026-07-05
"""

from alembic import op


revision = "0010_feedback_cancel_audit"
down_revision = "0009_message_soft_delete"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        """
        ALTER TABLE answer_feedbacks
        ADD COLUMN IF NOT EXISTS canceled_at timestamptz NULL
        """
    )
    op.execute(
        """
        ALTER TABLE answer_feedbacks
        ADD COLUMN IF NOT EXISTS canceled_by uuid NULL
        """
    )


def downgrade() -> None:
    op.execute("ALTER TABLE answer_feedbacks DROP COLUMN IF EXISTS canceled_by")
    op.execute("ALTER TABLE answer_feedbacks DROP COLUMN IF EXISTS canceled_at")
