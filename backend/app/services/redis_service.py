"""
Redis 封装。提供 JSON 缓存、队列、阻塞弹出和分布式控制所需基础操作。
"""

import json
from typing import Any
from redis.asyncio import Redis
from redis.exceptions import TimeoutError as RedisTimeoutError

from app.core.config import get_settings


_redis_clients: dict[str, Redis] = {}


def _redis_client(url: str) -> Redis:
    client = _redis_clients.get(url)
    if client is None:
        client = Redis.from_url(url, decode_responses=True)
        _redis_clients[url] = client
    return client


async def close_redis_clients() -> None:
    clients = list(_redis_clients.values())
    _redis_clients.clear()
    for client in clients:
        await client.aclose()


class RedisService:
    def __init__(self) -> None:
        self.redis = _redis_client(get_settings().redis_url)

    async def set_json(self, key: str, value: Any, ttl: int | None = None) -> None:
        payload = json.dumps(value, ensure_ascii=False)
        if ttl:
            await self.redis.setex(key, ttl, payload)
        else:
            await self.redis.set(key, payload)

    async def get_json(self, key: str) -> Any | None:
        raw = await self.redis.get(key)
        if raw is None:
            return None
        return json.loads(raw)

    async def mget_json(self, keys: list[str]) -> list[Any | None]:
        if not keys:
            return []
        values = await self.redis.mget(keys)
        results: list[Any | None] = []
        for raw in values:
            if raw is None:
                results.append(None)
                continue
            try:
                results.append(json.loads(raw))
            except Exception:
                results.append(None)
        return results

    async def mset_json(self, items: dict[str, Any], ttl: int | None = None) -> None:
        if not items:
            return
        async with self.redis.pipeline(transaction=False) as pipe:
            for key, value in items.items():
                payload = json.dumps(value, ensure_ascii=False)
                if ttl:
                    pipe.setex(key, ttl, payload)
                else:
                    pipe.set(key, payload)
            await pipe.execute()

    async def ping(self) -> bool:
        return bool(await self.redis.ping())

    async def eval(self, script: str, keys: list[str], args: list[Any]) -> Any:
        return await self.redis.eval(script, len(keys), *keys, *args)

    async def lpush(self, key: str, value: str) -> int:
        return int(await self.redis.lpush(key, value))

    async def brpop(self, key: str, timeout: int) -> tuple[str, str] | None:
        try:
            result = await self.redis.brpop(key, timeout=timeout)
        except RedisTimeoutError:
            return None
        if result is None:
            return None
        queue_key, value = result
        return str(queue_key), str(value)
