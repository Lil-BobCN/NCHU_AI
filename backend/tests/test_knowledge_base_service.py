from __future__ import annotations

from pathlib import Path
import sys
import unittest


BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from app.services.knowledge_base_service import (  # noqa: E402
    KnowledgeBaseOption,
    KnowledgeBaseService,
    normalize_knowledge_base_name,
    serialize_knowledge_base_option,
)


class KnowledgeBaseServiceTests(unittest.TestCase):
    def test_normalize_knowledge_base_name_compacts_whitespace_and_limits_length(self) -> None:
        self.assertEqual(normalize_knowledge_base_name("  finance   policy  "), "finance policy")
        self.assertEqual(len(normalize_knowledge_base_name("x" * 80)), 64)

    def test_serialize_knowledge_base_option_keeps_java_value_and_label(self) -> None:
        option = KnowledgeBaseOption(
            id="1",
            code="kb-001",
            value="kb-001",
            label="Finance Policy",
            source="knowledge_info",
            sort_order=2,
            is_top=1,
        )

        data = serialize_knowledge_base_option(option)

        self.assertEqual(data["value"], "kb-001")
        self.assertEqual(data["code"], "kb-001")
        self.assertEqual(data["label"], "Finance Policy")
        self.assertEqual(data["name"], "Finance Policy")
        self.assertEqual(data["source"], "knowledge_info")

    def test_dedupe_keeps_first_value(self) -> None:
        options = KnowledgeBaseService._dedupe(
            [
                KnowledgeBaseOption(value="default", label="default"),
                KnowledgeBaseOption(value="kb-001", label="Finance", source="knowledge_info"),
                KnowledgeBaseOption(value="kb-001", label="Finance Duplicate", source="documents"),
            ]
        )

        self.assertEqual([item.value for item in options], ["default", "kb-001"])
        self.assertEqual(options[1].source, "knowledge_info")


if __name__ == "__main__":
    unittest.main()
