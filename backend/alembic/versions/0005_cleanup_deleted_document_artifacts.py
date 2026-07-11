"""cleanup deleted document retrieval artifacts

Revision ID: 0005_cleanup_deleted_artifacts
Revises: 0004_knowledge_base_version
Create Date: 2026-06-23
"""

from alembic import op


revision = "0005_cleanup_deleted_artifacts"
down_revision = "0004_knowledge_base_version"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("DROP TABLE IF EXISTS tmp_deleted_document_chunks")
    op.execute(
        """
        CREATE TEMP TABLE tmp_deleted_document_chunks ON COMMIT DROP AS
        SELECT c.id AS chunk_id, c.document_id
        FROM document_chunks c
        JOIN documents d ON d.id = c.document_id
        WHERE d.deleted_at IS NOT NULL
        """
    )
    op.execute("DROP TABLE IF EXISTS tmp_deleted_document_qas")
    op.execute(
        """
        CREATE TEMP TABLE tmp_deleted_document_qas ON COMMIT DROP AS
        SELECT DISTINCT q.id AS qa_pair_id
        FROM qa_pairs q
        LEFT JOIN documents d ON d.id = q.source_document_id
        WHERE (
            (q.source_document_id IS NOT NULL AND d.deleted_at IS NOT NULL)
            OR (
              q.source_chunk_ids IS NOT NULL
              AND EXISTS (
                SELECT 1
                FROM tmp_deleted_document_chunks dc
                WHERE dc.chunk_id = ANY(q.source_chunk_ids)
              )
            )
          )
        """
    )
    op.execute(
        """
        DELETE FROM qa_pair_embeddings qe
        USING tmp_deleted_document_qas dq
        WHERE qe.qa_pair_id = dq.qa_pair_id
        """
    )
    op.execute(
        """
        UPDATE qa_pairs q
        SET status = 'disabled',
            deleted_at = now(),
            updated_at = now()
        FROM tmp_deleted_document_qas dq
        WHERE q.id = dq.qa_pair_id
          AND q.deleted_at IS NULL
        """
    )
    op.execute(
        """
        DELETE FROM chunk_embeddings e
        USING documents d
        WHERE e.document_id = d.id
          AND d.deleted_at IS NOT NULL
        """
    )
    op.execute(
        """
        DELETE FROM document_chunks c
        USING documents d
        WHERE c.document_id = d.id
          AND d.deleted_at IS NOT NULL
        """
    )
    op.execute(
        """
        DELETE FROM document_parse_results p
        USING documents d
        WHERE p.document_id = d.id
          AND d.deleted_at IS NOT NULL
        """
    )
    op.execute(
        """
        UPDATE document_jobs j
        SET status = 'canceled',
            progress = 100,
            message = 'document deleted; stale indexing job canceled',
            error_message = NULL,
            finished_at = now(),
            updated_at = now()
        FROM documents d
        WHERE j.document_id = d.id
          AND d.deleted_at IS NOT NULL
          AND j.status IN ('pending', 'running')
        """
    )
    op.execute(
        """
        INSERT INTO knowledge_base_versions(scope, version, changed_at, reason, document_id)
        VALUES ('default', 1, now(), 'cleanup_deleted_document_artifacts', NULL)
        ON CONFLICT (scope) DO UPDATE
        SET version = knowledge_base_versions.version + 1,
            changed_at = EXCLUDED.changed_at,
            reason = EXCLUDED.reason,
            document_id = NULL
        """
    )


def downgrade() -> None:
    pass
