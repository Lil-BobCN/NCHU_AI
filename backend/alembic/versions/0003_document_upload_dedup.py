"""enforce active document file name uniqueness

Revision ID: 0003_document_upload_dedup
Revises: 0002_context_state
Create Date: 2026-06-22
"""

from alembic import op


revision = "0003_document_upload_dedup"
down_revision = "0002_context_state"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        """
        WITH ranked AS (
          SELECT
            id,
            file_name,
            row_number() OVER (
              PARTITION BY lower(btrim(file_name))
              ORDER BY updated_at DESC NULLS LAST, created_at DESC NULLS LAST, id DESC
            ) AS duplicate_rank
          FROM documents
          WHERE deleted_at IS NULL
        ),
        parts AS (
          SELECT
            id,
            file_name,
            COALESCE(substring(file_name from '\\.[^.]*$'), '') AS ext,
            CASE
              WHEN substring(file_name from '\\.[^.]*$') IS NULL THEN file_name
              ELSE regexp_replace(file_name, '\\.[^.]*$', '')
            END AS stem
          FROM ranked
          WHERE duplicate_rank > 1
        ),
        renamed AS (
          SELECT
            id,
            file_name,
            left(
              stem,
              greatest(1, 255 - char_length(' (duplicate-' || left(id::text, 8) || ')' || ext))
            ) || ' (duplicate-' || left(id::text, 8) || ')' || ext AS new_file_name
          FROM parts
        )
        UPDATE documents AS d
        SET
          file_name = r.new_file_name,
          title = CASE WHEN d.title = r.file_name THEN r.new_file_name ELSE d.title END,
          updated_at = now()
        FROM renamed AS r
        WHERE d.id = r.id
        """
    )
    op.execute(
        """
        CREATE UNIQUE INDEX IF NOT EXISTS uq_documents_active_file_name_ci
        ON documents (lower(btrim(file_name)))
        WHERE deleted_at IS NULL
        """
    )


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS uq_documents_active_file_name_ci")
