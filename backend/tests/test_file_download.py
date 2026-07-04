from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch
import sys
import unittest


BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from app.api.v1.documents import _document_access_url  # noqa: E402
from app.api.v1.files import _content_disposition  # noqa: E402
from app.services.minio_service import MinioService  # noqa: E402
from app.services.retrieval_service import RetrievalService  # noqa: E402


class FileDownloadNameTests(unittest.TestCase):
    def test_content_disposition_keeps_utf8_original_name(self) -> None:
        header = _content_disposition("奖学金 申请说明.pdf")

        self.assertIn('filename="download.pdf"', header)
        self.assertIn("filename*=UTF-8''%E5%A5%96%E5%AD%A6%E9%87%91", header)
        self.assertIn("%20%E7%94%B3%E8%AF%B7%E8%AF%B4%E6%98%8E.pdf", header)

    def test_document_download_url_uses_proxy_with_original_file_name(self) -> None:
        document = SimpleNamespace(
            source_url="https://example.com/random-object",
            storage_bucket="documents",
            storage_object_key="2026/06/random-id/file.pdf",
            file_name="转学政策说明.pdf",
            preview_url="https://example.com/preview",
            download_url="https://example.com/download",
        )

        class FakeMinioService:
            def proxy_url(self, bucket: str, object_key: str, download_name: str | None = None) -> str:
                return f"/proxy/{bucket}/{object_key}?download_name={download_name}"

        with patch("app.api.v1.documents.MinioService", FakeMinioService):
            url = _document_access_url(document, download=True)

        self.assertEqual(url, "/proxy/documents/2026/06/random-id/file.pdf?download_name=转学政策说明.pdf")

    def test_document_preview_url_keeps_external_source_url(self) -> None:
        document = SimpleNamespace(
            source_url="https://example.com/source.pdf",
            storage_bucket="documents",
            storage_object_key="2026/06/random-id/file.pdf",
            file_name="转学政策说明.pdf",
            preview_url=None,
            download_url=None,
        )

        self.assertEqual(_document_access_url(document, download=False), "https://example.com/source.pdf")

    def test_retrieval_source_url_uses_original_file_name_for_proxy_download(self) -> None:
        service = RetrievalService()
        service.minio_service = FakeRetrievalMinio()

        url = service._result_url(
            {
                "storage_bucket": "documents",
                "storage_object_key": "2026/06/random-id/file.pdf",
                "document_name": "奖学金申请说明.pdf",
            }
        )

        self.assertEqual(url, "/files/documents/2026/06/random-id/file.pdf?download_name=奖学金申请说明.pdf")

    def test_retrieval_source_url_prefers_proxy_download_over_external_source(self) -> None:
        service = RetrievalService()
        service.minio_service = FakeRetrievalMinio()

        url = service._result_url(
            {
                "source_url": "https://example.com/random-object",
                "storage_bucket": "documents",
                "storage_object_key": "2026/06/random-id/file.pdf",
                "document_name": "转学政策说明.pdf",
            }
        )

        self.assertEqual(url, "/files/documents/2026/06/random-id/file.pdf?download_name=转学政策说明.pdf")

    def test_citation_exposes_original_document_name(self) -> None:
        service = RetrievalService()
        service.minio_service = FakeRetrievalMinio()

        citations = service._citations(
            [
                {
                    "document_id": "00000000-0000-0000-0000-000000000001",
                    "document_title": "转学政策",
                    "document_name": "转学政策说明.pdf",
                    "storage_bucket": "documents",
                    "storage_object_key": "2026/06/random-id/file.pdf",
                    "url": "/files/documents/2026/06/random-id/file.pdf?download_name=转学政策说明.pdf",
                }
            ]
        )

        self.assertEqual(citations[0]["document_name"], "转学政策说明.pdf")

    def test_proxy_url_encodes_download_name(self) -> None:
        service = MinioService.__new__(MinioService)
        service.settings = SimpleNamespace(app_public_base_url="")

        url = service.proxy_url("documents", "2026/06/random-id/file.pdf", download_name="奖学金 申请.pdf")

        self.assertIn("download_name=%E5%A5%96%E5%AD%A6%E9%87%91%20%E7%94%B3%E8%AF%B7.pdf", url)


class FakeRetrievalMinio:
    def proxy_url(self, bucket: str, object_key: str, download_name: str | None = None) -> str:
        return f"/files/{bucket}/{object_key}?download_name={download_name}"


if __name__ == "__main__":
    unittest.main()
