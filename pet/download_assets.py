#!/usr/bin/env python3
"""
素材下载器 — 获取 Rick Sanchez 桌面宠物精灵图。

Shimeji 精灵图格式说明：
- 每个动画一个精灵条 PNG，水平排列所有帧
- 帧宽 = 帧高 = 128px（推荐）
- 需要以下动画：
  idle.png    — 待机（4帧）
  walk.png    — 行走（8帧，右向）
  fall.png    — 下落（4帧）
  surprised.png — 惊讶（2帧）
  sleep.png   — 睡觉（2帧）
  grabbed.png — 被拖拽（2帧）

获取方式：
1. 从 Shimeji 社区下载 Rick 精灵图包
2. 使用本脚本自动生成占位精灵图（简化像素风）
3. 手动放置精灵图到 assets/sprites/rick/ 目录

已知资源站点（可能需要代理）：
- DeviantArt: 搜索 "Rick Sanchez shimeji"
- GitHub: 搜索 "shimeji rick sprites"
- Shimeji-ee 官方角色库
"""

import os
import sys
import json
from pathlib import Path
from sprite_engine import SpriteEngine


def generate_placeholder_sprites(output_dir: str):
    """
    生成占位精灵图（极简像素风，方便替换）。
    这不等于"手绘 Rick"，这是 code-generated placeholder，
    目的是让精灵图引擎能跑起来，用户可以随时换成真实素材。
    """
    try:
        from PIL import Image, ImageDraw
    except ImportError:
        print("需要 Pillow 库来生成占位图: pip install Pillow")
        return

    os.makedirs(output_dir, exist_ok=True)
    size = 128

    print(f"[下载器] 正在生成占位精灵图到 {output_dir} ...")

    # 调色板（Rick 配色）
    SKIN = (180, 180, 185)
    HAIR = (120, 180, 240)
    COAT = (240, 245, 250)
    PANTS = (80, 70, 60)
    EYE = (255, 255, 255)
    PUPIL = (30, 30, 35)
    GREEN = (100, 255, 100)

    def draw_rick_head(draw, ox=0, oy=0, s=128):
        """极简 Rick 头像（用于占位）"""
        # 头发
        draw.polygon([
            (ox + s*0.35, oy + s*0.25),
            (ox + s*0.3, oy + s*0.15),
            (ox + s*0.45, oy + s*0.3),
            (ox + s*0.5, oy + s*0.15),
            (ox + s*0.65, oy + s*0.25),
            (ox + s*0.65, oy + s*0.4),
            (ox + s*0.35, oy + s*0.4),
        ], fill=HAIR)
        # 脸
        draw.ellipse([ox + s*0.35, oy + s*0.22, ox + s*0.65, oy + s*0.55], fill=SKIN)
        # 眼
        draw.ellipse([ox + s*0.42, oy + s*0.32, ox + s*0.50, oy + s*0.38], fill=EYE)
        draw.ellipse([ox + s*0.55, oy + s*0.32, ox + s*0.63, oy + s*0.38], fill=EYE)
        draw.ellipse([ox + s*0.44, oy + s*0.34, ox + s*0.48, oy + s*0.36], fill=PUPIL)
        draw.ellipse([ox + s*0.57, oy + s*0.34, ox + s*0.61, oy + s*0.36], fill=PUPIL)

    def draw_rick_body(draw, ox=0, oy=0, s=128):
        """极简 Rick 身体"""
        # 白大褂
        draw.rectangle([ox + s*0.3, oy + s*0.35, ox + s*0.7, oy + s*0.7], fill=COAT)
        # 裤子
        draw.rectangle([ox + s*0.35, oy + s*0.6, ox + s*0.45, oy + s*0.85], fill=PANTS)
        draw.rectangle([ox + s*0.55, oy + s*0.6, ox + s*0.65, oy + s*0.85], fill=PANTS)
        # 传送枪（绿色光点）
        draw.ellipse([ox + s*0.68, oy + s*0.4, ox + s*0.78, oy + s*0.5], fill=GREEN)

    # --- 生成 idle.png (4帧：微呼吸) ---
    idle_img = Image.new("RGBA", (size * 4, size), (0, 0, 0, 0))
    for i in range(4):
        d = ImageDraw.Draw(idle_img)
        offset_y = int(2 * (1 if i % 2 == 0 else -1))  # 呼吸微动
        ox = i * size
        draw_rick_head(d, ox, 10 + offset_y)
        draw_rick_body(d, ox, 15 + offset_y)
        # "RICK" 标签
        d.text((ox + 45, 90), "RICK", fill=(200, 200, 200))
    idle_img.save(os.path.join(output_dir, "idle.png"))
    print("  ✓ idle.png (4帧)")

    # --- 生成 walk.png (8帧：行走) ---
    walk_img = Image.new("RGBA", (size * 8, size), (0, 0, 0, 0))
    for i in range(8):
        d = ImageDraw.Draw(walk_img)
        phase = i / 8.0 * 6.283  # 完整周期
        import math
        offset_y = int(3 * math.sin(phase))      # 上下弹跳
        offset_x = int(2 * math.cos(phase))      # 左右摆动
        ox = i * size
        draw_rick_head(d, ox + offset_x, 10 + offset_y)
        draw_rick_body(d, ox, 15 + offset_y)
        d.text((ox + 42 + offset_x, 90 + offset_y), "RICK", fill=(200, 200, 200))
    walk_img.save(os.path.join(output_dir, "walk.png"))
    print("  ✓ walk.png (8帧)")

    # --- 生成 surprised.png (2帧) ---
    surp_img = Image.new("RGBA", (size * 2, size), (0, 0, 0, 0))
    for i in range(2):
        d = ImageDraw.Draw(surp_img)
        ox = i * size
        draw_rick_head(d, ox, 8)
        draw_rick_body(d, ox, 12)
        # 惊讶大眼
        eye_size = 6 if i == 0 else 8
        d.ellipse([ox + 54, 51, ox + 54 + eye_size, 51 + eye_size], fill=EYE)
        d.ellipse([ox + 72, 51, ox + 72 + eye_size, 51 + eye_size], fill=EYE)
        d.text((ox + 35, 90), "WUBBA!", fill=GREEN)
    surp_img.save(os.path.join(output_dir, "surprised.png"))
    print("  ✓ surprised.png (2帧)")

    # --- 生成 sleep.png (2帧) ---
    sleep_img = Image.new("RGBA", (size * 2, size), (0, 0, 0, 0))
    for i in range(2):
        d = ImageDraw.Draw(sleep_img)
        ox = i * size
        draw_rick_head(d, ox, 15)
        draw_rick_body(d, ox, 20)
        # 闭眼线
        d.line([(ox+48, 54), (ox+56, 54)], fill=PUPIL, width=2)
        d.line([(ox+66, 54), (ox+74, 54)], fill=PUPIL, width=2)
        # Zzz
        zzz = "Z" if i == 0 else "z"
        d.text((ox + 80, 30 + i*3), zzz, fill=(150, 200, 255))
    sleep_img.save(os.path.join(output_dir, "sleep.png"))
    print("  ✓ sleep.png (2帧)")

    # --- 生成 grabbed.png (2帧) ---
    grab_img = Image.new("RGBA", (size * 2, size), (0, 0, 0, 0))
    for i in range(2):
        d = ImageDraw.Draw(grab_img)
        ox = i * size
        offset_y = i * 4  # 被抓取时微微上移
        draw_rick_head(d, ox, 5 - offset_y)
        draw_rick_body(d, ox, 10 - offset_y)
        d.text((ox + 30, 90 - offset_y), "HEY!", fill=(255, 100, 100))
    grab_img.save(os.path.join(output_dir, "grabbed.png"))
    print("  ✓ grabbed.png (2帧)")

    # --- 生成 fall.png (4帧) ---
    fall_img = Image.new("RGBA", (size * 4, size), (0, 0, 0, 0))
    for i in range(4):
        d = ImageDraw.Draw(fall_img)
        ox = i * size
        offset_y = i * 15  # 越来越往下
        angle = i * 10     # 旋转感
        draw_rick_head(d, ox + angle//2, 5 + offset_y)
        draw_rick_body(d, ox, 10 + offset_y)
        d.text((ox + 38, 88 + offset_y), "AAAH!", fill=(255, 150, 100))
    fall_img.save(os.path.join(output_dir, "fall.png"))
    print("  ✓ fall.png (4帧)")

    # 创建配置文件
    SpriteEngine.create_default_config(output_dir)
    print(f"\n[下载器] 占位精灵图已生成到: {output_dir}")
    print("[提示] 这些是占位图。获取更好的 Rick 精灵图后直接替换即可。")


def try_download_from_url(url: str, output_path: str) -> bool:
    """尝试从 URL 下载单个文件"""
    try:
        import urllib.request
        req = urllib.request.Request(url, headers={
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)"
        })
        with urllib.request.urlopen(req, timeout=30) as resp:
            data = resp.read()
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            with open(output_path, 'wb') as f:
                f.write(data)
            return True
    except Exception as e:
        print(f"  下载失败: {e}")
        return False


