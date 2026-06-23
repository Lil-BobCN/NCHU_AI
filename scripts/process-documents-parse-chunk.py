import argparse
import asyncio
import sys
from pathlib import Path

from sqlalchemy import select, update


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))

from app.db.models import Document  # noqa: E402
from app.db.session import AsyncSessionLocal  # noqa: E402
from app.services.document_pipeline import DocumentPipeline  # noqa: E402
from app.services.minio_service import MinioService  # noqa: E402


async def process_document(document_id: str) -> str:
    pipeline = DocumentPipeline()
    minio = MinioService()
    async with AsyncSessionLocal() as db:
        document = await db.scalar(select(Document).where(Document.id == document_id))
        if document is None:
            return f"SKIP missing {document_id}"
        data = minio.read_bytes(document.storage_bucket, document.storage_object_key)
        parsed = pipeline.parse_service.parse(document.file_name, data)
        await pipeline._store_parse_assets(document_id, parsed)
        quality = pipeline.parse_service.quality_score(parsed)
        object_key = f"parsed/{document_id}/content.md"
        minio.upload_text(pipeline.settings.minio_parsed_bucket, parsed.markdown or parsed.text, object_key)
        await pipeline._store_parse_result(db, document_id, parsed, quality, object_key)
        if parsed.meta.get("skip_chunking"):
            await db.execute(
                update(Document)
                .where(Document.id == document_id)
                .values(status="parsed", parse_quality_score=quality, error_message=None)
            )
            await db.commit()
            return f"PARSED skip_chunking {document.file_name}"
        chunk_count = await pipeline._chunk_document(db, document_id)
        await db.execute(
            update(Document)
            .where(Document.id == document_id)
            .values(status="chunked", parse_quality_score=quality, error_message=None)
        )
        await db.commit()
        return f"CHUNKED {chunk_count} {document.file_name}"


async def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--limit", type=int, default=0)
    parser.add_argument("--status", nargs="*", default=["uploaded", "failed", "parsed"])
    args = parser.parse_args()

    async with AsyncSessionLocal() as db:
        query = select(Document).where(Document.deleted_at.is_(None))
        if args.status:
            query = query.where(Document.status.in_(args.status))
        query = query.order_by(Document.created_at)
        if args.limit:
            query = query.limit(args.limit)
        rows = await db.execute(query)
        ids = [str(document.id) for document in rows.scalars()]

    print(f"found {len(ids)} documents")
    for index, document_id in enumerate(ids, start=1):
        try:
            result = await process_document(document_id)
        except Exception as exc:
            result = f"FAIL {document_id}: {exc}"
        print(f"[{index}/{len(ids)}] {result}", flush=True)


if __name__ == "__main__":
    asyncio.run(main())
