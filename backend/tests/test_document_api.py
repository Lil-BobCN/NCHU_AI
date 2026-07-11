import sys
import unittest
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.api.v1.documents import normalize_knowledge_base, router, serialize_document, serialize_knowledge_bases  # noqa: E402
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
            publish_dept_id="finance",
            owner_user_id="1001",
            visible_in_chat=True,
            publish_scope="custom",
            allowed_dept_ids=["finance"],
            allowed_user_ids=["1001"],
            status="indexed",
        )
        document.id = "doc-1"
        document.created_at = None
        document.updated_at = None

        data = serialize_document(document)

        self.assertEqual(data["knowledge_base"], "财务制度")
        self.assertEqual(data["file_name"], "票据管理.pdf")
        self.assertEqual(data["publish_dept_id"], "finance")
        self.assertEqual(data["publish_scope"], "custom")
        self.assertEqual(data["allowed_dept_ids"], ["finance"])
        self.assertEqual(data["allowed_user_ids"], ["1001"])

    def test_knowledge_base_list_route_is_registered_before_document_id_route(self) -> None:
        paths = [route.path for route in router.routes]

        self.assertIn("/documents/knowledge-bases", paths)
        self.assertLess(paths.index("/documents/knowledge-bases"), paths.index("/documents/{document_id}"))

    def test_serialize_knowledge_bases_includes_default_contract(self) -> None:
        data = serialize_knowledge_bases(["  招生 政策  ", None, "default"])

        self.assertEqual(data["default"], "default")
        self.assertEqual(data["items"], ["招生 政策", "default"])


if __name__ == "__main__":
    unittest.main()
