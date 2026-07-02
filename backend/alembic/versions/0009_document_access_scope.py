"""add document access scope fields

Revision ID: 0009_document_access_scope
Revises: 0008_document_batch_ops
Create Date: 2026-07-01
"""

from alembic import op


revision = "0009_document_access_scope"
down_revision = "0008_document_batch_ops"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        """
        ALTER TABLE documents
        ADD COLUMN IF NOT EXISTS publish_scope varchar(32) NOT NULL DEFAULT 'dept'
        """
    )
    op.execute(
        """
        ALTER TABLE documents
        ADD COLUMN IF NOT EXISTS allowed_dept_ids text[] NULL
        """
    )
    op.execute(
        """
        ALTER TABLE documents
        ADD COLUMN IF NOT EXISTS allowed_user_ids text[] NULL
        """
    )
    op.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_documents_publish_scope
        ON documents(publish_scope)
        """
    )
    op.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_documents_allowed_dept_ids
        ON documents USING GIN(allowed_dept_ids)
        """
    )
    op.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_documents_allowed_user_ids
        ON documents USING GIN(allowed_user_ids)
        """
    )


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS idx_documents_allowed_user_ids")
    op.execute("DROP INDEX IF EXISTS idx_documents_allowed_dept_ids")
    op.execute("DROP INDEX IF EXISTS idx_documents_publish_scope")
    op.execute("ALTER TABLE documents DROP COLUMN IF EXISTS allowed_user_ids")
    op.execute("ALTER TABLE documents DROP COLUMN IF EXISTS allowed_dept_ids")
    op.execute("ALTER TABLE documents DROP COLUMN IF EXISTS publish_scope")
