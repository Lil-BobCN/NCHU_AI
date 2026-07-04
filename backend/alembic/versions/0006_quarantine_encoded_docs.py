"""quarantine legacy encoded duplicate documents

Revision ID: 0006_quarantine_encoded_docs
Revises: 0005_cleanup_deleted_artifacts
Create Date: 2026-06-23
"""

from alembic import op


revision = "0006_quarantine_encoded_docs"
down_revision = "0005_cleanup_deleted_artifacts"
branch_labels = None
depends_on = None


LEGACY_URL_ENCODED_NAME_PATTERN = (
    r"(^|[^%])%(8[0-9A-F]|9[0-9A-F]|A[0-9A-F]|B[0-9A-F])(%[0-9A-F]{2}){2,}|%EF%BF%BD"
)


def upgrade() -> None:
    op.execute("DROP TABLE IF EXISTS tmp_quarantine_documents")
    op.execute(
        f"""
        CREATE TEMP TABLE tmp_quarantine_documents ON COMMIT DROP AS
        SELECT active.id AS document_id
        FROM documents active
        WHERE active.deleted_at IS NULL
          AND active.file_name ~* '{LEGACY_URL_ENCODED_NAME_PATTERN}'
          AND EXISTS (
            SELECT 1
            FROM documents deleted
            WHERE deleted.deleted_at IS NOT NULL
              AND deleted.file_name = active.file_name
          )
        """
    )
    op.execute("DROP TABLE IF EXISTS tmp_quarantine_document_chunks")
    op.execute(
        """
        CREATE TEMP TABLE tmp_quarantine_document_chunks ON COMMIT DROP AS
        SELECT c.id AS chunk_id, c.document_id
        FROM document_chunks c
        JOIN tmp_quarantine_documents qd ON qd.document_id = c.document_id
        """
    )
    op.execute("DROP TABLE IF EXISTS tmp_quarantine_document_qas")
    op.execute(
        """
        CREATE TEMP TABLE tmp_quarantine_document_qas ON COMMIT DROP AS
        SELECT DISTINCT q.id AS qa_pair_id
        FROM qa_pairs q
        LEFT JOIN tmp_quarantine_documents qd ON qd.document_id = q.source_document_id
        WHERE (
            qd.document_id IS NOT NULL
            OR (
              q.source_chunk_ids IS NOT NULL
              AND EXISTS (
                SELECT 1
                FROM tmp_quarantine_document_chunks qc
                WHERE qc.chunk_id = ANY(q.source_chunk_ids)
              )
            )
          )
        """
    )
    op.execute(
        """
        DELETE FROM qa_pair_embeddings qe
        USING tmp_quarantine_document_qas qq
        WHERE qe.qa_pair_id = qq.qa_pair_id
        """
    )
    op.execute(
        """
        UPDATE qa_pairs q
        SET status = 'disabled',
            deleted_at = now(),
            updated_at = now()
        FROM tmp_quarantine_document_qas qq
        WHERE q.id = qq.qa_pair_id
          AND q.deleted_at IS NULL
        """
    )
    op.execute(
        """
        DELETE FROM chunk_embeddings e
        USING tmp_quarantine_documents qd
        WHERE e.document_id = qd.document_id
        """
    )
    op.execute(
        """
        DELETE FROM document_chunks c
        USING tmp_quarantine_documents qd
        WHERE c.document_id = qd.document_id
        """
    )
    op.execute(
        """
        DELETE FROM document_parse_results p
        USING tmp_quarantine_documents qd
        WHERE p.document_id = qd.document_id
        """
    )
    op.execute(
        """
        UPDATE document_jobs j
        SET status = 'canceled',
            progress = 100,
            message = 'legacy encoded duplicate document quarantined; stale indexing job canceled',
            error_message = NULL,
            finished_at = now(),
            updated_at = now()
        FROM tmp_quarantine_documents qd
        WHERE j.document_id = qd.document_id
          AND j.status IN ('pending', 'running')
        """
    )
    op.execute(
        """
        UPDATE documents d
        SET status = 'deleted',
            deleted_at = now(),
            updated_at = now()
        FROM tmp_quarantine_documents qd
        WHERE d.id = qd.document_id
          AND d.deleted_at IS NULL
        """
    )
    op.execute(
        """
        INSERT INTO knowledge_base_versions(scope, version, changed_at, reason, document_id)
        SELECT 'default', 1, now(), 'quarantine_legacy_encoded_duplicate_documents', NULL
        WHERE EXISTS (SELECT 1 FROM tmp_quarantine_documents)
        ON CONFLICT (scope) DO UPDATE
        SET version = knowledge_base_versions.version + 1,
            changed_at = EXCLUDED.changed_at,
            reason = EXCLUDED.reason,
            document_id = NULL
        """
    )


def downgrade() -> None:
    pass
