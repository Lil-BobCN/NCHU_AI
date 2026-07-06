import sys
import unittest
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.api.v1.documents import (  # noqa: E402
    _batch_task_params,
    _new_batch,
    normalize_batch_status,
    normalize_knowledge_base,
    serialize_document,
    serialize_job,
)
from app.db.models import Document, DocumentJob  # noqa: E402


class DocumentApiTests(unittest.TestCase):
    def test_normalize_knowledge_base_compacts_whitespace(self) -> None:
        self.assertEqual(normalize_knowledge_base("  财务   政策  "), "财务 政策")

    def test_serialize_document_includes_knowledge_base(self) -> None:
        document = Document(
            title="票据管理",
            file_name="票据管理.pdf",
            file_ext=".pdf",
            file_size=1024,
            file_hash="hash",
            storage_bucket="docs",
            storage_object_key="docs/1.pdf",
            knowledge_base="财务制度",
            status="indexed",
        )
        document.id = "doc-1"
        document.created_at = None
        document.updated_at = None

        data = serialize_document(document)

        self.assertEqual(data["knowledge_base"], "财务制度")
        self.assertEqual(data["file_name"], "票据管理.pdf")

    def test_batch_task_params_include_traceable_batch_metadata(self) -> None:
        batch = _new_batch("batch_reparse", ["doc-1", "doc-2"])

        params = _batch_task_params(batch, 2)

        self.assertTrue(batch["id"].startswith("BRP-"))
        self.assertEqual(params["batch_id"], batch["id"])
        self.assertEqual(params["batch_action"], "batch_reparse")
        self.assertEqual(params["batch_label"], "批量重解析")
        self.assertEqual(params["batch_size"], 2)
        self.assertEqual(params["batch_index"], 2)

    def test_serialize_job_includes_batch_params(self) -> None:
        job = DocumentJob(
            document_id="doc-1",
            job_type="parse",
            status="failed",
            progress=100,
            message="处理失败",
            error_message="PaddleOCR is not installed",
            params={"batch_id": "BRP-1", "batch_action": "batch_reparse"},
        )
        job.id = "job-1"
        job.created_at = None
        job.updated_at = None

        data = serialize_job(job)

        self.assertEqual(data["params"]["batch_id"], "BRP-1")
        self.assertEqual(data["error_message"], "PaddleOCR is not installed")

    def test_normalize_batch_status_only_accepts_job_statuses(self) -> None:
        self.assertEqual(normalize_batch_status("failed"), "failed")
        self.assertEqual(normalize_batch_status("unknown"), "")


if __name__ == "__main__":
    unittest.main()
