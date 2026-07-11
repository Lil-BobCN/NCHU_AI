"""
后台 worker 入口。消费 Redis 队列任务，分发文档处理、QA 生成、QA 向量同步和评测运行。
"""

import asyncio
import logging

from app.core.config import get_settings
from app.db.session import AsyncSessionLocal
from app.services.document_pipeline import DocumentPipeline
from app.services.model_service import close_model_clients
from app.services.qa_embedding_service import QaEmbeddingService
from app.services.qa_generation_service import QaGenerationService
from app.services.redis_service import close_redis_clients
from app.services.rerank_service import close_rerank_clients
from app.services.task_queue_service import TaskQueueService


logger = logging.getLogger("rag.background_worker")


async def dispatch_task(task: dict) -> None:
    task_type = str(task.get("type") or "")
    payload = task.get("payload") or {}
    if not isinstance(payload, dict):
        raise ValueError("Task payload must be an object")

    # 评测任务内部会自己管理运行记录，这里直接转交评测模块。
    if task_type == "evaluation_run":
        from app.api.v1.evaluation import _run_evaluation

        case_ids = payload.get("case_ids")
        await _run_evaluation(str(payload["run_id"]), list(case_ids) if case_ids else None)
        return

    # 文档类任务共享同一个数据库会话，失败时由具体服务写入任务错误信息。
    async with AsyncSessionLocal() as db:
        if task_type == "document_full_pipeline":
            await DocumentPipeline().run_full_pipeline_from_storage(
                db,
                str(payload["document_id"]),
                job_id=str(payload["job_id"]) if payload.get("job_id") else None,
            )
            return
        if task_type == "document_rechunk":
            await DocumentPipeline().run_chunk_and_embed(
                db,
                str(payload["document_id"]),
                job_id=str(payload["job_id"]) if payload.get("job_id") else None,
            )
            return
        if task_type == "document_reembed":
            await DocumentPipeline().run_embed_only(
                db,
                str(payload["document_id"]),
                job_id=str(payload["job_id"]) if payload.get("job_id") else None,
            )
            return
        if task_type == "document_convert_office":
            await DocumentPipeline().run_convert_office(db, str(payload["document_id"]))
            return
        if task_type == "document_extract_archive":
            await DocumentPipeline().run_extract_archive(db, str(payload["document_id"]))
            return
        if task_type == "document_qa_generate":
            await QaGenerationService().generate_from_document(
                db,
                str(payload["document_id"]),
                int(payload.get("count") or 10),
                bool(payload.get("auto_enable", True)),
            )
            return
        if task_type == "qa_embedding_sync":
            try:
                await QaEmbeddingService().sync_one(db, str(payload["qa_pair_id"]))
                await db.commit()
            except Exception:
                await db.rollback()
                raise
            return

    raise ValueError(f"Unsupported task type: {task_type}")


async def worker_loop(worker_index: int) -> None:
    queue = TaskQueueService()
    logger.info("Background worker %s started", worker_index)
    while True:
        task = await queue.dequeue()
        if task is None:
            continue
        task_id = task.get("id")
        task_type = task.get("type")
        logger.info("Processing task %s (%s)", task_id, task_type)
        try:
            await dispatch_task(task)
            logger.info("Finished task %s (%s)", task_id, task_type)
        except Exception:
            logger.exception("Failed task %s (%s)", task_id, task_type)


async def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s")
    settings = get_settings()
    concurrency = max(1, int(settings.background_worker_concurrency))
    workers = [asyncio.create_task(worker_loop(index + 1)) for index in range(concurrency)]
    try:
        await asyncio.gather(*workers)
    finally:
        for worker in workers:
            worker.cancel()
        await close_rerank_clients()
        await close_model_clients()
        await close_redis_clients()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