def download_rick_sprites(output_dir: str):
    """尝试从已知 URL 下载 Rick 精灵图"""
    print("[下载器] 尝试从网络获取 Rick 精灵图...")
    print("[下载器] 注意：自动下载可能因网络限制失败，将 fallback 到生成占位图。\n")

    # 已知的 shimeji 资源 URL（可能失效，需要更新）
    base_urls = [
        # DeviantArt shimeji 资源（通常需要手动下载）
        # GitHub 上可能的 shimeji 仓库
        "https://raw.githubusercontent.com/user/rick-shimeji-sprites/main/",
    ]

    downloaded_any = False

    for anim in ["idle", "walk", "fall", "surprised", "sleep", "grabbed"]:
        for base in base_urls:
            url = f"{base}{anim}.png"
            out = os.path.join(output_dir, f"{anim}.png")
            if try_download_from_url(url, out):
                print(f"  ✓ 已下载 {anim}.png")
                downloaded_any = True
                break

    if not downloaded_any:
        print("[下载器] 在线下载未成功，生成占位精灵图...")
        generate_placeholder_sprites(output_dir)
    else:
        # 创建配置文件
        SpriteEngine.create_default_config(output_dir)


def main():
    import argparse
    parser = argparse.ArgumentParser(
        description="Rick 桌面宠物 — 精灵图素材下载器"
    )
    parser.add_argument(
        "--output", "-o",
        default=None,
        help="输出目录（默认: assets/sprites/rick/）"
    )
    parser.add_argument(
        "--placeholder", "-p",
        action="store_true",
        help="直接生成占位精灵图（跳过在线下载）"
    )

    args = parser.parse_args()

    if args.output:
        output_dir = args.output
    else:
        # 默认输出到 pet/assets/sprites/rick/
        script_dir = os.path.dirname(os.path.abspath(__file__))
        output_dir = os.path.join(script_dir, "assets", "sprites", "rick")

    if args.placeholder:
        generate_placeholder_sprites(output_dir)
    else:
        download_rick_sprites(output_dir)

    print("""
╔══════════════════════════════════════════════╗
║  🧪  精灵图准备完成！                      ║
║                                              ║
║  获取更好的 Rick 精灵图:                    ║
║  1. DeviantArt 搜索 "Rick Sanchez shimeji"  ║
║  2. GitHub 搜索 "shimeji rick sprites"      ║
║  3. 将下载的 PNG 放入资产目录替换占位图    ║
║                                              ║
║  然后运行: python main.py                   ║
╚══════════════════════════════════════════════╝
    """)


if __name__ == "__main__":
    main()
