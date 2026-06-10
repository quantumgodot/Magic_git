#!/usr/bin/env python3
"""
高质量 Rick Sanchez 像素精灵图生成器。

逐像素绘制 Rick 形象（128x128），细节包括：
- 灰皮肤 + 阴影层次
- 蓝色渐变尖发
- 白大褂 + 衣褶
- 传送枪 + 绿色光晕
- 口水/打嗝特效
- 浓眉 + 半睁眼

生成 6 组动画精灵条：
  idle (4帧) / walk (8帧) / surprised (2帧) / sleep (2帧) / grabbed (2帧) / fall (4帧)
"""

import os
import math
import json
from pathlib import Path

# =============================================================================
# 调色板
# =============================================================================
C_SKIN       = (188, 188, 193)   # 灰皮肤
C_SKIN_DARK  = (158, 158, 163)   # 深灰（阴影）
C_SKIN_LIGHT = (210, 210, 215)   # 浅灰（高光）
C_HAIR       = (100, 170, 240)   # 蓝发
C_HAIR_DARK  = (60, 130, 210)    # 深蓝发
C_HAIR_LIGHT = (140, 200, 250)   # 浅蓝发
C_COAT       = (240, 245, 252)   # 白大褂
C_COAT_DARK  = (210, 218, 228)   # 大褂阴影
C_SHIRT      = (110, 160, 200)   # 蓝衬衫
C_PANTS      = (80, 70, 62)      # 棕裤子
C_PANTS_DARK = (60, 52, 44)      # 深棕
C_SHOES      = (38, 38, 42)      # 黑鞋
C_BELT       = (55, 45, 38)      # 深棕皮带
C_EYEBROW    = (70, 75, 80)      # 浓眉
C_EYE_WHITE  = (252, 252, 252)   # 眼白
C_PUPIL      = (22, 22, 28)      # 瞳孔
C_MOUTH      = (140, 80, 70)     # 嘴
C_DROOL      = (140, 210, 170)   # 口水
C_GUN        = (150, 150, 158)   # 传送枪
C_GUN_DARK   = (120, 120, 128)   # 枪深色
C_GLOW       = (60, 255, 60)     # 绿光
C_GLOW_DIM   = (40, 180, 40)     # 暗绿光


def blend(c1, c2, t):
    """颜色混合"""
    return tuple(int(a + (b - a) * t) for a, b in zip(c1, c2))


# =============================================================================
# 绘制基元
# =============================================================================

def draw_rick(pixels, w, h, ox, oy, anim, frame, total_frames):
    """
    在 pixels 画布上 (ox,oy) 偏移处绘制一帧 Rick。
    
    Args:
        pixels: PIL 像素访问对象
        w, h: 单帧宽高 (128x128)
        ox, oy: 当前帧在精灵条上的偏移
        anim: 动画名 ('idle','walk','surprised','sleep','grabbed','fall')
        frame: 当前帧号 (0-based)
        total_frames: 总帧数
    """
    s = w  # 128
    cx, cy = s // 2, s // 2

    # --- 动画参数 ---
    phase = frame / max(total_frames, 1) * 2 * math.pi

    bob_y = 0        # 身体上下弹跳
    head_tilt = 0    # 头部倾斜
    arm_swing = 0    # 手臂摆动
    leg_phase = 0    # 腿部相位
    mouth_open = 0   # 张嘴程度
    eye_scale = 1.0  # 眼睛大小
    is_sleep = False

    if anim == 'idle':
        bob_y = int(1.5 * math.sin(phase))
    elif anim == 'walk':
        bob_y = int(4 * math.sin(phase))
        arm_swing = math.sin(phase) * 0.15
        leg_phase = phase
    elif anim == 'surprised':
        mouth_open = 0.7
        eye_scale = 1.4 if frame == 1 else 1.2
    elif anim == 'sleep':
        is_sleep = True
        bob_y = int(1 * math.sin(phase))
    elif anim == 'grabbed':
        bob_y = -3 - frame * 2
    elif anim == 'fall':
        bob_y = frame * 10
        head_tilt = frame * 5

    # --- 身体偏移 ---
    body_cy = int(cy + bob_y * 0.5)

    # --- 绘制 ---
    _draw_body(pixels, ox + cx, body_cy, s, arm_swing)
    _draw_legs(pixels, ox + cx, body_cy, s, leg_phase)
    _draw_arms(pixels, ox + cx, body_cy, s, arm_swing)
    _draw_head(pixels, ox + cx, body_cy - int(s * 0.38), s,
               mouth_open, eye_scale, is_sleep, anim, frame)
    _draw_hair(pixels, ox + cx, body_cy - int(s * 0.38), s)
    _draw_portal_gun(pixels, ox + cx, body_cy, s, anim)

    # 特效
    if anim == 'sleep':
        _draw_zzz(pixels, ox, oy, s, frame)
    if anim == 'surprised':
        _draw_exclamation(pixels, ox, oy, s, frame)


