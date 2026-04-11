#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
用户认证模块
提供注册、登录、登出功能，使用 Redis 存储用户数据 + Flask Session 认证
"""
import hashlib
import os
import re
import time
import json
import secrets
from functools import wraps
from flask import Blueprint, request, jsonify, session
from werkzeug.security import generate_password_hash, check_password_hash

from app.cache import get_cache
from app.logger import log_debug

auth_bp = Blueprint('auth', __name__)

# 管理员用户列表（模块加载时缓存）
_ADMIN_USERS = frozenset(
    u.strip() for u in os.getenv('ADMIN_USERS', '').split(',') if u.strip()
)


def _hash_password(password: str) -> str:
    """
    对密码进行 scrypt 哈希

    Args:
        password: 原始密码

    Returns:
        哈希值字符串
    """
    return generate_password_hash(password, method='scrypt')


def _get_user_key(identifier: str) -> str:
    """生成用户存储键"""
    return f"user:{identifier}"


def _get_user_by_field(field: str, value: str):
    """
    根据字段查找用户

    Args:
        field: 字段名 (username 或 email)
        value: 字段值

    Returns:
        用户字典或 None
    """
    cache = get_cache()
    if not cache or not cache.redis_client:
        return None

    redis_client = cache.redis_client
    # 通过索引查找
    index_key = f"user_index:{field}:{value}"
    username = redis_client.get(index_key)
    if not username:
        return None

    user_data = redis_client.get(_get_user_key(username))
    if not user_data:
        return None

    return json.loads(user_data)


def login_required(f):
    """
    登录验证装饰器

    检查 session 中是否存在 user_id，未登录返回 401
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return jsonify({
                'error': '请先登录',
                'code': 401,
                'need_login': True
            }), 401
        return f(*args, **kwargs)
    return decorated_function


@auth_bp.route('/api/auth/register', methods=['POST'])
def register():
    """
    用户注册接口

    请求体:
    {
        "username": "用户名",
        "password": "密码",
        "email": "邮箱（可选）",
        "student_id": "学号（可选）"
    }

    返回:
    {
        "success": true,
        "user": { "username": "...", "email": "..." }
    }
    """
    cache = get_cache()
    if not cache or not cache.redis_client:
        return jsonify({'error': '存储服务不可用', 'code': 503}), 503

    data = request.get_json()
    if not data:
        return jsonify({'error': '请求体不能为空'}), 400

    username = (data.get('username') or '').strip()
    password = data.get('password', '')
    email = (data.get('email') or '').strip()
    student_id = (data.get('student_id') or '').strip()

    # 验证输入
    if not username:
        return jsonify({'error': '用户名不能为空'}), 400
    if len(username) < 2 or len(username) > 30:
        return jsonify({'error': '用户名长度为 2-30 个字符'}), 400
    if not re.match(r'^[a-zA-Z0-9_\u4e00-\u9fff-]+$', username):
        return jsonify({'error': '用户名只能包含字母、数字、汉字、下划线和连字符'}), 400
    # 密码强度校验
    if len(password) < 8:
        return jsonify({'error': '密码至少 8 个字符'}), 400
    if password == username:
        return jsonify({'error': '密码不能与用户名相同'}), 400
    if len(password) > 128:
        return jsonify({'error': '密码不能超过 128 个字符'}), 400
    if email and '@' not in email:
        return jsonify({'error': '邮箱格式不正确'}), 400

    redis_client = cache.redis_client

    # 检查用户名是否已存在
    if redis_client.exists(_get_user_key(username)):
        return jsonify({'error': '用户名已存在'}), 409
    if email and redis_client.get(f"user_index:email:{email}"):
        return jsonify({'error': '邮箱已被注册'}), 409

    # 创建用户
    hashed = _hash_password(password)
    user = {
        'username': username,
        'email': email,
        'student_id': student_id,
        'password_hash': hashed,
        'created_at': time.time(),
    }

    # 原子性创建用户（SET NX = set-if-not-exists）
    ok = redis_client.set(_get_user_key(username), json.dumps(user), nx=True)
    if not ok:
        return jsonify({'error': '用户名已存在'}), 409

    # 只有用户创建成功才设置索引
    redis_client.set(f"user_index:username:{username}", username)
    if email:
        redis_client.set(f"user_index:email:{email}", username)

    log_debug(f"[AUTH] 用户注册成功: {username}")

    # 注册后自动登录
    session['user_id'] = username
    session.permanent = True

    return jsonify({
        'success': True,
        'user': {
            'username': username,
            'email': email,
            'student_id': student_id,
        }
    }), 201


