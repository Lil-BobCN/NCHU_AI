from __future__ import annotations

from pathlib import Path
import sys
import unittest


BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from app.services.document_upload_service import (  # noqa: E402
    MAX_FILE_NAME_LENGTH,
    file_name_key,
    initial_document_status,
    make_copy_file_name,
    normalize_upload_file_name,
)
from app.services.document_lifecycle_service import (  # noqa: E402
    DocumentLifecycleService,
    StoredObjectRef,
)


class DocumentUploadServiceTests(unittest.TestCase):
    def test_normalize_upload_file_name_keeps_basename(self) -> None:
        self.assertEqual(normalize_upload_file_name("../奖学金政策.pdf"), "奖学金政策.pdf")

    def test_normalize_upload_file_name_defaults_empty_name(self) -> None:
        self.assertEqual(normalize_upload_file_name(""), "upload.bin")

    def test_normalize_upload_file_name_limits_length_and_keeps_suffix(self) -> None:
        file_name = f"{'a' * 320}.pdf"

        normalized = normalize_upload_file_name(file_name)

        self.assertLessEqual(len(normalized), MAX_FILE_NAME_LENGTH)
        self.assertTrue(normalized.endswith(".pdf"))

    def test_make_copy_file_name_adds_stable_suffix_before_extension(self) -> None:
        self.assertEqual(make_copy_file_name("转学政策.pdf", 2), "转学政策 (2).pdf")

    def test_file_name_key_is_case_insensitive(self) -> None:
        self.assertEqual(file_name_key(" Policy.PDF "), file_name_key("policy.pdf"))

    def test_archive_upload_uses_needs_extraction_status(self) -> None:
        self.assertEqual(initial_document_status("资料包.zip"), "needs_extraction")
        self.assertEqual(initial_document_status("资料包.RAR"), "uploaded")
        self.assertEqual(initial_document_status("奖学金政策.pdf"), "uploaded")

    def test_remove_storage_objects_deduplicates_refs(self) -> None:
        fake_minio = FakeMinio()
        service = DocumentLifecycleService()

        service.remove_storage_objects(
            [
                StoredObjectRef("documents", "a.pdf"),
                StoredObjectRef("documents", "a.pdf"),
                StoredObjectRef("parsed", None),
                StoredObjectRef("parsed", "content.md"),
            ],
            fake_minio,
        )

        self.assertEqual(fake_minio.removed, [("documents", "a.pdf"), ("parsed", "content.md")])


class FakeMinio:
    def __init__(self) -> None:
        self.removed: list[tuple[str, str]] = []

    def remove_object(self, bucket: str, object_key: str) -> None:
        self.removed.append((bucket, object_key))


if __name__ == "__main__":
    unittest.main()
