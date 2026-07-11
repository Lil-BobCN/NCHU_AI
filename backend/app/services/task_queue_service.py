"""任务队列服务：用 Redis list 管理后台任务的入队和出队。"""

import json
from datetime import datetime, timezone
from uuid import uuid4

from app.core.config import get_settings
from app.core.json_utils import to_jsonable
from app.services.redis_service import RedisService


class TaskQueueService:
    def __init__(self) -> None:
        self.settings = get_settings()
        self.redis_service = RedisService()

    async def enqueue(self, task_type: str, payload: dict) -> dict:
        task_id = str(uuid4())
        task_payload = to_jsonable(payload)
        if isinstance(task_payload, dict):
            task_payload.setdefault("queue_task_id", task_id)
        task = {
            "id": task_id,
            "type": task_type,
            "payload": task_payload,
            "enqueued_at": datetime.now(timezone.utc).isoformat(),
        }
        await self.redis_service.lpush(
            self.settings.background_task_queue_key,
            json.dumps(task, ensure_ascii=False, separators=(",", ":")),
        )
        return task

    async def dequeue(self) -> dict | None:
        result = await self.redis_service.brpop(
            self.settings.background_task_queue_key,
            timeout=max(1, int(self.settings.background_worker_poll_timeout_seconds)),
        )
        if result is None:
            return None
        _, raw = result
        task = json.loads(raw)
        if not isinstance(task, dict):
            raise ValueError("Invalid background task payload")
        return task
