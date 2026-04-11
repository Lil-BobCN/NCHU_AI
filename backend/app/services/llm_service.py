"""LLM service using DashScope compatible-mode API.

Wraps HTTP calls to the DashScope (Qwen) API with streaming, retry logic,
and error handling. Reuses the payload/response patterns from the existing
Flask app's qwen_api.py.
"""
from __future__ import annotations

import json
import asyncio
from typing import AsyncGenerator

import httpx

from app.core.exceptions import LLMError


class LLMService:
    """DashScope LLM client with streaming and retry support.

    Attributes:
        api_key: DashScope API key.
        model_name: Model identifier (e.g. qwen3.5-plus).
        base_url: DashScope compatible-mode base URL.
        max_retries: Maximum retry attempts on transient failures.
        timeout: HTTP request timeout in seconds.
    """

    def __init__(
        self,
        api_key: str,
        model_name: str = "qwen3.5-plus",
        base_url: str = "https://dashscope.aliyuncs.com/compatible-mode/v1",
        max_retries: int = 2,
        timeout: int = 60,
    ) -> None:
        """Initialize the LLM service.

        Args:
            api_key: DashScope API key.
            model_name: Model to use for completions.
            base_url: Base URL for the DashScope API.
            max_retries: Number of retries on transient errors.
            timeout: HTTP timeout in seconds.
        """
        self.api_key = api_key
        self.model_name = model_name
        self.base_url = base_url.rstrip("/")
        self.max_retries = max_retries
        self.timeout = timeout

    def _build_payload(
        self,
        messages: list[dict],
        stream: bool = True,
        tools: list[dict] | None = None,
    ) -> dict:
        """Build the DashScope API request payload.

        Mirrors the build_payload logic from the Flask app: limits history
        to the last 3 messages, wraps in the DashScope-compatible input format.

        Args:
            messages: Conversation messages (role + content).
            stream: Whether to request streaming.
            tools: Optional list of tools to enable (e.g. web_search).

        Returns:
            Payload dict ready for POST to DashScope.
        """
        # Limit history to last 3 messages (matching existing pattern)
        recent_history = messages[:-1] if len(messages) > 1 else []
        if len(recent_history) > 3:
            recent_history = recent_history[-3:]

        # Build input field
        if recent_history:
            input_messages = [
                {"role": msg["role"], "content": msg.get("content", "")}
                for msg in recent_history
                if msg.get("role") in ("user", "assistant")
            ]
            last_msg = messages[-1] if messages else {}
            input_messages.append(
                {"role": last_msg.get("role", "user"), "content": last_msg.get("content", "")}
            )
            input_data = input_messages
        else:
            last_msg = messages[-1] if messages else {}
            input_data = last_msg.get("content", "")

        payload = {
            "model": self.model_name,
            "input": input_data,
            "stream": stream,
            "enable_thinking": False,
            "temperature": 0.7,
            "max_tokens": 1500,
        }
        if tools:
            payload["tools"] = tools
        return payload

    def _headers(self) -> dict[str, str]:
        """Build HTTP headers for DashScope API requests."""
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "Accept": "text/event-stream",
        }

    async def chat(
        self,
        messages: list[dict],
        stream: bool = True,
        tools: list[dict] | None = None,
    ) -> AsyncGenerator[str, None]:
        """Stream chat response from DashScope API.

        Parses SSE (Server-Sent Events) lines and yields content chunks
        in the same format the existing widget expects.

        Args:
            messages: Conversation messages.
            stream: Whether to stream (always True for this method).
            tools: Optional list of tools to enable (e.g. web_search).

        Yields:
            SSE-formatted data lines (``data: {...}\\n\\n``).
        """
        url = f"{self.base_url}/responses"
        payload = self._build_payload(messages, stream=True, tools=tools)

        for attempt in range(self.max_retries + 1):
            try:
                async with httpx.AsyncClient(
                    timeout=self.timeout
                ) as client:
                    async with client.stream(
                        "POST",
                        url,
                        headers=self._headers(),
                        json=payload,
                    ) as response:
                        if response.status_code != 200:
                            body = await response.aread()
                            error_msg = (
                                f"API request failed: HTTP {response.status_code}"
                            )
                            try:
                                error_data = json.loads(body)
                                if "error" in error_data:
                                    error_msg += f" - {error_data['error']}"
                            except (json.JSONDecodeError, ValueError):
                                error_msg += f" - {body.decode('utf-8', errors='replace')[:200]}"
                            raise LLMError(error_msg)

                        async for line in response.aiter_lines():
                            if not line:
                                continue
                            stripped = line.strip()
                            if stripped.startswith("data:"):
                                yield stripped + "\n\n"
                    return  # Success — exit retry loop

            except httpx.TimeoutException:
                yield f'data: {json.dumps({"error": "请求超时，请稍后重试"})}\n\n'
            except httpx.ConnectError:
                yield f'data: {json.dumps({"error": "网络连接失败，请检查网络"})}\n\n'
            except LLMError:
                raise
            except Exception as exc:
                if attempt < self.max_retries:
                    await asyncio.sleep(0.5 * (attempt + 1))
                    continue
                yield f'data: {json.dumps({"error": "请求失败: " + str(exc)})}\n\n'

    async def chat_completion(self, messages: list[dict]) -> str:
        """Non-streaming chat completion.

        Sends a single request and returns the full response text.

        Args:
            messages: Conversation messages.

        Returns:
            Complete assistant response as a string.

        Raises:
            LLMError: If the API call fails after all retries.
        """
        url = f"{self.base_url}/responses"
        payload = self._build_payload(messages, stream=False)

        for attempt in range(self.max_retries + 1):
            try:
                async with httpx.AsyncClient(timeout=self.timeout) as client:
                    resp = await client.post(
                        url,
                        headers=self._headers(),
                        json=payload,
                    )

                    if resp.status_code != 200:
                        error_msg = f"API request failed: HTTP {resp.status_code}"
                        try:
                            error_data = resp.json()
                            if "error" in error_data:
                                error_msg += f" - {error_data['error']}"
                        except (json.JSONDecodeError, ValueError):
                            error_msg += f" - {resp.text[:200]}"
                        raise LLMError(error_msg)

                    data = resp.json()
                    # DashScope compatible-mode response structure
                    output = data.get("output", {})
                    content = output.get("content", "")

                    # Fallback: try alternate response structure
                    if not content:
                        choices = data.get("choices", [])
                        if choices:
                            content = (
                                choices[0].get("message", {}).get("content", "")
                            )

                    if not content:
                        # Try raw text extraction from SSE-like response
                        content = data.get("text", "")

                    return content

            except LLMError:
                raise
            except httpx.TimeoutException:
                if attempt < self.max_retries:
                    await asyncio.sleep(0.5 * (attempt + 1))
                    continue
                raise LLMError("Request timed out")
            except httpx.ConnectError:
                if attempt < self.max_retries:
                    await asyncio.sleep(0.5 * (attempt + 1))
                    continue
                raise LLMError("Connection failed")
            except Exception as exc:
                if attempt < self.max_retries:
                    await asyncio.sleep(0.5 * (attempt + 1))
                    continue
                raise LLMError(f"Request failed: {exc}")

        raise LLMError("LLM service unavailable after retries")
