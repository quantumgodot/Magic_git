#!/usr/bin/env python3
"""
下载多张原版 Rick Sanchez 全身照，去背景，存入 assets/rick_frames/ 供轮播。

来源：Rick and Morty Fandom Wiki
- FullBodyRick.png        全身照 696×1082
- Rick.png                半身照 243×439
- Rick Sanchez.png        标准照 848×1080
- Rick Sanchez (M-616).png Marvel版 362×585

用法：
    python download_rick.py           # 下载 + 去背景
    python download_rick.py --nobg    # 下载但不去背景
"""

import urllib.request
import os
import sys
from pathlib import Path

IMAGES = {
    "rick_fullbody": {
        "url": "https://static.wikia.nocookie.net/rickandmorty/images/6/68/FullBodyRick.png/revision/latest?cb=20250818125920",
        "desc": "全身照 696×1082",
    },
    "rick_std": {
        "url": "https://static.wikia.nocookie.net/rickandmorty/images/a/a6/Rick_Sanchez.png/revision/latest?cb=20250817060829",
        "desc": "标准照 848×1080",
    },
    "rick_classic": {
        "url": "https://static.wikia.nocookie.net/rickandmorty/images/d/dd/Rick.png/revision/latest?cb=20131230003659",
        "desc": "经典照 243×439",
    },
    "rick_marvel": {
        "url": "https://static.wikia.nocookie.net/rickandmorty/images/d/d1/Rick_Sanchez_%28M-616%29.png/revision/latest?cb=20260404111306",
        "desc": "M-616版 362×585",
    },
}

OUTPUT_DIR = Path(__file__).parent / "assets" / "rick_frames"
UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"


def download_image(name, url):
    """下载单张图片"""
    out_path = OUTPUT_DIR / f"{name}_raw.png"
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    print(f"  下载 {name} ({IMAGES[name]['desc']}) ...")
    with urllib.request.urlopen(req) as resp:
        data = resp.read()
    with open(out_path, 'wb') as f:
        f.write(data)
    print(f"    ✓ {len(data)//1024} KB -> {out_path.name}")
    return out_path


def remove_background(input_path, output_path):
    """
    去背景：将白色/浅色背景替换为透明。
    
    策略：
    1. 检测图片四个角的颜色（通常为背景色）
    2. 将接近背景色的像素 alpha 设为 0
    3. 边缘羽化处理
    """
    try:
        from PIL import Image
        import numpy as np
    except ImportError:
        print("    ⚠️ 需要 Pillow: pip install Pillow")
        return False

    img = Image.open(input_path).convert("RGBA")
    arr = np.array(img)
    h, w = arr.shape[:2]

    # 检测背景色（采样四角 + 四边中点）
    corners = [
        arr[0, 0], arr[0, w-1], arr[h-1, 0], arr[h-1, w-1],
        arr[0, w//2], arr[h-1, w//2], arr[h//2, 0], arr[h//2, w-1],
    ]
    bg_color = np.median(corners, axis=0)[:3]  # RGB only

    # 计算每个像素与背景色的距离
    diff = np.sqrt(np.sum((arr[:, :, :3].astype(float) - bg_color) ** 2, axis=2))

    # 阈值：距离 < 30 的视为背景
    threshold = 35
    mask = diff > threshold

    # 边缘羽化（距离在 threshold~threshold+20 之间半透明）
    feather = 20
    alpha = np.clip((diff - threshold) / feather * 255, 0, 255).astype(np.uint8)

    # 应用 alpha
    arr[:, :, 3] = alpha

    # 对于明显不是背景的区域保持完全不透明
    arr[diff > threshold + feather, 3] = 255

    result = Image.fromarray(arr, 'RGBA')
    result.save(output_path)
    return True


def main():
    import argparse
    parser = argparse.ArgumentParser(description="下载 Rick Sanchez 图片")
    parser.add_argument("--nobg", action="store_true", help="不去背景")
    args = parser.parse_args()

    os.makedirs(OUTPUT_DIR, exist_ok=True)
    print(f"\n🧪 下载 Rick Sanchez 图片到 {OUTPUT_DIR}\n")

    saved = []
    for name, info in IMAGES.items():
        try:
            raw_path = download_image(name, info["url"])
            
            if args.nobg:
                # 直接使用原始文件
                final_path = OUTPUT_DIR / f"{name}.png"
                os.rename(raw_path, final_path)
                saved.append(str(final_path))
            else:
                # 去背景
                final_path = OUTPUT_DIR / f"{name}.png"
                print(f"    🎨 去背景中 ...")
                if remove_background(raw_path, final_path):
                    print(f"    ✓ 已保存透明版: {final_path.name}")
                    os.remove(raw_path)  # 删除原始文件
                    saved.append(str(final_path))
                else:
                    # 去背景失败，保留原始文件
                    os.rename(raw_path, final_path)
                    saved.append(str(final_path))
        except Exception as e:
            print(f"    ✗ 失败: {e}")

    print(f"\n✅ 成功下载 {len(saved)} 张图片")
    for s in saved:
        print(f"   {Path(s).name}")
    print(f"\n运行 python main.py 启动轮播桌面宠物")


if __name__ == "__main__":
    main()
