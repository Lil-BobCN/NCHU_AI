#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
WSGI 入口文件 - 用于生产环境部署

使用方式:
    # Gunicorn
    gunicorn -w 4 -b 0.0.0.0:5000 wsgi:app

    # uWSGI
    uwsgi --http 0.0.0.0:5000 --wsgi-file wsgi.py --callable app --processes 4

    # Waitress (Windows)
    waitress-serve --host=0.0.0.0 --port=5000 wsgi:app
"""
import os
import sys

# 确保能正确导入模块
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

from app import create_app

# 创建应用实例
app = create_app()

# 暴露给WSGI服务器
application = app

if __name__ == '__main__':
    # 直接运行时使用简单的WSGI服务器
    from werkzeug.serving import run_simple
    run_simple('localhost', 5000, app, use_reloader=True, use_debugger=True)
