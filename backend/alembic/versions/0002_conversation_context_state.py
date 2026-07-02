"""add conversation context state

Revision ID: 0002_context_state
Revises: 0001_initial
Create Date: 2026-06-18
"""

from alembic import op


revision = "0002_context_state"
down_revision = "0001_initial"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        """
        ALTER TABLE conversations
        ADD COLUMN IF NOT EXISTS context_state jsonb NOT NULL DEFAULT '{}'::jsonb
        """
    )


def downgrade() -> None:
    op.drop_column("conversations", "context_state")
