#!/usr/bin/env python3
"""
桌面宠物 Rick — 入口文件

用法:
    python main.py                    启动桌面宠物
    python main.py --mute             静音模式
    python main.py --no-camera        禁用摄像头
    python main.py --llm MODEL        指定 LLM 模型

环境变量:
    OPENAI_API_KEY    OpenAI API 密钥（启用 LLM 对话）
    OPENAI_BASE_URL   API 端点（默认 https://api.openai.com/v1）
    OPENAI_MODEL      模型名称（默认 gpt-3.5-turbo）

依赖安装:
    pip install -r requirements.txt
"""

import sys
import os
import argparse

# 确保 pet 目录在 Python 路径中
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from pet_app import create_app, PetApp


def main():
    parser = argparse.ArgumentParser(
        description="🧪 Rick Sanchez 桌面宠物 — Wubba lubba dub dub!",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  python main.py                      # 正常启动
  python main.py --mute               # 静音模式
  python main.py --llm gpt-4          # 使用 GPT-4
  python main.py --camera             # 启动时开启摄像头

环境变量:
  OPENAI_API_KEY=sk-xxx  python main.py  # 带 LLM 启动
        """,
    )

    parser.add_argument(
        "--mute", "-m",
        action="store_true",
        help="静音模式（不播放音效）",
    )
    parser.add_argument(
        "--camera", "-c",
        action="store_true",
        help="启动时开启摄像头面部检测",
    )
    parser.add_argument(
        "--no-camera",
        action="store_true",
        help="禁用摄像头（默认）",
    )
    parser.add_argument(
        "--llm", "-l",
        type=str,
        metavar="MODEL",
        help="启用 LLM 并指定模型（如 gpt-3.5-turbo, gpt-4）",
    )
    parser.add_argument(
        "--api-key", "-k",
        type=str,
        help="OpenAI API 密钥",
    )
    parser.add_argument(
        "--base-url", "-b",
        type=str,
        help="API Base URL（默认 https://api.openai.com/v1）",
    )

    args = parser.parse_args()

    # 处理命令行参数
    if args.mute:
        os.environ["RICK_MUTE"] = "1"

    if args.api_key:
        os.environ["OPENAI_API_KEY"] = args.api_key

    if args.base_url:
        os.environ["OPENAI_BASE_URL"] = args.base_url

    if args.llm:
        os.environ["OPENAI_MODEL"] = args.llm

    # 打印欢迎信息
    print(r"""
    ╔═══════════════════════════════════╗
    ║   🧪  Desktop Rick              ║
    ║   Wubba lubba dub dub!          ║
    ║                                 ║
    ║   Rick Sanchez 已抵达桌面      ║
    ║   右键点击查看菜单             ║
    ║   双击开始聊天                 ║
    ╚═══════════════════════════════════╝
    """)

    print("🎯 提示:")
    print("  • 单击 Rick = 互动 + 台词")
    print("  • 双击 Rick = 打开聊天")
    print("  • 右键 Rick = 设置菜单")
    print("  • 拖拽 Rick = 移动位置")
    print()

    # 创建应用
    app = create_app()

    # 应用命令行参数覆盖
    if args.mute:
        app.sound.mute = True

    if args.camera and app.camera.is_available:
        app.behavior.is_camera_enabled = True
        app.camera.start()

    if args.llm and app.llm.is_available:
        app.behavior.is_llm_enabled = True

    # 运行
    try:
        sys.exit(app.run())
    except KeyboardInterrupt:
        print("\n👋 Rick 说再见... Wubba lubba dub dub!")
        sys.exit(0)


if __name__ == "__main__":
    main()
