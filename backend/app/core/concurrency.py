"""并发控制工具：用本地信号量和 Redis 槽位保护模型与聊天接口。"""

import asyncio
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager, suppress
from contextvars import ContextVar

from app.core.config import get_settings
from app.services.redis_service import RedisService


settings = get_settings()

_chat_slots = asyncio.Semaphore(max(1, settings.chat_max_concurrent_requests))
_model_slots = asyncio.Semaphore(max(1, settings.model_max_concurrent_requests))
_embedding_slots = asyncio.Semaphore(max(1, settings.embedding_max_concurrent_requests))
_rerank_slots = asyncio.Semaphore(max(1, settings.rerank_max_concurrent_requests))
_chat_slot_state: ContextVar[tuple[bool, bool] | None] = ContextVar("chat_slot_state", default=None)
_chat_global_key = "rag:chat:active_requests"
_acquire_chat_slot_script = """
local limit = tonumber(ARGV[1])
local ttl_ms = tonumber(ARGV[2])
local current = tonumber(redis.call('GET', KEYS[1]) or '0')
if current >= limit then
  if current > 0 then
    redis.call('PEXPIRE', KEYS[1], ttl_ms)
  end
  return 0
end
current = redis.call('INCR', KEYS[1])
redis.call('PEXPIRE', KEYS[1], ttl_ms)
if current > limit then
  redis.call('DECR', KEYS[1])
  return 0
end
return 1
"""
_release_chat_slot_script = """
local current = tonumber(redis.call('GET', KEYS[1]) or '0')
if current <= 1 then
  redis.call('DEL', KEYS[1])
  return 0
end
return redis.call('DECR', KEYS[1])
"""


async def try_acquire_chat_slot() -> bool:
    try:
        await asyncio.wait_for(
            _chat_slots.acquire(),
            timeout=max(0.001, settings.chat_queue_timeout_seconds),
        )
    except TimeoutError:
        return False
    redis_acquired = await _try_acquire_global_chat_slot()
    if redis_acquired is False:
        _chat_slots.release()
        return False
    _chat_slot_state.set((True, bool(redis_acquired)))
    return True


def release_chat_slot() -> None:
    state = _chat_slot_state.get()
    _chat_slot_state.set(None)
    if state and state[1]:
        asyncio.create_task(_release_global_chat_slot())
    _chat_slots.release()


async def _try_acquire_global_chat_slot() -> bool | None:
    if not settings.chat_distributed_concurrency_enabled:
        return None
    limit = int(settings.chat_global_max_concurrent_requests or 0)
    if limit <= 0:
        return None
    ttl_ms = max(1000, int(settings.chat_slot_ttl_seconds * 1000))
    try:
        result = await RedisService().eval(
            _acquire_chat_slot_script,
            [_chat_global_key],
            [limit, ttl_ms],
        )
        return bool(int(result))
    except Exception:
        return None


async def _release_global_chat_slot() -> None:
    with suppress(Exception):
        await RedisService().eval(_release_chat_slot_script, [_chat_global_key], [])


@asynccontextmanager
async def model_call_slot() -> AsyncIterator[None]:
    async with _model_slots:
        yield


@asynccontextmanager
async def embedding_call_slot() -> AsyncIterator[None]:
    async with _embedding_slots:
        yield


@asynccontextmanager
async def rerank_call_slot() -> AsyncIterator[None]:
    async with _rerank_slots:
        yield
