#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
通义千问 API 封装
提供与阿里云DashScope API的交互功能
"""
import json
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from typing import List, Dict, Optional, Generator

from config.default import QWEN_API_CONFIG, TOOLS_CONFIG, REQUEST_CONFIG
from app.logger import log_debug


class QwenAPIError(Exception):
    """通义千问API错误"""
    pass


class QwenAPI:
    """通义千问 API 客户端"""

    def __init__(self):
        self.config = QWEN_API_CONFIG
        self.session = self._create_session()
        self._validate_config()

    def _validate_config(self):
        """验证配置是否完整"""
        if not self.config.get('api_key'):
            raise QwenAPIError("API密钥未配置，请设置QWEN_API_KEY环境变量")

    def _create_session(self) -> requests.Session:
        """创建带连接池和重试机制的Session"""
        session = requests.Session()

        retry_strategy = Retry(
            total=REQUEST_CONFIG['retry_total'],
            backoff_factor=REQUEST_CONFIG['retry_backoff_factor'],
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["POST", "GET"]
        )

        adapter = HTTPAdapter(
            pool_connections=REQUEST_CONFIG['pool_connections'],
            pool_maxsize=REQUEST_CONFIG['pool_maxsize'],
            max_retries=retry_strategy
        )

        session.mount("https://", adapter)
        session.mount("http://", adapter)

        return session

    def build_payload(
        self,
        messages: List[Dict],
        user_query: str,
        detected_college: Optional[str] = None,
        is_first_msg: bool = False,
        instructions: str = ""
    ) -> Dict:
        """
        构建 API 请求体

        Args:
            messages: 历史消息
            user_query: 当前用户查询
            detected_college: 检测到的学院
            is_first_msg: 是否为首次消息
            instructions: 系统指令

        Returns:
            API 请求体字典
        """
        # 截取最近的历史消息（限制上下文长度，提升响应速度）
        recent_history = messages[:-1] if len(messages) > 1 else []
        if len(recent_history) > 3:
            recent_history = recent_history[-3:]

        # 构建input字段
        if recent_history:
            input_messages = [
                {'role': msg['role'], 'content': msg.get('content', '')}
                for msg in recent_history
                if msg.get('role') in ['user', 'assistant']
            ]
            input_messages.append({'role': 'user', 'content': user_query})
            input_data = input_messages
        else:
            input_data = user_query

        # 构建请求体
        payload = {
            'model': self.config['model'],
            'input': input_data,
            'instructions': instructions,
            'tools': TOOLS_CONFIG,
            'stream': True,
            'enable_thinking': False,  # 禁用深度思考，提升响应速度
            'temperature': 0.7,        # 适中温度值，平衡质量与速度
            'max_tokens': 1500,        # 限制最大输出，避免过长响应
        }

        log_debug(f"[API] 构建请求 | 模型: {self.config['model']} | "
                  f"历史消息数: {len(recent_history)}")

        return payload

    def _iter_sse_lines(self, response) -> Generator[str, None, None]:
        """
        安全迭代 SSE 行，避免 UTF-8 多字节字符在字节边界处被截断

        BUG-001 修复: 原 iter_lines() 在字节边界截断中文等多字节字符，
        导致下游收到的 SSE 数据中中文字符损坏。改用 iter_content(decode_unicode=True)
        确保字符级别的完整性。
        """
        buffer = ''
        for chunk in response.iter_content(chunk_size=4096, decode_unicode=True):
            if chunk is None:
                break
            buffer += chunk
            while '\n' in buffer:
                line, buffer = buffer.split('\n', 1)
                line = line.strip()
                if line and line.startswith('data:'):
                    yield line + '\n\n'
        # 处理缓冲区剩余数据
        if buffer.strip():
            line = buffer.strip()
            if line.startswith('data:'):
                yield line + '\n\n'

    def parse_sse_event(self, line: str) -> Optional[Dict]:
        """
        解析单条 SSE 数据行为 JSON 对象

        Args:
            line: 原始 SSE 行（包含 'data: ' 前缀）

        Returns:
            解析后的字典，解析失败返回 None
        """
        try:
            data_str = line[5:].strip()
            if data_str == '[DONE]':
                return {'__done__': True}
            return json.loads(data_str)
        except (json.JSONDecodeError, ValueError):
            return None

    def stream_chat(
        self,
        payload: Dict
    ) -> Generator[str, None, None]:
        """
        流式对话

        Args:
            payload: 请求体

        Yields:
            SSE 格式的数据行（包含 'data: ' 前缀和 '\\n\\n' 后缀）

        Raises:
            QwenAPIError: API调用失败
        """
        headers = {
            'Authorization': f"Bearer {self.config['api_key']}",
            'Content-Type': 'application/json',
            'Accept': 'text/event-stream'
        }

        url = f"{self.config['api_base_url']}/responses"

        try:
            log_debug(f"[API] 发送请求到 {url}")

            response = self.session.post(
                url,
                headers=headers,
                json=payload,
                stream=True,
                timeout=REQUEST_CONFIG['timeout']
            )

            # 检查HTTP错误
            if not response.ok:
                error_msg = f"API请求失败: HTTP {response.status_code}"
                try:
                    error_data = response.json()
                    if 'error' in error_data:
                        error_msg = f"{error_msg} - {error_data['error']}"
                except Exception:
                    error_msg = f"{error_msg} - {response.text[:200]}"

                raise QwenAPIError(error_msg)

            # 流式读取响应（使用修复后的 UTF-8 安全迭代器）
            yield from self._iter_sse_lines(response)

        except requests.exceptions.Timeout:
            log_debug("[API_ERROR] 请求超时")
            yield f'data: {json.dumps({"error": "请求超时，请稍后重试"})}\n\n'
        except requests.exceptions.ConnectionError:
            log_debug("[API_ERROR] 连接失败")
            yield f'data: {json.dumps({"error": "网络连接失败，请检查网络"})}\n\n'
        except QwenAPIError as e:
            log_debug(f"[API_ERROR] {e}")
            yield f'data: {json.dumps({"error": str(e)})}\n\n'
        except Exception as e:
            log_debug(f"[API_ERROR] 未知错误: {e}")
            yield f'data: {json.dumps({"error": "请求失败: " + str(e)})}\n\n'


# 全局 API 实例（懒加载）
_qwen_api = None


def get_qwen_api() -> QwenAPI:
    """
    获取 Qwen API 实例（单例模式）

    Returns:
        QwenAPI实例
    """
    global _qwen_api
    if _qwen_api is None:
        _qwen_api = QwenAPI()
    return _qwen_api


def reset_qwen_api():
    """重置API实例（用于测试或重新配置）"""
    global _qwen_api
    _qwen_api = None
