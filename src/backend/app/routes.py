#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
API 路由定义
提供AI聊天接口、健康检查和配置获取功能
"""
import json
import re
import time
from datetime import datetime
from flask import Blueprint, request, Response, stream_with_context, jsonify

from config.default import RATE_LIMIT, COLLEGE_LOCK_CONFIG
from config.prompts import (
    MAIN_INSTRUCTIONS,
    FIRST_MESSAGE_INSTRUCTIONS,
    CITATION_FORMAT_INSTRUCTION
)
from app.cache import get_cache
from app.utils import (
    detect_college,
    is_first_conversation,
    is_college_only_message
)
from app.qwen_api import get_qwen_api
from app.auth import login_required
from app.logger import log_debug

api_bp = Blueprint('api', __name__)


def create_sse_response(generator):
    """
    创建SSE流式响应

    Args:
        generator: 数据生成器

    Returns:
        Flask Response对象
    """
    return Response(
        stream_with_context(generator),
        mimetype='text/event-stream',
        headers={
            'Cache-Control': 'no-cache',
            'X-Accel-Buffering': 'no',
            'Connection': 'keep-alive'
        }
    )


@api_bp.route('/api/chat', methods=['POST', 'OPTIONS'])
@login_required
def chat():
    """
    对话接口 - 处理AI聊天请求

    请求体格式:
    {
        "messages": [
            {"role": "user", "content": "..."},
            {"role": "assistant", "content": "..."}
        ],
        "chat_id": "unique-chat-id"
    }

    返回: SSE流式响应
    """
    # 处理预检请求
    if request.method == 'OPTIONS':
        return '', 204

    try:
        # 解析请求数据
        data = request.get_json()
        if not data:
            return jsonify({'error': '请求体不能为空'}), 400

        messages = data.get('messages', [])
        chat_id = data.get('chat_id', '')

        if not messages:
            return jsonify({'error': 'messages不能为空'}), 400

        # 获取最后一条用户消息
        user_messages = [m for m in messages if m.get('role') == 'user']
        if not user_messages:
            return jsonify({'error': '没有用户消息'}), 400

        user_query = user_messages[-1].get('content', '')

        # 检测学院信息
        detected_college = detect_college(messages)
        is_first = is_first_conversation(messages)

        log_debug(f"[CHAT] 新请求 | chat_id: {chat_id} | "
                  f"学院: {detected_college or '未检测'} | 首次: {is_first}")

        # ========== 学院信息锁定逻辑 ==========
        if COLLEGE_LOCK_CONFIG['enabled'] and is_college_only_message(user_query, detected_college):
            forced_response = COLLEGE_LOCK_CONFIG['forced_response']
            log_debug(f"[COLLEGE_LOCK] 检测到学院信息，返回固定回复")

            def college_stream():
                yield f'data: {json.dumps({"choices": [{"delta": {"content": forced_response}}]})}\n\n'

            return create_sse_response(college_stream())

        # ========== 缓存检查 ==========
        cache = get_cache()
        if cache:
            cached_response = cache.get(user_query, detected_college)
            if cached_response:
                log_debug(f"[CACHE] 命中缓存")

                def cached_stream():
                    yield f'data: {json.dumps({"choices": [{"delta": {"content": cached_response}}]})}\n\n'

                return create_sse_response(cached_stream())

        # ========== 选择系统指令 ==========
        if is_first and not detected_college:
            instructions = FIRST_MESSAGE_INSTRUCTIONS
        else:
            college_hint = f"\n\n【用户所属学院】{detected_college}（仅用于个性化回答）" if detected_college else ""
            instructions = MAIN_INSTRUCTIONS + CITATION_FORMAT_INSTRUCTION + college_hint

        # ========== 构建API请求 ==========
        qwen_api = get_qwen_api()
        payload = qwen_api.build_payload(
            messages=messages,
            user_query=user_query,
            detected_college=detected_college,
            is_first_msg=is_first,
            instructions=instructions
        )

        # ========== 流式响应处理 ==========
        def generate():
            full_response = []
            start_time = time.time()
            search_results = []
            citation_map = {}
            sent_citation_keys = set()  # 已发送的引用键，避免重复

            try:
                for line in qwen_api.stream_chat(payload):
                    # 解析SSE数据提取搜索结果和引用信息
                    if line.startswith('data:'):
                        try:
                            data_str = line[5:].strip()
                            data = json.loads(data_str)

                            # 提取搜索结果
                            if 'output' in data and isinstance(data['output'], list):
                                for item in data['output']:
                                    if item.get('type') == 'search_result':
                                        url = item.get('url', '')
                                        title = item.get('title', '')
                                        if url and not any(r['url'] == url for r in search_results):
                                            search_results.append({'url': url, 'title': title})

                            # 提取引用信息（从API原生citations字段）
                            choices = data.get('choices', [])
                            if choices:
                                delta = choices[0].get('delta', {})
                                if 'citations' in delta:
                                    for cite in delta['citations']:
                                        url = cite.get('url', '')
                                        num = cite.get('index', len(citation_map) + 1)
                                        if url:
                                            citation_map[str(num)] = {
                                                'url': url,
                                                'title': cite.get('title', '')
                                            }

                                # 从内容中提取脚注引用定义（优先 [^数字]: URL，兼容 [数字]: URL）
                                content = delta.get('content', '')
                                if content:
                                    footnote_pattern = r'\[\^(\d+)\]:\s*(https?://[^\s\n]+)(?:\s*[-–—]\s*([^\n]*?))?$'
                                    for match in re.finditer(footnote_pattern, content, re.MULTILINE):
                                        num = match.group(1)
                                        url = match.group(2).rstrip('.,;:!?)')
                                        title = (match.group(3) or '').strip()
                                        if url and num not in citation_map:
                                            citation_map[num] = {'url': url, 'title': title}

                                    alt_pattern = r'^\[(\d+)\]:\s*(https?://[^\s\n]+)(?:\s*[-–—]\s*([^\n]*?))?$'
                                    for match in re.finditer(alt_pattern, content, re.MULTILINE):
                                        num = match.group(1)
                                        url = match.group(2).rstrip('.,;:!?)')
                                        title = (match.group(3) or '').strip()
                                        if url and num not in citation_map:
                                            citation_map[num] = {'url': url, 'title': title}

                        except json.JSONDecodeError:
                            pass
                        except Exception as e:
                            log_debug(f"[PARSE_ERROR] 解析行失败: {e}")

                    # 拦截上游 [DONE]，不转发
                    data_str = line[5:].strip() if line.startswith('data:') else ''
                    if data_str == '[DONE]':
                        log_debug("[STREAM] 拦截上游 [DONE]，延迟到引用数据之后发送")
                        continue

                    yield line

                    # 提取内容用于缓存
                    try:
                        if line.startswith('data:'):
                            data = json.loads(line[5:].strip())
                            delta = data.get('choices', [{}])[0].get('delta', {})
                            content = delta.get('content', '')
                            if content:
                                full_response.append(content)
                    except Exception:
                        pass

                    # ========== 实时发送新发现的引用映射 ==========
                    # 每当有新的引用被发现，立即发送给前端
                    new_citations = {}
                    for key, val in citation_map.items():
                        if key not in sent_citation_keys:
                            new_citations[key] = val
                            sent_citation_keys.add(key)

                    # 同时检查搜索结果是否有新的
                    for idx, result in enumerate(search_results, 1):
                        key = str(idx)
                        if key not in sent_citation_keys and result.get('url'):
                            new_citations[key] = {
                                'url': result['url'],
                                'title': result.get('title', '')
                            }
                            sent_citation_keys.add(key)

                    if new_citations:
                        yield f'data: {json.dumps({"citations": new_citations})}\n\n'

                # ========== 流结束后：发送参考链接文本和最终引用汇总 ==========
                final_citation_map = {}

                for idx, result in enumerate(search_results, 1):
                    url = result.get('url', '')
                    if url:
                        final_citation_map[str(idx)] = {
                            'url': url,
                            'title': result.get('title', '')
                        }

                for num, cite in citation_map.items():
                    if num not in final_citation_map:
                        final_citation_map[num] = cite

                # 从完整响应文本中再次提取脚注引用（兜底）
                if full_response:
                    full_text = ''.join(full_response)
                    footnote_pattern = r'\[\^(\d+)\]:\s*(https?://[^\s\n]+)(?:\s*[-–—]\s*([^\n]*?))?$'
                    for match in re.finditer(footnote_pattern, full_text, re.MULTILINE):
                        num = match.group(1)
                        url = match.group(2).rstrip('.,;:!?)')
                        title = (match.group(3) or '').strip()
                        if url and num not in final_citation_map:
                            final_citation_map[num] = {'url': url, 'title': title}
                    alt_pattern = r'^\[(\d+)\]:\s*(https?://[^\s\n]+)(?:\s*[-–—]\s*([^\n]*?))?$'
                    for match in re.finditer(alt_pattern, full_text, re.MULTILINE):
                        num = match.group(1)
                        url = match.group(2).rstrip('.,;:!?)')
                        title = (match.group(3) or '').strip()
                        if url and num not in final_citation_map:
                            final_citation_map[num] = {'url': url, 'title': title}

                # 发送参考链接文本 + 最终引用汇总 + [DONE]
                if final_citation_map:
                    citations_text = "\n\n## 参考链接\n"
                    sorted_nums = sorted(
                        final_citation_map.keys(),
                        key=lambda x: int(x) if x.isdigit() else 999
                    )
                    for num in sorted_nums:
                        cite = final_citation_map[num]
                        url = cite.get('url', '')
                        title = cite.get('title', '')
                        if url:
                            citations_text += f"[^{num}]: {url} - {title}\n"

                    yield f'data: {json.dumps({"choices": [{"delta": {"content": citations_text}}]})}\n\n'
                    yield f'data: {json.dumps({"citations": final_citation_map, "done": True})}\n\n'
                    log_debug(f"[CITATION] 最终引用汇总 {len(final_citation_map)} 个")

                yield 'data: [DONE]\n\n'

                # 保存到缓存
                if cache and full_response:
                    final_response = ''.join(full_response)
                    cache.set(user_query, final_response, detected_college)

                elapsed = time.time() - start_time
                log_debug(f"[COMPLETE] 响应完成，耗时: {elapsed:.2f}s")

            except Exception as e:
                log_debug(f"[STREAM_ERROR] 流处理错误: {e}")
                yield f'data: {json.dumps({"error": str(e)})}\n\n'

        return create_sse_response(generate())

    except Exception as e:
        log_debug(f"[ERROR] 处理请求失败: {e}")
        return jsonify({'error': str(e)}), 500


@api_bp.route('/health', methods=['GET'])
def health_check():
    """
    健康检查接口

    用于监控系统和服务状态检查
    """
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'service': 'ai-assistant-api'
    })


@api_bp.route('/api/config', methods=['GET'])
def get_config():
    """
    获取配置接口

    返回前端需要的配置信息
    """
    return jsonify({
        'rate_limit': RATE_LIMIT,
        'college_lock': COLLEGE_LOCK_CONFIG['enabled'],
        'enable_thinking': False
    })
