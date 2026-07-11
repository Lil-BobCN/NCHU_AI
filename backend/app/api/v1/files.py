"""文件访问接口：为 MinIO 文件提供后端代理下载和文件名处理。"""

from pathlib import Path
from urllib.parse import quote, unquote

from fastapi import APIRouter, HTTPException, Query, Request
from fastapi.responses import Response, StreamingResponse

from app.services.minio_service import MinioService


router = APIRouter(prefix="/files", tags=["files"])


def _object_header(response, name: str) -> str | None:
    return response.headers.get(name) or response.headers.get(name.lower()) or response.headers.get(name.title())


def _ascii_download_name(filename: str) -> str:
    safe_name = Path(filename.replace("\\", "/")).name or "download"
    path = Path(safe_name)
    stem = path.stem.encode("ascii", "ignore").decode("ascii").strip(" ._-") or "download"
    suffix = path.suffix if path.suffix and path.suffix.isascii() else ""
    return f"{stem}{suffix}".replace('"', "").replace("\r", "_").replace("\n", "_")


def _content_disposition(filename: str) -> str:
    safe_name = Path(filename.replace("\\", "/")).name or "download"
    encoded = quote(safe_name, safe="")
    return f'attachment; filename="{_ascii_download_name(safe_name)}"; filename*=UTF-8\'\'{encoded}'


@router.api_route("/{bucket}/{object_key:path}", methods=["GET", "HEAD"])
async def get_file(
    request: Request,
    bucket: str,
    object_key: str,
    download_name: str | None = Query(default=None),
):
    bucket = unquote(bucket)
    object_key = unquote(object_key)
    try:
        response = MinioService().get_object(bucket, object_key)
    except Exception as exc:
        raise HTTPException(status_code=404, detail="file_not_found_or_inaccessible") from exc

    filename = Path(download_name or object_key).name
    headers = {}
    content_length = _object_header(response, "content-length")
    if content_length:
        headers["Content-Length"] = content_length
    if download_name:
        headers["Content-Disposition"] = _content_disposition(filename)
    media_type = _object_header(response, "content-type") or "application/octet-stream"

    if request.method == "HEAD":
        response.close()
        response.release_conn()
        return Response(status_code=200, media_type=media_type, headers=headers)

    def iter_object():
        try:
            for chunk in response.stream(1024 * 1024):
                yield chunk
        finally:
            response.close()
            response.release_conn()

    return StreamingResponse(iter_object(), media_type=media_type, headers=headers)