def _rect(pixels, x1, y1, x2, y2, color):
    """填充矩形"""
    x1, x2 = max(0, min(x1, x2)), min(pixels.shape[0], max(x1, x2))
    y1, y2 = max(0, min(y1, y2)), min(pixels.shape[1], max(y1, y2))
    if x1 < x2 and y1 < y2:
        for y in range(y1, y2):
            for x in range(x1, x2):
                try:
                    pixels[x, y] = (*color, 255)
                except IndexError:
                    pass

def _ellipse(pixels, cx, cy, rx, ry, color):
    """填充椭圆"""
    for y in range(max(0, cy - ry), min(pixels.shape[1], cy + ry + 1)):
        for x in range(max(0, cx - rx), min(pixels.shape[0], cx + rx + 1)):
            if rx > 0 and ry > 0:
                if ((x - cx) / rx) ** 2 + ((y - cy) / ry) ** 2 <= 1:
                    try:
                        pixels[x, y] = (*color, 255)
                    except IndexError:
                        pass

def _line_h(pixels, x1, x2, y, color, thick=1):
    """水平线"""
    for t in range(thick):
        _rect(pixels, x1, y + t, x2 + 1, y + t + 1, color)

def _line_v(pixels, x, y1, y2, color, thick=1):
    """竖直线"""
    for t in range(thick):
        _rect(pixels, x + t, y1, x + t + 1, y2 + 1, color)

def _gradient_rect(pixels, x1, y1, x2, y2, c_top, c_bottom):
    """渐变矩形（上到下）"""
    for y in range(y1, y2):
        t = (y - y1) / max(y2 - y1, 1)
        c = blend(c_top, c_bottom, t)
        _rect(pixels, x1, y, x2, y + 1, c)


# =============================================================================
# 身体部件
# =============================================================================

def _draw_body(pixels, cx, cy, s, arm_swing):
    """白大褂 + 衬衫 + 腰带"""
    s2 = lambda v: int(v * s)
    
    # 白大褂
    bx1 = cx + s2(-0.23)
    by1 = cy + s2(-0.18)
    bx2 = cx + s2(0.23)
    by2 = cy + s2(0.30)
    _gradient_rect(pixels, bx1, by1, bx2, by2, C_COAT, C_COAT_DARK)
    
    # 大褂边缘线
    _line_v(pixels, bx1, by1, by2, C_COAT_DARK, 1)
    _line_v(pixels, bx2 - 1, by1, by2, C_COAT_DARK, 1)
    
    # 衬衫 V 领
    vx1 = cx + s2(-0.10)
    vx2 = cx + s2(0.10)
    vy_top = cy + s2(-0.18)
    vy_btm = cy + s2(-0.04)
    for y in range(vy_top, vy_btm):
        t = (y - vy_top) / max(vy_btm - vy_top, 1)
        lx = int(vx1 + (cx - vx1) * t)
        rx = int(vx2 - (vx2 - cx) * t)
        _rect(pixels, lx, y, rx, y + 1, C_SHIRT)
    
    # 腰带
    belt_y = cy + s2(0.24)
    _rect(pixels, bx1 - s2(0.02), belt_y, bx2 + s2(0.02), belt_y + s2(0.04), C_BELT)
    # 腰带扣
    buckle_x = cx - s2(0.03)
    _rect(pixels, buckle_x, belt_y - 1, buckle_x + s2(0.06), belt_y + s2(0.05), (180, 170, 80))


def _draw_legs(pixels, cx, cy, s, leg_phase):
    """裤子 + 鞋"""
    s2 = lambda v: int(v * s)
    
    ls = math.sin(leg_phase) * s2(0.04) if leg_phase else 0
    
    # 左腿
    lx1 = cx + s2(-0.15) + int(ls * 0.5)
    lx2 = cx + s2(-0.03) + int(ls * 0.5)
    ly1 = cy + s2(0.28)
    ly2 = cy + s2(0.48)
    _gradient_rect(pixels, lx1, ly1, lx2, ly2, C_PANTS, C_PANTS_DARK)
    
    # 右腿
    rx1 = cx + s2(0.03) - int(ls * 0.5)
    rx2 = cx + s2(0.15) - int(ls * 0.5)
    _gradient_rect(pixels, rx1, ly1, rx2, ly2, C_PANTS, C_PANTS_DARK)
    
    # 左鞋
    _rect(pixels, lx1 - s2(0.02), ly2, lx2 + s2(0.04), ly2 + s2(0.06), C_SHOES)
    # 右鞋
    _rect(pixels, rx1 - s2(0.02), ly2, rx2 + s2(0.04), ly2 + s2(0.06), C_SHOES)


