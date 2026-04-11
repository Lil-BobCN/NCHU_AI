#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
后端服务启动入口
提供Flask应用启动和Werkzeug服务器运行

使用方法:
    python run.py                    # 默认配置启动
    python run.py --host 0.0.0.0     # 指定主机
    python run.py --port 8080        # 指定端口
    python run.py --debug            # 调试模式
"""
import sys
import os
import argparse

# 确保能正确导入模块
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

from app import create_app
from config.default import SERVER_CONFIG, QWEN_API_CONFIG


def print_banner():
    """打印启动横幅"""
    banner = """
╔══════════════════════════════════════════════════════════════════════╗
║                     南昌航空大学 AI 助手服务                         ║
║                     NCHU AI Assistant Service                        ║
╠══════════════════════════════════════════════════════════════════════╣
║  版本: 1.0.0                                                         ║
║  模型: {model:<20}                                         ║
╚══════════════════════════════════════════════════════════════════════╝
    """.format(model=QWEN_API_CONFIG.get('model', 'unknown'))
    print(banner)


def print_config(host, port, debug):
    """打印配置信息"""
    print("[配置信息]")
    print(f"  - 监听地址: {host}:{port}")
    print(f"  - 调试模式: {'开启' if debug else '关闭'}")
    print(f"  - API密钥: {'已配置' if QWEN_API_CONFIG.get('api_key') else '未配置'}")
    print("-" * 70)


def parse_args():
    """解析命令行参数"""
    parser = argparse.ArgumentParser(
        description='南昌航空大学AI助手后端服务',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  python run.py                    # 使用默认配置启动
  python run.py --host 0.0.0.0     # 监听所有接口
  python run.py --port 8080        # 使用8080端口
  python run.py --debug            # 启用调试模式
        """
    )

    parser.add_argument(
        '--host',
        type=str,
        default=SERVER_CONFIG['host'],
        help=f'服务器监听地址 (默认: {SERVER_CONFIG["host"]})'
    )

    parser.add_argument(
        '--port',
        type=int,
        default=SERVER_CONFIG['port'],
        help=f'服务器端口 (默认: {SERVER_CONFIG["port"]})'
    )

    parser.add_argument(
        '--debug',
        action='store_true',
        default=SERVER_CONFIG['debug'],
        help='启用调试模式'
    )

    return parser.parse_args()


def main():
    """主函数"""
    args = parse_args()

    print_banner()

    # 检查必要配置
    if not QWEN_API_CONFIG.get('api_key'):
        print("[警告] API密钥未配置！请设置 QWEN_API_KEY 环境变量")
        print("       从阿里云控制台获取: https://dashscope.console.aliyun.com/")
        print("-" * 70)

    print_config(args.host, args.port, args.debug)

    # 创建应用
    app = create_app()

    try:
        print("[启动] 服务器启动中...")
        app.run(
            host=args.host,
            port=args.port,
            debug=args.debug,
            threaded=True,
            use_reloader=args.debug  # 调试模式下启用自动重载
        )
    except KeyboardInterrupt:
        print("\n[关闭] 收到中断信号，服务器正在关闭...")
    except Exception as e:
        print(f"\n[错误] 服务器启动失败: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()
