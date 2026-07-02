"""add knowledge base version marker

Revision ID: 0004_knowledge_base_version
Revises: 0003_document_upload_dedup
Create Date: 2026-06-22
"""

from alembic import op


revision = "0004_knowledge_base_version"
down_revision = "0003_document_upload_dedup"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        """
        CREATE TABLE IF NOT EXISTS knowledge_base_versions (
          scope varchar(64) PRIMARY KEY DEFAULT 'default',
          version bigint NOT NULL DEFAULT 1,
          changed_at timestamptz NOT NULL DEFAULT now(),
          reason varchar(128) NULL,
          document_id uuid NULL REFERENCES documents(id) ON DELETE SET NULL
        )
        """
    )
    op.execute(
        """
        INSERT INTO knowledge_base_versions(scope, version, changed_at, reason)
        VALUES ('default', 1, now(), 'initial')
        ON CONFLICT (scope) DO NOTHING
        """
    )


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS knowledge_base_versions")
