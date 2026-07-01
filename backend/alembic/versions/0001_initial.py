"""initial schema

Revision ID: 0001_initial
Revises:
Create Date: 2026-06-08
"""

from pathlib import Path

from alembic import op


revision = "0001_initial"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    sql_path = Path(__file__).resolve().parents[2] / "sql" / "001_init.sql"
    for statement in sql_path.read_text(encoding="utf-8").split(";"):
        statement = statement.strip()
        if statement:
            op.execute(statement)


def downgrade() -> None:
    for table in [
        "evaluation_results",
        "evaluation_runs",
        "evaluation_cases",
        "answer_feedbacks",
        "retrieval_logs",
        "conversation_messages",
        "conversations",
        "qa_pair_embeddings",
        "qa_pairs",
        "chunk_embeddings",
        "document_chunks",
        "document_parse_results",
        "document_jobs",
        "knowledge_base_versions",
        "documents",
        "admins",
    ]:
        op.execute(f"DROP TABLE IF EXISTS {table} CASCADE")
