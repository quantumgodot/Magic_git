# modules/duel_3_dodge.py
import sys
import os
import cv2
import pygame
import numpy as np
import random
import time
from ultralytics import YOLO

# 确保能找到根目录的 config
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import BASE_DIR, CAM_WIDTH, CAM_HEIGHT

# ---------- 全局 YOLO 人脸检测器 ----------
_face_detector = None

def _get_face_detector():
    global _face_detector
    if _face_detector is None:
        model_path = os.path.join(BASE_DIR,  "models", "yolov8n-face.pt")  # 修正文件名
        print("正在加载 YOLOv8-Face 模型...")
        _face_detector = YOLO(model_path)
        print("模型加载完成！")
    return _face_detector

# ---------- 字体工具 ----------
def get_game_font(size=36, lang="zh"):
    if lang == "zh":
        font_path = os.path.join(BASE_DIR, "assets", "fonts", "zh.ttf")   # 你的中文字体
    else:
        font_path = os.path.join(BASE_DIR, "assets", "fonts", "HARRY.ttf") # 英文字体
    if not os.path.exists(font_path):
        raise FileNotFoundError(f"字体文件不存在: {font_path}")
    return pygame.font.Font(font_path, size)

def draw_text_with_bg(screen, text, font, pos, text_color=(255,255,255), bg_color=(0,0,0,180)):
    text_surf = font.render(text, True, text_color)
    text_rect = text_surf.get_rect(topleft=pos)
    bg_rect = text_rect.inflate(20, 10)
    bg_surf = pygame.Surface(bg_rect.size, pygame.SRCALPHA)
    bg_surf.fill(bg_color)
    screen.blit(bg_surf, bg_rect.topleft)
    screen.blit(text_surf, text_rect.topleft)

# ---------- 火球类 ----------
class Fireball:
    def __init__(self, pos, target):
        self.x, self.y = pos
        self.speed = 5
        self.target = target
        self.radius = 15

    def move_towards(self):
        tx, ty = self.target
        dx = tx - self.x
        dy = ty - self.y
        dist = np.sqrt(dx**2 + dy**2)
        if dist > 0:
            self.x += self.speed * dx / dist
            self.y += self.speed * dy / dist

    def collides_with(self, rect):
        rx, ry, rw, rh = rect
        cx, cy = self.x, self.y
        closest_x = max(rx, min(cx, rx + rw))
        closest_y = max(ry, min(cy, ry + rh))
        dist = np.sqrt((cx - closest_x)**2 + (cy - closest_y)**2)
        return dist < self.radius

# ---------- 主游戏函数 ----------
def dodge_fireballs(cap, screen):
    """躲避火球，5条命，每2秒回1血，坚持30秒胜利"""
    clock = pygame.time.Clock()
    font = get_game_font(28, "zh")
    fireballs = []
    start_time = time.time()
    game_duration = 30

    max_health = 5
    health = max_health
    last_heal_time = start_time

    head_center = (CAM_WIDTH // 2, CAM_HEIGHT // 2)
    head_bbox = None

    detector = _get_face_detector()

    cam_x = 20
    cam_y = 50

    ui_x = cam_x + CAM_WIDTH + 20
    ui_y = cam_y
    bar_width = 200
    bar_height = 20

    while time.time() - start_time < game_duration:
        # 退出事件
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False
            if event.type == pygame.KEYDOWN and event.key == pygame.K_q:
                return False

        ret, frame = cap.read()
        if not ret:
            break
        frame = cv2.flip(frame, 1)

        # YOLO人脸检测
        results = detector(frame, verbose=False, imgsz=320)
        head_bbox = None
        if results[0].boxes is not None and len(results[0].boxes) > 0:
            boxes = results[0].boxes.data.cpu().numpy()
            boxes = boxes[boxes[:, 4].argsort()[::-1]]
            best = boxes[0]
            x1, y1, x2, y2 = best[0:4].astype(int)
            conf = best[4]
            if conf > 0.3 and (x2 - x1) > 10 and (y2 - y1) > 10:
                w = x2 - x1
                h = y2 - y1
                head_bbox = (x1, y1, w, h)
                head_center = (x1 + w // 2, y1 + h // 2)
                cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)

        # 回血机制
        now = time.time()
        if now - last_heal_time >= 2.0:
            if health < max_health:
                health += 1
            last_heal_time = now

        # 生成火球
        if random.random() < 0.03:
            side = random.choice(['top', 'bottom', 'left', 'right'])
            if side == 'top':
                pos = (random.randint(0, CAM_WIDTH), 0)
            elif side == 'bottom':
                pos = (random.randint(0, CAM_WIDTH), CAM_HEIGHT)
            elif side == 'left':
                pos = (0, random.randint(0, CAM_HEIGHT))
            else:
                pos = (CAM_WIDTH, random.randint(0, CAM_HEIGHT))
            fireballs.append(Fireball(pos, head_center))

        # 火球移动与碰撞
        for fb in fireballs[:]:
            fb.move_towards()
            cv2.circle(frame, (int(fb.x), int(fb.y)), fb.radius, (0, 0, 255), -1)
            if head_bbox and fb.collides_with(head_bbox):
                health -= 1
                fireballs.remove(fb)
                if health <= 0:
                    return False

        # 清屏并绘制摄像头画面
        screen.fill((0, 0, 0))
        small = cv2.resize(frame, (CAM_WIDTH, CAM_HEIGHT))
        small_rgb = cv2.cvtColor(small, cv2.COLOR_BGR2RGB)
        small_rgb = np.transpose(small_rgb, (1, 0, 2))
        frame_surf = pygame.surfarray.make_surface(small_rgb)
        screen.blit(frame_surf, (cam_x, cam_y))

        # 绘制血条
        pygame.draw.rect(screen, (60, 60, 60), (ui_x, ui_y, bar_width, bar_height))
        current_bar_width = int(bar_width * (health / max_health))
        pygame.draw.rect(screen, (200, 50, 50), (ui_x, ui_y, current_bar_width, bar_height))
        draw_text_with_bg(screen, f"血量: {health}/{max_health}", font, (ui_x, ui_y - 25))

        # 剩余时间
        remaining = int(game_duration - (time.time() - start_time))
        draw_text_with_bg(screen, f"剩余 {remaining} 秒", font, (ui_x, ui_y + bar_height + 10))

        pygame.display.flip()
        clock.tick(15)

    return True