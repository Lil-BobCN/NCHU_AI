#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
搜索关键词提取模块
从 DashScope web_search_call 事件中提取关键词标签
"""
import json
from typing import List, Dict, Any, Optional


def extract_search_keywords(web_search_event: Dict[str, Any]) -> List[str]:
    """
    从 web_search_call 事件中提取搜索关键词

    Args:
        web_search_event: DashScope web_search_call 事件数据

    Returns:
        关键词列表，最多返回 8 个
    """
    keywords = []

    # 从 search_plan 中提取关键词
    search_plan = web_search_event.get('search_plan', {})
    if isinstance(search_plan, dict):
        plan_keywords = search_plan.get('keywords', [])
        if isinstance(plan_keywords, list):
            keywords.extend(plan_keywords)

    # 从 search_results 中提取相关关键词（标题中的关键词）
    search_results = web_search_event.get('search_results', [])
    if isinstance(search_results, list):
        # 从结果标题中提取补充关键词，最多补充到 8 个
        for result in search_results:
            if len(keywords) >= 8:
                break
            title = result.get('title', '')
            if title and title not in keywords:
                # 取标题前 10 个字符作为补充关键词
                keyword = title[:10].strip()
                if keyword and keyword not in keywords:
                    keywords.append(keyword)

    # 去重并保持顺序
    seen = set()
    unique_keywords = []
    for kw in keywords:
        if kw and kw not in seen:
            seen.add(kw)
            unique_keywords.append(kw)

    return unique_keywords[:8]


def format_search_event(keywords: List[str], count: int) -> str:
    """
    格式化为前端可消费的 SSE 事件

    Args:
        keywords: 关键词列表
        count: 搜索结果数量

    Returns:
        SSE 事件字符串
    """
    event_data = {
        'type': 'search_keywords',
        'keywords': keywords,
        'count': count
    }
    return f'data: {json.dumps(event_data, ensure_ascii=False)}\n\n'
