import argparse
import asyncio
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))

from sqlalchemy import case, select  # noqa: E402

from app.core.config import get_settings  # noqa: E402
from app.db.models import Document  # noqa: E402
from app.db.session import AsyncSessionLocal  # noqa: E402
from app.services.document_pipeline import DocumentPipeline, supported_file  # noqa: E402
from app.services.hash_service import sha256_bytes  # noqa: E402
from app.services.minio_service import MinioService  # noqa: E402


async def ingest_file(path: Path, auto_process: bool) -> str:
    settings = get_settings()
    data = path.read_bytes()
    if len(data) > settings.max_upload_size_mb * 1024 * 1024:
        return f"SKIP size>{settings.max_upload_size_mb}MB {path.name}"
    file_hash = sha256_bytes(data)
    async with AsyncSessionLocal() as db:
        existing = await db.scalar(
            select(Document)
            .where(Document.file_hash == file_hash, Document.deleted_at.is_(None))
            .order_by(
                case(
                    (Document.status == "indexed", 0),
                    (Document.status == "chunked", 1),
                    (Document.status == "parsed", 2),
                    else_=3,
                ),
                Document.updated_at.desc(),
            )
        )
        if existing:
            return f"SKIP existing {path.name} -> {existing.id}"
        object_key, download_url = MinioService().upload_bytes(
            settings.minio_documents_bucket,
            data,
            path.name,
            "application/pdf" if path.suffix.lower() == ".pdf" else "application/octet-stream",
        )
        document = Document(
            title=path.stem,
            file_name=path.name,
            file_ext=path.suffix.lower(),
            mime_type="application/pdf" if path.suffix.lower() == ".pdf" else None,
            file_size=len(data),
            file_hash=file_hash,
            storage_bucket=settings.minio_documents_bucket,
            storage_object_key=object_key,
            preview_url=download_url,
            download_url=download_url,
            status="uploaded",
        )
        db.add(document)
        await db.commit()
        await db.refresh(document)
        document_id = str(document.id)
        if auto_process:
            await DocumentPipeline().run_full_pipeline(db, document_id, data)
        return f"OK {path.name} -> {document_id}"


async def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("folder", nargs="?", default=str(ROOT / "10个合同"))
    parser.add_argument("--ext", nargs="*", default=[".pdf"])
    parser.add_argument("--all", action="store_true")
    parser.add_argument("--limit", type=int, default=0)
    parser.add_argument("--no-process", action="store_true")
    args = parser.parse_args()

    folder = Path(args.folder)
    extensions = {item.lower() if item.startswith(".") else f".{item.lower()}" for item in args.ext}
    paths = [
        path
        for path in sorted(folder.iterdir())
        if path.is_file()
        and supported_file(path.name)
        and (args.all or path.suffix.lower() in extensions)
    ]
    if args.limit:
        paths = paths[: args.limit]
    print(f"found {len(paths)} files")
    for index, path in enumerate(paths, start=1):
        print(f"[{index}/{len(paths)}] {path.name}")
        try:
            print(await ingest_file(path, auto_process=not args.no_process))
        except Exception as exc:
            print(f"FAIL {path.name}: {exc}")


if __name__ == "__main__":
    asyncio.run(main())
