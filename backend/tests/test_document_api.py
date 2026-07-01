import sys
import unittest
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.api.v1.documents import normalize_knowledge_base, serialize_document  # noqa: E402
from app.db.models import Document  # noqa: E402


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


if __name__ == "__main__":
    unittest.main()
