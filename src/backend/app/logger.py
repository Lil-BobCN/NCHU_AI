#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
日志配置模块 - 统一的日志管理
"""
import os
import logging
from logging.handlers import RotatingFileHandler
from datetime import datetime


def setup_logger(name: str = 'ai_assistant') -> logging.Logger:
    """
    设置并返回配置好的日志记录器

    Args:
        name: 日志记录器名称

    Returns:
        配置好的Logger实例
    """
    logger = logging.getLogger(name)

    # 如果已经配置过，直接返回
    if logger.handlers:
        return logger

    # 从环境变量获取日志级别
    log_level = os.getenv('LOG_LEVEL', 'INFO').upper()
    logger.setLevel(getattr(logging, log_level, logging.INFO))

    # 日志格式
    formatter = logging.Formatter(
        '[%(asctime)s] [%(levelname)s] %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

    # 控制台处理器
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    # 文件处理器（如果配置了日志文件路径）
    log_file = os.getenv('LOG_FILE')
    if log_file:
        # 确保日志目录存在
        log_dir = os.path.dirname(log_file)
        if log_dir and not os.path.exists(log_dir):
            os.makedirs(log_dir, exist_ok=True)

        file_handler = RotatingFileHandler(
            log_file,
            maxBytes=10*1024*1024,  # 10MB
            backupCount=5,
            encoding='utf-8'
        )
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

    return logger


def get_logger(name: str = 'ai_assistant') -> logging.Logger:
    """获取日志记录器"""
    return logging.getLogger(name)


# 兼容旧版的日志函数（用于routes.py中的log_debug）
class DebugLogger:
    """调试日志兼容类"""

    def __init__(self):
        self.logger = setup_logger()
        # 为兼容性保留文件日志
        self.log_file = os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
            'logs', 'api_debug.log'
        )
        os.makedirs(os.path.dirname(self.log_file), exist_ok=True)

    def __call__(self, message: str):
        """写入调试日志"""
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        log_line = f"[{timestamp}] {message}\n"

        # 写入文件
        try:
            with open(self.log_file, 'a', encoding='utf-8') as f:
                f.write(log_line)
        except Exception as e:
            self.logger.error(f"写入日志文件失败: {e}")

        # 同时输出到控制台
        self.logger.info(message)


# 创建全局调试日志实例
log_debug = DebugLogger()
