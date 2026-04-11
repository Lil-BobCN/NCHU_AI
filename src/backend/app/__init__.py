#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Flask 应用初始化
"""
import os
import sys
from datetime import timedelta
from flask import Flask, jsonify
from flask_cors import CORS

# 添加项目根目录到路径
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(os.path.dirname(current_dir))
if project_root not in sys.path:
    sys.path.insert(0, project_root)


def create_app(config=None):
    """
    创建 Flask 应用

    Args:
        config: 配置字典或配置对象，可选

    Returns:
        Flask 应用实例
    """
    app = Flask(__name__)

    # Session 配置
    secret_key = os.getenv('SESSION_SECRET_KEY')
    if not secret_key:
        raise RuntimeError(
            'SESSION_SECRET_KEY 环境变量未设置。请在 .env 文件中配置一个随机字符串。'
        )
    app.secret_key = secret_key
    app.config['SESSION_COOKIE_HTTPONLY'] = True
    app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
    app.config['SESSION_COOKIE_PATH'] = '/'
    try:
        session_hours = int(os.getenv('SESSION_LIFETIME_HOURS', '24'))
    except (ValueError, TypeError):
        session_hours = 24
    app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(hours=session_hours)

    # 从环境变量加载CORS配置
    cors_origins = os.getenv('CORS_ORIGINS', '*')
    if cors_origins != '*':
        cors_origins = cors_origins.split(',')

    # 配置CORS
    CORS(app, resources={
        r"/api/*": {
            "origins": cors_origins,
            "methods": ["GET", "POST", "OPTIONS"],
            "allow_headers": ["Content-Type", "Authorization"],
            "supports_credentials": True
        },
        r"/health": {
            "origins": "*"
        }
    })

    # 初始化缓存
    try:
        from config.default import CACHE_CONFIG
        from app.cache import init_cache
        init_cache(CACHE_CONFIG)
    except Exception as e:
        print(f"[WARNING] 缓存初始化失败: {e}")

    # 注册蓝图
    from app.routes import api_bp
    app.register_blueprint(api_bp)

    # 注册认证蓝图
    from app.auth import auth_bp
    app.register_blueprint(auth_bp)

    # 注册错误处理器
    register_error_handlers(app)

    return app


def register_error_handlers(app):
    """注册全局错误处理器"""

    @app.errorhandler(404)
    def not_found(error):
        return jsonify({'error': '接口不存在', 'code': 404}), 404

    @app.errorhandler(405)
    def method_not_allowed(error):
        return jsonify({'error': '请求方法不允许', 'code': 405}), 405

    @app.errorhandler(500)
    def internal_error(error):
        return jsonify({'error': '服务器内部错误', 'code': 500}), 500

    @app.errorhandler(Exception)
    def handle_exception(error):
        app.logger.error(f"Unhandled error: {error}", exc_info=True)
        return jsonify({'error': '服务器内部错误', 'code': 500}), 500
