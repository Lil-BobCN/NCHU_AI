import json
from datetime import datetime
from datetime import timedelta
from io import BytesIO
from pathlib import Path
from urllib.parse import quote, urlsplit, urlunsplit
from uuid import uuid4

from minio import Minio

from app.core.config import get_settings


class MinioService:
    def __init__(self) -> None:
        self.settings = get_settings()
        self.client = Minio(
            self.settings.minio_endpoint,
            access_key=self.settings.minio_access_key,
            secret_key=self.settings.minio_secret_key,
            secure=self.settings.minio_secure,
        )

    def ensure_buckets(self) -> None:
        for bucket in [
            self.settings.minio_documents_bucket,
            self.settings.minio_parsed_bucket,
            self.settings.minio_preview_bucket,
        ]:
            if not self.client.bucket_exists(bucket):
                self.client.make_bucket(bucket)
            self._clear_public_read_policy(bucket)

    def _clear_public_read_policy(self, bucket: str) -> None:
        try:
            self.client.delete_bucket_policy(bucket)
        except Exception as exc:
            import logging
            logging.getLogger(__name__).warning(
                "清理 MinIO bucket %s 公开读策略失败: %s", bucket, exc
            )

    def upload_bytes(
        self,
        bucket: str,
        data: bytes,
        file_name: str,
        content_type: str | None = None,
    ) -> tuple[str, str]:
        self.ensure_buckets()
        today = datetime.now()
        safe_name = Path(file_name).name
        object_key = f"{today:%Y/%m}/{uuid4()}/{safe_name}"
        self.client.put_object(
            bucket,
            object_key,
            BytesIO(data),
            length=len(data),
            content_type=content_type or "application/octet-stream",
        )
        return object_key, self.public_url(bucket, object_key)

    def upload_text(self, bucket: str, text: str, object_key: str) -> str:
        self.ensure_buckets()
        data = text.encode("utf-8")
        self.client.put_object(
            bucket,
            object_key,
            BytesIO(data),
            length=len(data),
            content_type="text/plain; charset=utf-8",
        )
        return self.public_url(bucket, object_key)

    def read_bytes(self, bucket: str, object_key: str) -> bytes:
        response = self.client.get_object(bucket, object_key)
        try:
            return response.read()
        finally:
            response.close()
            response.release_conn()

    def get_object(self, bucket: str, object_key: str):
        return self.client.get_object(bucket, object_key)

    def remove_object(self, bucket: str, object_key: str | None) -> None:
        if not object_key:
            return
        try:
            self.client.remove_object(bucket, object_key)
        except Exception as exc:
            import logging
            logging.getLogger(__name__).warning(
                "删除 MinIO 对象失败: bucket=%s object=%s error=%s", bucket, object_key, exc
            )

    def signed_url(
        self,
        bucket: str,
        object_key: str,
        expires_seconds: int = 3600,
        download_name: str | None = None,
    ) -> str:
        client = self._public_client() or self.client
        response_headers = None
        if download_name:
            response_headers = {
                "response-content-disposition": (
                    "attachment; "
                    f"filename*=UTF-8''{quote(Path(download_name).name, safe='')}"
                )
            }
        url = client.presigned_get_object(
            bucket,
            object_key,
            expires=timedelta(seconds=max(60, expires_seconds)),
            response_headers=response_headers,
        )
        return url if client is not self.client else self._rewrite_to_public_base(url)

    def public_url(self, bucket: str, object_key: str) -> str:
        base = self.settings.minio_public_base_url.rstrip("/")
        return f"{base}/{bucket}/{object_key}"

    def proxy_url(self, bucket: str, object_key: str, download_name: str | None = None) -> str:
        base = (self.settings.app_public_base_url or "").rstrip("/")
        path = f"/api/v1/files/{quote(bucket, safe='')}/{quote(object_key, safe='')}"
        if download_name:
            path = f"{path}?download_name={quote(Path(download_name).name, safe='')}"
        return f"{base}{path}" if base else path

    def _rewrite_to_public_base(self, url: str) -> str:
        public_base = (self.settings.minio_public_base_url or "").rstrip("/")
        if not public_base:
            return url
        source = urlsplit(url)
        target = urlsplit(public_base)
        if not target.scheme or not target.netloc:
            return url
        return urlunsplit((target.scheme, target.netloc, source.path, source.query, source.fragment))

    def _public_client(self) -> Minio | None:
        public_base = (self.settings.minio_public_base_url or "").rstrip("/")
        if not public_base:
            return None
        target = urlsplit(public_base)
        if not target.scheme or not target.netloc:
            return None
        return Minio(
            target.netloc,
            access_key=self.settings.minio_access_key,
            secret_key=self.settings.minio_secret_key,
            secure=target.scheme == "https",
            region="us-east-1",
        )
