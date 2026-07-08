"""add qa tag library

Revision ID: 0012_qa_tag_library
Revises: 0011_message_quote_metadata
Create Date: 2026-07-08
"""

from alembic import op


revision = "0012_qa_tag_library"
down_revision = "0011_message_quote_metadata"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        """
        CREATE TABLE IF NOT EXISTS qa_tags (
          id uuid PRIMARY KEY DEFAULT uuid_generate_v4(),
          name varchar(64) NOT NULL,
          normalized_name varchar(64) NOT NULL UNIQUE,
          status varchar(32) NOT NULL DEFAULT 'enabled',
          created_by uuid NULL,
          updated_by uuid NULL,
          created_at timestamptz NOT NULL DEFAULT now(),
          updated_at timestamptz NOT NULL DEFAULT now()
        )
        """
    )
    op.execute("CREATE INDEX IF NOT EXISTS idx_qa_tags_status ON qa_tags(status)")
    # 用历史 QA 记录里的标签初始化标准标签库，避免上线后已有标签突然不可选。
    op.execute(
        """
        INSERT INTO qa_tags(name, normalized_name, status)
        SELECT tag, lower(tag), 'enabled'
        FROM (
          SELECT DISTINCT btrim(unnest(tags)) AS tag
          FROM qa_pairs
          WHERE deleted_at IS NULL AND tags IS NOT NULL
        ) existing_tags
        WHERE tag <> ''
        ON CONFLICT (normalized_name) DO NOTHING
        """
    )


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS qa_tags")
