#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
缓存系统 - 支持Redis和内存缓存
提供智能的缓存策略和过期机制
"""
import hashlib
import time
from typing import Optional, Dict, Any


class CacheManager:
    """缓存管理器 - 支持多级缓存策略"""

    def __init__(self, config: Dict[str, Any]):
        """
        初始化缓存管理器

        Args:
            config: 配置字典，包含enabled, ttl, max_size等
        """
        self.config = config
        self.redis_client = None
        self.memory_cache: Dict[str, Dict] = {}  # 包含过期时间的存储
        self.enabled = config.get('enabled', True)
        self.ttl = config.get('ttl', 3600)  # 默认1小时
        self.max_size = config.get('max_size', 100)

        if self.enabled:
            self._init_redis()

    def _init_redis(self):
        """尝试初始化Redis连接"""
        try:
            import redis
            redis_host = self.config.get('redis_host', 'localhost')
            redis_port = self.config.get('redis_port', 6379)
            redis_db = self.config.get('redis_db', 0)

            self.redis_client = redis.Redis(
                host=redis_host,
                port=redis_port,
                db=redis_db,
                socket_connect_timeout=3,
                socket_timeout=3,
                decode_responses=True
            )
            # 测试连接
            self.redis_client.ping()
            print(f"[CACHE] Redis连接成功: {redis_host}:{redis_port}/{redis_db}")
        except Exception as e:
            print(f"[CACHE] Redis连接失败，使用内存缓存: {e}")
            self.redis_client = None

    def _get_cache_key(self, query: str, college: Optional[str] = None) -> str:
        """
        生成缓存键

        Args:
            query: 查询内容
            college: 学院名称（可选）

        Returns:
            MD5哈希后的缓存键
        """
        key_str = f"{query}_{college or 'general'}_v2"  # v2版本号，用于强制刷新
        return hashlib.md5(key_str.encode('utf-8')).hexdigest()

    def _is_expired(self, entry: Dict) -> bool:
        """检查缓存条目是否过期"""
        return time.time() > entry.get('expire_at', 0)

    def _cleanup_memory_cache(self):
        """清理过期的内存缓存条目"""
        expired_keys = [
            k for k, v in self.memory_cache.items()
            if self._is_expired(v)
        ]
        for k in expired_keys:
            del self.memory_cache[k]

    def _evict_oldest(self):
        """淘汰最旧的缓存条目（LRU策略）"""
        if len(self.memory_cache) >= self.max_size:
            # 按访问时间排序，淘汰最旧的
            sorted_items = sorted(
                self.memory_cache.items(),
                key=lambda x: x[1].get('access_time', 0)
            )
            # 移除20%最旧的条目
            to_remove = int(self.max_size * 0.2) or 1
            for key, _ in sorted_items[:to_remove]:
                del self.memory_cache[key]

    def get(self, query: str, college: Optional[str] = None) -> Optional[str]:
        """
        获取缓存的响应

        Args:
            query: 查询内容
            college: 学院名称

        Returns:
            缓存的响应内容，如果没有或已过期则返回None
        """
        if not self.enabled:
            return None

        key = self._get_cache_key(query, college)

        # 优先从Redis获取
        if self.redis_client:
            try:
                value = self.redis_client.get(key)
                if value:
                    return value
            except Exception as e:
                print(f"[CACHE] Redis读取失败: {e}")

        # 从内存缓存获取
        entry = self.memory_cache.get(key)
        if entry and not self._is_expired(entry):
            entry['access_time'] = time.time()  # 更新访问时间
            return entry.get('value')

        # 清理过期条目
        if entry and self._is_expired(entry):
            del self.memory_cache[key]

        return None

    def set(self, query: str, response: str, college: Optional[str] = None):
        """
        设置缓存响应

        Args:
            query: 查询内容
            response: 响应内容
            college: 学院名称
        """
        if not self.enabled or not response:
            return

        key = self._get_cache_key(query, college)

        # 写入Redis
        if self.redis_client:
            try:
                self.redis_client.setex(key, self.ttl, response)
                return
            except Exception as e:
                print(f"[CACHE] Redis写入失败: {e}")

        # 写入内存缓存
        self._cleanup_memory_cache()
        self._evict_oldest()

        self.memory_cache[key] = {
            'value': response,
            'expire_at': time.time() + self.ttl,
            'access_time': time.time()
        }

    def clear(self):
        """清除所有缓存"""
        if self.redis_client:
            try:
                self.redis_client.flushdb()
            except Exception as e:
                print(f"[CACHE] Redis清空失败: {e}")

        self.memory_cache.clear()
        print("[CACHE] 缓存已清除")

    def get_stats(self) -> Dict[str, Any]:
        """获取缓存统计信息"""
        stats = {
            'enabled': self.enabled,
            'ttl': self.ttl,
            'memory_cache_size': len(self.memory_cache),
            'redis_connected': self.redis_client is not None
        }
        return stats


# 全局缓存实例
cache_manager: Optional[CacheManager] = None


def init_cache(config: Dict[str, Any]) -> CacheManager:
    """
    初始化全局缓存

    Args:
        config: 缓存配置

    Returns:
        CacheManager实例
    """
    global cache_manager
    cache_manager = CacheManager(config)
    return cache_manager


def get_cache() -> Optional[CacheManager]:
    """获取缓存实例"""
    return cache_manager
