import sys
import unittest
from datetime import datetime
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.services.knowledge_base_service import (  # noqa: E402
    KnowledgeBaseOption,
    KnowledgeBaseService,
    normalize_knowledge_base_name,
    serialize_knowledge_base_option,
)


class KnowledgeBaseServiceTests(unittest.TestCase):
    def test_normalize_knowledge_base_name_compacts_whitespace_and_limits_length(self) -> None:
        self.assertEqual(normalize_knowledge_base_name("  招生办   政策  "), "招生办 政策")
        self.assertEqual(len(normalize_knowledge_base_name("x" * 80)), 64)

    def test_serialize_knowledge_base_option_keeps_frontend_contract(self) -> None:
        created_at = datetime(2026, 7, 1, 13, 52, 22)
        option = KnowledgeBaseOption(
            id="2072196595978928130",
            code="74ExrzBdHz",
            value="测试",
            label="测试",
            source="knowledge_info",
            sort_order=1,
            created_at=created_at,
        )

        data = serialize_knowledge_base_option(option)

        self.assertEqual(data["value"], "测试")
        self.assertEqual(data["label"], "测试")
        self.assertEqual(data["name"], "测试")
        self.assertEqual(data["source"], "knowledge_info")
        self.assertEqual(data["created_at"], "2026-07-01T13:52:22")

    def test_dedupe_keeps_default_then_master_options(self) -> None:
        options = KnowledgeBaseService._dedupe(
            [
                KnowledgeBaseOption(value="default", label="default"),
                KnowledgeBaseOption(value="招生办", label="招生办", source="knowledge_info"),
                KnowledgeBaseOption(value="default", label="default", source="documents"),
                KnowledgeBaseOption(value="招生办", label="招生办", source="documents"),
            ]
        )

        self.assertEqual([option.value for option in options], ["default", "招生办"])
        self.assertEqual(options[1].source, "knowledge_info")


if __name__ == "__main__":
    unittest.main()
