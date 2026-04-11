#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
工具函数模块
提供学院检测、引用处理等实用功能
"""
import re
from typing import List, Dict, Optional, Tuple

# ========== 学院关键词映射 ==========
# 支持全称和简称，按匹配优先级排序（长的优先）
COLLEGE_KEYWORDS: List[Tuple[str, str]] = [
    # 研究生院
    ('研究生院', '研究生院'),
    # 学院全称
    ('经济管理学院', '经济管理学院'),
    ('材料科学与工程学院', '材料科学与工程学院'),
    ('航空制造工程学院', '航空制造工程学院'),
    ('航空制造与机械工程学院', '航空制造工程学院'),
    ('信息工程学院', '信息工程学院'),
    ('飞行器工程学院', '飞行器工程学院'),
    ('航空宇航学院', '飞行器工程学院'),
    ('环境与化学工程学院', '环境与化学工程学院'),
    ('软件学院', '软件学院'),
    ('外国语学院', '外国语学院'),
    ('数学与信息科学学院', '数学与信息科学学院'),
    ('土木建筑学院', '土木建筑学院'),
    ('体育学院', '体育学院'),
    ('马克思主义学院', '马克思主义学院'),
    ('艺术学院', '艺术学院'),
    ('航空服务与音乐学院', '航空服务与音乐学院'),
    ('创新创业学院', '创新创业学院'),
    ('继续教育学院', '继续教育学院'),
    ('国际教育学院', '国际教育学院'),
    # 学院简称
    ('经管院', '经济管理学院'),
    ('经管学院', '经济管理学院'),
    ('材料学院', '材料科学与工程学院'),
    ('航空制造学院', '航空制造工程学院'),
    ('信工学院', '信息工程学院'),
    ('信工院', '信息工程学院'),
    ('飞行器学院', '飞行器工程学院'),
    ('环化学院', '环境与化学工程学院'),
    ('环化院', '环境与化学工程学院'),
    ('软院', '软件学院'),
    ('外院', '外国语学院'),
    ('数信学院', '数学与信息科学学院'),
    ('数信院', '数学与信息科学学院'),
    ('土院', '土木建筑学院'),
    ('马院', '马克思主义学院'),
    ('艺院', '艺术学院'),
    ('航音院', '航空服务与音乐学院'),
]


def detect_college(messages: List[Dict]) -> Optional[str]:
    """
    从消息历史中检测用户所属学院

    采用倒序遍历策略，获取最新的学院声明

    Args:
        messages: 消息历史列表，每项包含role和content

    Returns:
        检测到的学院全称，如果没有则返回None

    Example:
        >>> messages = [{'role': 'user', 'content': '我是软件学院的'}]
        >>> detect_college(messages)
        '软件学院'
    """
    for msg in reversed(messages):
        if msg.get('role') == 'user':
            content = msg.get('content') or ''
            # 按顺序匹配，优先匹配长的关键词
            for keyword, full_name in COLLEGE_KEYWORDS:
                if keyword in content:
                    return full_name
    return None


def is_college_only_message(content: str, detected_college: Optional[str]) -> bool:
    """
    检测用户是否仅回复了学院信息（无其他实质问题）

    用于识别用户首次告知学院时的简短回复，避免AI回复过多学院介绍信息

    Args:
        content: 用户消息内容
        detected_college: 已检测到的学院名称

    Returns:
        True表示仅回复学院信息，False表示包含其他问题

    判定规则:
        1. 必须有检测到的学院
        2. 内容长度不超过30字符
        3. 包含学院关键词
        4. 包含确认词或内容较短
        5. 不包含疑问词
    """
    if not detected_college:
        return False

    clean_content = content.strip()

    # 内容过长，可能包含其他问题
    if len(clean_content) > 30:
        return False

    # 检测是否明确声明了学院归属（精确匹配学院名称）
    if detected_college:
        has_college = detected_college in clean_content
    else:
        has_college = False

    # 检测确认词
    confirm_words = ['我是', '对的', '是的', '没错', '正确', '嗯', '好', '好的']
    has_confirm = any(word in clean_content for word in confirm_words)

    # 检测疑问词
    question_words = ['什么', '怎么', '哪里', '为什么', '吗', '？', '?', '如何', '多少', '几']
    has_question = any(word in clean_content for word in question_words)

    return has_college and (has_confirm or len(clean_content) < 15) and not has_question


def is_first_conversation(messages: List[Dict]) -> bool:
    """
    判断是否为首次对话

    Args:
        messages: 消息历史列表

    Returns:
        True表示首次对话（只有一条用户消息），False表示非首次
    """
    user_messages = [msg for msg in messages if msg.get('role') == 'user']
    return len(user_messages) <= 1


def extract_citations(content: str) -> List[str]:
    """
    从内容中提取引用标记 [数字]

    Args:
        content: 内容文本

    Returns:
        引用编号列表（去重且保持顺序）
    """
    pattern = r'\[(\d+)\]'
    matches = re.findall(pattern, content)
    # 使用dict.fromkeys去重并保持顺序
    return list(dict.fromkeys(matches))


def convert_citations_to_links(content: str, citation_map: Dict[str, str]) -> str:
    """
    将 [数字] 格式的引用转换为 Markdown 链接格式

    Args:
        content: 原始内容
        citation_map: 引用编号到URL的映射 { "1": "https://...", ... }

    Returns:
        转换后的内容
    """
    def replace_citation(match):
        num = match.group(1)
        url = citation_map.get(num)
        if url:
            return f'[{num}]({url})'
        return match.group(0)

    return re.sub(r'\[(\d+)\]', replace_citation, content)


def extract_and_convert_citations(content: str, search_results: List[Dict] = None) -> Tuple[str, Dict[str, str]]:
    """
    提取引用并转换为链接

    Args:
        content: 原始内容
        search_results: 搜索结果列表（包含URL信息）

    Returns:
        (转换后的内容, 引用映射字典)
    """
    citations = extract_citations(content)
    citation_map = {}

    if search_results:
        for i, citation_num in enumerate(citations, 1):
            if i <= len(search_results):
                url = search_results[i-1].get('url', '')
                if url:
                    citation_map[citation_num] = url

    converted = convert_citations_to_links(content, citation_map)
    return converted, citation_map


def build_citation_map_from_search_results(search_results: List[Dict]) -> Dict[str, str]:
    """
    从搜索结果构建引用映射

    Args:
        search_results: 搜索结果列表，每项包含url或link字段

    Returns:
        引用编号到URL的映射字典
    """
    citation_map = {}
    for i, result in enumerate(search_results, 1):
        url = result.get('url') or result.get('link', '')
        if url:
            citation_map[str(i)] = url
    return citation_map


def sanitize_input(text: str, max_length: int = 2000) -> str:
    """
    清理用户输入，防止XSS和注入攻击

    Args:
        text: 原始输入文本
        max_length: 最大允许长度

    Returns:
        清理后的文本
    """
    if not text:
        return ''

    # 截断过长文本
    if len(text) > max_length:
        text = text[:max_length]

    # 移除潜在危险字符
    # 保留常见标点但移除控制字符
    text = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f]', '', text)

    return text.strip()


def truncate_messages(messages: List[Dict], max_messages: int = 10) -> List[Dict]:
    """
    截断消息历史，保留最近的消息

    Args:
        messages: 消息列表
        max_messages: 最大保留消息数

    Returns:
        截断后的消息列表
    """
    if len(messages) <= max_messages:
        return messages
    return messages[-max_messages:]
