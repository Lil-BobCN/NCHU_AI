#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
简单的HTTP服务器 - 用于访问AI助手插件演示页面
支持通过局域网访问HTML文件
"""

import http.server
import socketserver
import os
import sys
from pathlib import Path

# 配置
PORT = 5437  # 服务器端口，可以修改为其他端口
HOST = "0.0.0.0"  # 监听所有网络接口（支持公网IP访问）
# 服务目录：项目根目录（包含 NCHU_XGC.html 的目录）
DIRECTORY = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')


class MyHTTPRequestHandler(http.server.SimpleHTTPRequestHandler):
    """自定义HTTP请求处理器"""
    
    def __init__(self, *args, **kwargs):
        # 设置服务目录
        super().__init__(*args, directory=DIRECTORY, **kwargs)
    
    def end_headers(self):
        # 添加CORS头，允许跨域访问
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.send_header('Cache-Control', 'no-store, no-cache, must-revalidate')
        super().end_headers()
    
    def log_message(self, format, *args):
        # 自定义日志格式，显示中文友好的消息
        sys.stdout.write("%s - - [%s] %s\n" %
                         (self.address_string(),
                          self.log_date_time_string(),
                          format % args))


def get_local_ip():
    """获取本机局域网IP地址"""
    import socket
    try:
        # 创建一个UDP连接来获取本机IP（不会真正发送数据）
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return "127.0.0.1"


def main():
    """启动HTTP服务器"""
    # 切换到目标目录
    os.chdir(DIRECTORY)
    
    # 获取本机IP
    local_ip = get_local_ip()
    
    # 创建服务器
    Handler = MyHTTPRequestHandler
    
    with socketserver.TCPServer((HOST, PORT), Handler) as httpd:
        print("=" * 70)
        print("[AI助手] 插件演示服务器已启动")
        print("=" * 70)
        print(f"[DIR] 服务目录: {DIRECTORY}")
        print(f"[URL] 监听地址: {HOST}:{PORT} (所有网络接口)")
        print(f"")
        print(f"[LOCAL] 本机访问:")
        print(f"   http://localhost:{PORT}/NCHU_XGC.html")
        print(f"   http://127.0.0.1:{PORT}/NCHU_XGC.html")
        print(f"")
        print(f"[LAN] 局域网访问:")
        print(f"   http://{local_ip}:{PORT}/NCHU_XGC.html")
        print(f"")
        print(f"[WAN] 公网访问 (需配置内网穿透):")
        print(f"   http://[您的公网IP]:{PORT}/NCHU_XGC.html")
        print(f"")
        print(f"[DEMO] 演示页面:")
        print(f"   http://localhost:{PORT}/demo.html")
        print("=" * 70)
        print("[TIP] 提示:")
        print("   - 按 Ctrl+C 停止服务器")
        print("   - 监听 0.0.0.0 表示接受所有来源的连接")
        print("   - 支持局域网、公网IP、内网穿透访问")
        print("   - 确保防火墙允许端口 %d 的访问" % PORT)
        print("=" * 70)
        print("\n[RUNNING] 服务器运行中，等待请求...\n")
        
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\n\n⏹️  服务器已停止")
            sys.exit(0)


if __name__ == "__main__":
    main()