@auth_bp.route('/api/auth/login', methods=['POST'])
def login():
    """
    用户登录接口

    请求体:
    {
        "username": "用户名",
        "password": "密码"
    }

    返回:
    {
        "success": true,
        "user": { "username": "...", "email": "..." }
    }
    """
    data = request.get_json()
    if not data:
        return jsonify({'error': '请求体不能为空'}), 400

    username = (data.get('username') or '').strip()
    password = data.get('password', '')

    if not username or not password:
        return jsonify({'error': '用户名和密码不能为空'}), 400

    cache = get_cache()
    if not cache or not cache.redis_client:
        return jsonify({'error': '存储服务不可用', 'code': 503}), 503

    redis_client = cache.redis_client

    # 暴力破解防护：限制登录尝试次数
    attempt_key = f"login_attempts:{username}"
    attempts = redis_client.get(attempt_key)
    if attempts:
        try:
            if int(attempts) >= 5:
                return jsonify({'error': '尝试次数过多，请稍后再试'}), 429
        except (ValueError, TypeError):
            redis_client.delete(attempt_key)

    user = _get_user_by_field('username', username)
    if not user:
        # 记录失败尝试
        redis_client.incr(attempt_key)
        redis_client.expire(attempt_key, 300)  # 5分钟过期
        return jsonify({'error': '用户名或密码错误'}), 401

    # 验证密码
    if not check_password_hash(user.get('password_hash', ''), password):
        redis_client.incr(attempt_key)
        redis_client.expire(attempt_key, 300)
        return jsonify({'error': '用户名或密码错误'}), 401

    # 登录成功，清除尝试计数
    redis_client.delete(attempt_key)

    # 设置 session
    session['user_id'] = username
    session.permanent = True

    log_debug(f"[AUTH] 用户登录成功: {username}")

    return jsonify({
        'success': True,
        'user': {
            'username': user['username'],
            'email': user.get('email', ''),
            'student_id': user.get('student_id', ''),
        }
    })


@auth_bp.route('/api/auth/logout', methods=['POST'])
def logout():
    """
    用户登出接口

    清除 session
    """
    session.clear()
    return jsonify({'success': True, 'message': '已登出'})


@auth_bp.route('/api/auth/me', methods=['GET'])
def get_current_user():
    """
    获取当前登录用户信息

    返回:
    {
        "username": "...",
        "email": "...",
        "student_id": "..."
    }
    """
    if 'user_id' not in session:
        return jsonify({'error': '未登录', 'code': 401}), 401

    user = _get_user_by_field('username', session['user_id'])
    if not user:
        session.pop('user_id', None)
        return jsonify({'error': '用户不存在'}), 404

    return jsonify({
        'username': user['username'],
        'email': user.get('email', ''),
        'student_id': user.get('student_id', ''),
    })


def admin_required(f):
    """
    管理员验证装饰器

    检查 session 中 user_id 是否为管理员（通过 ADMIN_USERS 环境变量配置）
    未登录返回 401，非管理员返回 403
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return jsonify({
                'error': '请先登录',
                'code': 401,
                'need_login': True
            }), 401

        if not _ADMIN_USERS:
            return jsonify({
                'error': '管理员未配置，请联系管理员设置 ADMIN_USERS 环境变量',
                'code': 503
            }), 503

        if session['user_id'] not in _ADMIN_USERS:
            return jsonify({
                'error': '权限不足，需要管理员权限',
                'code': 403
            }), 403

        return f(*args, **kwargs)
    return decorated_function


@auth_bp.route('/api/admin/users', methods=['GET'])
@admin_required
def list_users():
    """
    管理员查看所有注册用户列表

    查询参数:
        page: 页码（默认 1）
        per_page: 每页数量（默认 50，最大 100）

    返回:
    {
        "success": true,
        "users": [...],
        "total": 10,
        "page": 1,
        "per_page": 50
    }
    """
    cache = get_cache()
    if not cache or not cache.redis_client:
        return jsonify({'error': '存储服务不可用', 'code': 503}), 503

    redis_client = cache.redis_client

    # 获取所有用户名（通过扫描 username 索引）
    username_keys = redis_client.keys('user_index:username:*')
    usernames = []
    for key in username_keys:
        username = redis_client.get(key)
        if username:
            usernames.append(username.decode() if isinstance(username, bytes) else username)

    # 获取每个用户的完整信息
    users = []
    for username in usernames:
        user_data = redis_client.get(_get_user_key(username))
        if user_data:
            user = json.loads(user_data)
            users.append({
                'username': user.get('username', ''),
                'email': user.get('email', ''),
                'student_id': user.get('student_id', ''),
                'created_at': user.get('created_at', 0),
            })

    # 按创建时间排序（新用户在前）
    users.sort(key=lambda u: u.get('created_at', 0), reverse=True)

    # 分页
    try:
        page = max(1, int(request.args.get('page', 1)))
        per_page = min(max(1, int(request.args.get('per_page', 50))), 100)
    except (ValueError, TypeError):
        page = 1
        per_page = 50
    total = len(users)
    start = (page - 1) * per_page
    end = start + per_page
    paginated_users = users[start:end]

    # 格式化创建时间
    for user in paginated_users:
        if user['created_at']:
            user['created_at_formatted'] = time.strftime(
                '%Y-%m-%d %H:%M:%S', time.localtime(user['created_at'])
            )

    return jsonify({
        'success': True,
        'users': paginated_users,
        'total': total,
        'page': page,
        'per_page': per_page,
    })
