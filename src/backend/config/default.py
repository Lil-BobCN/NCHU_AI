#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
默认配置文件
从环境变量加载配置，提供合理的默认值
"""
import os
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

# ========== 服务器配置 ==========
SERVER_CONFIG = {
    'host': os.getenv('HOST', '0.0.0.0'),
    'port': int(os.getenv('PORT', '5000')),
    'debug': os.getenv('DEBUG', 'False').lower() == 'true'
}

# ========== 缓存配置 ==========
CACHE_CONFIG = {
    'enabled': os.getenv('CACHE_ENABLED', 'true').lower() == 'true',
    'ttl': int(os.getenv('CACHE_TTL', '3600')),  # 缓存有效期：1小时
    'max_size': int(os.getenv('CACHE_MAX_SIZE', '100')),  # 内存缓存最大条目数
    'redis_host': os.getenv('REDIS_HOST', 'localhost'),
    'redis_port': int(os.getenv('REDIS_PORT', '6379')),
    'redis_db': int(os.getenv('REDIS_DB', '0'))
}

# ========== 速率限制配置 ==========
RATE_LIMIT = {
    'max_requests_per_minute': int(os.getenv('RATE_LIMIT_PER_MINUTE', '60')),
    'max_requests_per_hour': int(os.getenv('RATE_LIMIT_PER_HOUR', '1000'))
}

# ========== 通义千问 API 配置 ==========
QWEN_API_CONFIG = {
    'api_key': os.getenv('QWEN_API_KEY', ''),
    'api_base_url': os.getenv(
        'QWEN_API_BASE_URL',
        'https://dashscope.aliyuncs.com/compatible-mode/v1'
    ),
    'model': os.getenv('QWEN_MODEL', 'qwen3.5-plus'),
    'enable_thinking': False  # 强制禁用深度思考，提升响应速度
}

# ========== 工具配置 ==========
# 仅保留web_search，移除可能拖慢响应的其他工具
TOOLS_CONFIG = [
    {'type': 'web_search'}  # 联网搜索工具
]

# ========== 请求配置 ==========
REQUEST_CONFIG = {
    'retry_total': int(os.getenv('RETRY_TOTAL', '2')),
    'retry_backoff_factor': float(os.getenv('RETRY_BACKOFF_FACTOR', '0.5')),
    'pool_connections': int(os.getenv('POOL_CONNECTIONS', '10')),
    'pool_maxsize': int(os.getenv('POOL_MAXSIZE', '20')),
    'timeout': int(os.getenv('REQUEST_TIMEOUT', '60'))  # 请求超时时间
}

# ========== 学院信息锁定配置 ==========
COLLEGE_LOCK_CONFIG = {
    'enabled': True,
    'forced_response': '好的，我已了解您的学院信息，请提问。',
    'max_message_length': 30  # 判定为学院信息的最大消息长度
}

# ========== 引用链接配置 ==========
CITATION_CONFIG = {
    'enabled': True,
    'pattern': r'\[\^(\d+)\]',  # 匹配 Markdown 脚注格式 [^数字]
    'template': '[^{num}]({url})',  # 转换为Markdown链接格式
    'strict_mode': True  # 严格模式：无真实URL时不生成链接
}

# ========== 学院列表 ==========
COLLEGES = [
    '经济管理学院',
    '材料科学与工程学院',
    '航空制造工程学院',
    '信息工程学院',
    '飞行器工程学院',
    '环境与化学工程学院',
    '软件学院',
    '外国语学院',
    '数学与信息科学学院',
    '土木建筑学院',
    '体育学院',
    '马克思主义学院',
    '艺术学院',
    '航空服务与音乐学院',
    '创新创业学院',
    '继续教育学院',
    '国际教育学院',
    '研究生院'
]