def _draw_arms(pixels, cx, cy, s, arm_swing):
    """手臂"""
    s2 = lambda v: int(v * s)
    
    sw = int(arm_swing * s * 0.08)
    
    # 左臂（自然下垂）
    ax1 = cx + s2(-0.22)
    ay1 = cy + s2(-0.12)
    ax2 = cx + s2(-0.28) + sw
    ay2 = cy + s2(0.18)
    _rect(pixels, ax1, ay1, ax2, ay1 + s2(0.04), C_COAT)
    _rect(pixels, ax2 - s2(0.03), ay1 + s2(0.02), ax2 + s2(0.01), ay2, C_COAT)
    
    # 左手
    _ellipse(pixels, ax2, ay2 + s2(0.02), s2(0.04), s2(0.04), C_SKIN)
    
    # 右臂（持枪）
    rax1 = cx + s2(0.18)
    ray1 = cy + s2(-0.10)
    rax2 = cx + s2(0.25) - sw
    ray2 = cy + s2(0.08)
    _rect(pixels, rax1, ray1, rax2, ray1 + s2(0.04), C_COAT)
    _rect(pixels, rax2 - s2(0.03), ray1 + s2(0.02), rax2 + s2(0.01), ray2 + s2(0.06), C_COAT)


def _draw_head(pixels, cx, cy, s, mouth_open, eye_scale, is_sleep, anim, frame):
    """头部 + 五官"""
    s2 = lambda v: int(v * s)
    
    # 脸椭圆
    hx1 = cx + s2(-0.20)
    hy1 = cy + s2(-0.22)
    hx2 = cx + s2(0.20)
    hy2 = cy + s2(0.22)
    _ellipse(pixels, (hx1 + hx2) // 2, (hy1 + hy2) // 2,
             (hx2 - hx1) // 2, (hy2 - hy1) // 2, C_SKIN)
    
    # 下巴阴影
    _ellipse(pixels, cx, cy + s2(0.10), s2(0.12), s2(0.10), C_SKIN_DARK)
    _ellipse(pixels, cx, cy + s2(0.06), s2(0.16), s2(0.14), C_SKIN)
    
    # 额头皱纹
    wr_y = cy + s2(-0.12)
    _line_h(pixels, cx + s2(-0.08), cx + s2(0.06), wr_y, C_SKIN_DARK, 1)
    _line_h(pixels, cx + s2(-0.06), cx + s2(0.08), wr_y + s2(0.03), C_SKIN_DARK, 1)
    
    # --- 浓眉 ---
    brow_y = cy + s2(-0.04)
    brow_drop = s2(0.03)
    for t in range(3):  # 粗眉
        # 左眉
        _line_h(pixels, cx + s2(-0.15), cx + s2(-0.02), brow_y - t, C_EYEBROW, 1)
        # 右眉
        _line_h(pixels, cx + s2(0.02), cx + s2(0.15), brow_y - t, C_EYEBROW, 1)
    
    # --- 眼睛 ---
    eye_y = cy + s2(0.02)
    eye_r = int(s2(0.05) * eye_scale)
    
    if is_sleep:
        # 闭眼
        _line_h(pixels, cx + s2(-0.12), cx + s2(-0.01), eye_y, C_EYEBROW, 2)
        _line_h(pixels, cx + s2(0.01), cx + s2(0.12), eye_y, C_EYEBROW, 2)
    else:
        # 左眼
        le_x = cx + s2(-0.07)
        _ellipse(pixels, le_x, eye_y, eye_r, int(eye_r * 1.15), C_EYE_WHITE)
        _ellipse(pixels, le_x, eye_y, max(2, int(eye_r * 0.4)), max(2, int(eye_r * 0.45)), C_PUPIL)
        _ellipse(pixels, le_x - 1, eye_y - 1, 1, 1, C_SKIN_LIGHT)
        # 右眼
        re_x = cx + s2(0.07)
        _ellipse(pixels, re_x, eye_y, eye_r, int(eye_r * 1.15), C_EYE_WHITE)
        _ellipse(pixels, re_x, eye_y, max(2, int(eye_r * 0.4)), max(2, int(eye_r * 0.45)), C_PUPIL)
        _ellipse(pixels, re_x - 1, eye_y - 1, 1, 1, C_SKIN_LIGHT)
        
        # 眼袋
        bag_c = C_SKIN_DARK
        _line_h(pixels, le_x - s2(0.03), le_x + s2(0.03), eye_y + s2(0.04), bag_c, 1)
        _line_h(pixels, re_x - s2(0.03), re_x + s2(0.03), eye_y + s2(0.04), bag_c, 1)
    
    # --- 鼻子（简化为阴影） ---
    nose_y = cy + s2(0.08)
    _ellipse(pixels, cx, nose_y, s2(0.03), s2(0.02), C_SKIN_DARK)
    
    # --- 嘴巴 ---
    mouth_y = cy + s2(0.13)
    if mouth_open > 0.3:
        mw = s2(0.07)
        mh = int(s2(0.06) * mouth_open)
        _rect(pixels, cx - mw, mouth_y, cx + mw, mouth_y + mh, C_MOUTH)
        # 舌头
        _rect(pixels, cx - mw + 2, mouth_y + mh // 2, cx + mw - 2, mouth_y + mh, (200, 90, 80))
        
        # 口水
        if anim == 'surprised' or mouth_open > 0.5:
            drool_x = cx + s2(0.05)
            drool_y = mouth_y + mh
            _line_v(pixels, drool_x, drool_y, drool_y + s2(0.08), C_DROOL, 2)
            _ellipse(pixels, drool_x, drool_y + s2(0.09), s2(0.015), s2(0.02), C_DROOL)
    else:
        # 微笑弧线
        for t in range(2):
            _line_h(pixels, cx + s2(-0.06), cx + s2(0.06), mouth_y + t, C_MOUTH, 1)
    
    # --- 耳朵位置标记 ---
    _ellipse(pixels, cx + s2(-0.19), cy, s2(0.03), s2(0.04), C_SKIN_DARK)
    _ellipse(pixels, cx + s2(0.19), cy, s2(0.03), s2(0.04), C_SKIN_DARK)


def _draw_hair(pixels, cx, cy, s):
    """蓝渐变尖发"""
    s2 = lambda v: int(v * s)
    
    # 头发覆盖头顶椭圆上半
    hx1 = cx + s2(-0.22)
    hy1 = cy + s2(-0.20)
    hx2 = cx + s2(0.22)
    hy2 = cy + s2(-0.08)
    
    for y in range(hy1, hy2 + 1):
        t = (y - hy1) / max(hy2 - hy1, 1)
        for x in range(hx1, hx2 + 1):
            rx = (hx2 - hx1) / 2
            ry = (hy2 - hy1) / 2
            hcx = (hx1 + hx2) / 2
            hcy = (hy1 + hy2) / 2
            if rx > 0 and ry > 0:
                if ((x - hcx) / rx) ** 2 + ((y - hcy) / ry) ** 2 <= 1:
                    c = blend(C_HAIR, C_HAIR_DARK, t)
                    try:
                        if y <= cy + s2(-0.04):
                            pixels[x, y] = (*c, 255)
                    except IndexError:
                        pass
    
    # 尖刺（8根）
    spikes = [
        (cx + s2(-0.20), cy + s2(-0.24)),   # 左最
        (cx + s2(-0.14), cy + s2(-0.32)),   # 左尖
        (cx + s2(-0.06), cy + s2(-0.26)),
        (cx + s2(0.00), cy + s2(-0.36)),    # 中间最高
        (cx + s2(0.06), cy + s2(-0.28)),
        (cx + s2(0.10), cy + s2(-0.34)),    # 右尖
        (cx + s2(0.16), cy + s2(-0.26)),
        (cx + s2(0.20), cy + s2(-0.16)),    # 右落
    ]
    
    for i, (sx, sy) in enumerate(spikes):
        spike_w = s2(0.05)
        spike_h = s2(0.10) + (i % 3) * s2(0.03)
        for dy in range(spike_h):
            t = dy / max(spike_h, 1)
            c = blend(C_HAIR_LIGHT, C_HAIR_DARK, t)
            lw = int(spike_w * (1 - t * 0.8))
            _rect(pixels, sx - lw, sy - dy, sx + lw, sy - dy + 1, c)
    
    # 发根渐变
    for y in range(cy + s2(-0.08), cy + s2(-0.01)):
        t = (y - (cy + s2(-0.08))) / s2(0.07)
        c = blend(C_HAIR_DARK, C_HAIR, t)
        _rect(pixels, cx + s2(-0.18), y, cx + s2(0.18), y + 1, c)


def _draw_portal_gun(pixels, cx, cy, s, anim):
    """传送枪"""
    s2 = lambda v: int(v * s)
    
    gx = cx + s2(0.20)
    gy = cy + s2(0.04)
    
    # 枪身
    _rect(pixels, gx, gy - s2(0.10), gx + s2(0.08), gy + s2(0.02), C_GUN)
    _rect(pixels, gx + s2(0.02), gy - s2(0.08), gx + s2(0.10), gy + s2(0.04), C_GUN_DARK)
    
    # 枪口绿光
    glow_x = gx + s2(0.08)
    glow_y = gy - s2(0.04)
    for r in range(s2(0.05), 0, -1):
        alpha = 0.8 - r / s2(0.05) * 0.8
        gc = blend(C_GLOW, (0, 0, 0), 1 - alpha)
        _ellipse(pixels, glow_x, glow_y, r, r, gc)
    
    # 能量脉冲（动画）
    if anim == 'surprised':
        for r in range(s2(0.07), s2(0.04), -1):
            _ellipse(pixels, glow_x, glow_y, r, r, C_GLOW)


def _draw_zzz(pixels, ox, oy, s, frame):
    """Zzz 睡眠标记"""
    s2 = lambda v: int(v * s)
    zx = ox + s2(0.75)
    zy = oy + s2(0.10) + frame * s2(0.03)
    
    z_colors = [(180, 210, 255), (150, 190, 245), (120, 170, 235)]
    z_texts = ["Z", "z", "z"]
    
    for i, (txt, col) in enumerate(zip(z_texts, z_colors)):
        z_ox = zx - i * s2(0.06)
        z_oy = zy - i * s2(0.10)
        # 简化 Z 绘制
        size = s2(0.06) - i * s2(0.01)
        _line_h(pixels, z_ox - size, z_ox + size, z_oy - size, col, 2)
        _line_h(pixels, z_ox - size, z_ox + size, z_oy + size, col, 2)


def _draw_exclamation(pixels, ox, oy, s, frame):
    """惊讶感叹号"""
    s2 = lambda v: int(v * s)
    ex = ox + s2(0.72)
    ey = oy + s2(0.15)
    
    # ! 号
    _rect(pixels, ex - s2(0.015), ey, ex + s2(0.015), ey + s2(0.08), (255, 200, 50))
    _ellipse(pixels, ex, ey + s2(0.10), s2(0.02), s2(0.02), (255, 200, 50))


# =============================================================================
# 主生成函数
# =============================================================================

def generate_sprite_sheet(anim_name, num_frames, output_path):
    """生成单个精灵条 PNG"""
    from PIL import Image
    import numpy as np
    
    W, H = 128, 128
    sheet_w = W * num_frames
    sheet_h = H
    
    img = Image.new("RGBA", (sheet_w, sheet_h), (0, 0, 0, 0))
    pixels = img.load()
    
    # 使用 numpy 数组做像素操作更方便
    arr = np.zeros((sheet_w, sheet_h, 4), dtype=np.uint8)
    
    for f in range(num_frames):
        ox = f * W
        draw_rick(arr, W, H, ox, 0, anim_name, f, num_frames)
    
    # numpy -> PIL
    img = Image.fromarray(arr, 'RGBA')
    img.save(output_path)
    print(f"  ✓ {output_path} ({num_frames}帧)")


def main():
    import argparse
    parser = argparse.ArgumentParser(description="高质量 Rick 像素精灵图生成器")
    parser.add_argument("--output", "-o", default=None,
                        help="输出目录 (默认: assets/sprites/rick/)")
    args = parser.parse_args()
    
    if args.output:
        out_dir = args.output
    else:
        script_dir = os.path.dirname(os.path.abspath(__file__))
        out_dir = os.path.join(script_dir, "assets", "sprites", "rick")
    
    os.makedirs(out_dir, exist_ok=True)
    
    print("\n🧪 生成高质量 Rick 像素精灵图...\n")
    
    animations = {
        "idle": 4,
        "walk": 8,
        "surprised": 2,
        "sleep": 2,
        "grabbed": 2,
        "fall": 4,
    }
    
    for name, frames in animations.items():
        path = os.path.join(out_dir, f"{name}.png")
        generate_sprite_sheet(name, frames, path)
    
    # 写 config.json
    from sprite_engine import SpriteEngine
    SpriteEngine.create_default_config(out_dir)
    
    print(f"\n✅ 精灵图已生成到: {out_dir}")
    print("  运行 python main.py 启动桌面宠物")


if __name__ == "__main__":
    main()
