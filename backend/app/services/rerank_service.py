"""Rerank 服务：调用远程重排模型并提供失败重试和降级入口。"""

import httpx

from app.core.concurrency import rerank_call_slot
from app.core.config import get_settings


_http_clients: dict[float, httpx.AsyncClient] = {}


def _http_client(timeout: float) -> httpx.AsyncClient:
    key = float(timeout)
    client = _http_clients.get(key)
    if client is None:
        client = httpx.AsyncClient(timeout=timeout)
        _http_clients[key] = client
    return client


async def close_rerank_clients() -> None:
    clients = list(_http_clients.values())
    _http_clients.clear()
    for client in clients:
        await client.aclose()


class RerankService:
    def __init__(self) -> None:
        self.settings = get_settings()

    async def rerank(self, query: str, candidates: list[dict]) -> list[dict]:
        if not candidates or not self.settings.rerank_api_key:
            return self._fallback(candidates)
        for attempt in range(max(1, self.settings.rerank_request_retries + 1)):
            try:
                scores = await self._call_rerank_api(query, candidates)
                break
            except Exception:
                if attempt >= self.settings.rerank_request_retries:
                    return self._fallback(candidates)
        try:
            for item, score in zip(candidates, scores, strict=False):
                item["rerank_score"] = float(score)
            return sorted(candidates, key=lambda x: x.get("rerank_score", 0), reverse=True)
        except Exception:
            return self._fallback(candidates)

    async def _call_rerank_api(self, query: str, candidates: list[dict]) -> list[float]:
        url = self._endpoint()
        payload = self._dashscope_payload(query, candidates)
        headers = {
            "Authorization": f"Bearer {self.settings.rerank_api_key}",
            "Content-Type": "application/json",
        }
        async with rerank_call_slot():
            response = await _http_client(self.settings.rerank_request_timeout_seconds).post(
                url,
                json=payload,
                headers=headers,
            )
            response.raise_for_status()
            data = response.json()
        results = (data.get("output") or {}).get("results") or data.get("results") or []
        scores = [0.0 for _ in candidates]
        for rank, item in enumerate(results):
            index = int(item.get("index", rank))
            score = item.get("relevance_score", item.get("score", 0))
            if 0 <= index < len(scores):
                scores[index] = float(score)
        return scores

    def _endpoint(self) -> str:
        base_url = self.settings.rerank_base_url.rstrip("/")
        if base_url.endswith("/text-rerank/text-rerank"):
            return base_url
        if base_url.endswith("/api/v1"):
            return f"{base_url}/services/rerank/text-rerank/text-rerank"
        if "dashscope.aliyuncs.com" in base_url:
            return f"{base_url}/api/v1/services/rerank/text-rerank/text-rerank"
        return f"{base_url}/services/rerank/text-rerank/text-rerank"

    def _dashscope_payload(self, query: str, candidates: list[dict]) -> dict:
        return {
            "model": self.settings.rerank_model,
            "input": {
                "query": {"text": query},
                "documents": [{"text": item.get("content", "")} for item in candidates],
            },
            "parameters": {
                "return_documents": False,
                "top_n": len(candidates),
                "instruct": "Given a user question, retrieve relevant passages that answer the question.",
            },
        }

    def _fallback(self, candidates: list[dict]) -> list[dict]:
        for idx, item in enumerate(candidates, start=1):
            item["rerank_score"] = float(item.get("rrf_score", 0)) + max(0, 1 / (idx + 1))
        return sorted(candidates, key=lambda x: x["rerank_score"], reverse=True)
