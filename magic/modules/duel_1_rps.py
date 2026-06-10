# modules/duel_1_rps.py
import sys
import os
import cv2
import mediapipe as mp
from mediapipe.tasks import python as mp_python
from mediapipe.tasks.python import vision as mp_vision
import random
import time
import numpy as np

# 确保能找到根目录的 config 模块
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import BASE_DIR, CAM_WIDTH, CAM_HEIGHT

# ---------- 模型路径 ----------
MODEL_PATH = os.path.join(BASE_DIR, "models", "hand_landmarker.task")

# ---------- 全局 HandLandmarker 单例 ----------
_hand_landmarker = None

def _get_hand_landmarker():
    global _hand_landmarker
    if _hand_landmarker is None:
        base_options = mp_python.BaseOptions(model_asset_path=MODEL_PATH)
        options = mp_vision.HandLandmarkerOptions(
            base_options=base_options,
            running_mode=mp_vision.RunningMode.VIDEO,
            num_hands=1,
            min_hand_detection_confidence=0.7,
            min_hand_presence_confidence=0.7,
            min_tracking_confidence=0.7,
        )
        _hand_landmarker = mp_vision.HandLandmarker.create_from_options(options)
    return _hand_landmarker

def cleanup_hand_landmarker():
    """游戏退出时释放资源"""
    global _hand_landmarker
    if _hand_landmarker:
        _hand_landmarker.close()
        _hand_landmarker = None

# ---------- 字体工具 ----------
def get_game_font(size=36, lang="zh"):
    """加载魔法字体，中文用自定义字体，英文用 HarryP"""
    import pygame
    if lang == "zh":
        # 请替换成你的实际中文字体文件名
        font_path = os.path.join(BASE_DIR, "assets", "fonts", "zh.ttf")
    else:
        font_path = os.path.join(BASE_DIR, "assets", "fonts", "HARRY.ttf")

    if not os.path.exists(font_path):
        raise FileNotFoundError(f"字体文件不存在: {font_path}")
    return pygame.font.Font(font_path, size)

def draw_text_with_bg(screen, text, font, pos, text_color=(255,255,255), bg_color=(0,0,0,180)):
    """绘制带半透明背景框的文字，避免重叠和混杂"""
    import pygame
    text_surf = font.render(text, True, text_color)
    text_rect = text_surf.get_rect(topleft=pos)
    # 背景框稍微比文字大一点
    bg_rect = text_rect.inflate(20, 10)
    bg_surf = pygame.Surface(bg_rect.size, pygame.SRCALPHA)
    bg_surf.fill(bg_color)
    screen.blit(bg_surf, bg_rect.topleft)
    screen.blit(text_surf, text_rect.topleft)

# ---------- 掌心球手势识别 ----------
def compute_palm_circle(hand_landmarks, width, height):
    """利用手腕(0)、中指根部(9)、小指根部(13)确定掌心圆心与半径"""
    indices = [0, 9, 13]
    pts = []
    for i in indices:
        lm = hand_landmarks[i]
        pts.append([lm.x * width, lm.y * height])
    pts = np.array(pts, dtype=np.float32)
    center = pts.mean(axis=0)
    radius = np.linalg.norm(pts - center, axis=1).max() * 0.85
    return center, radius

def is_finger_straight(hand_landmarks, tip_idx, center, radius, width, height):
    """指尖到掌心圆心距离 > 半径 → 伸直，否则弯曲"""
    lm = hand_landmarks[tip_idx]
    pt = np.array([lm.x * width, lm.y * height])
    dist = np.linalg.norm(pt - center)
    return dist > radius

def classify_gesture(hand_landmarks, width, height):
    """根据五根手指的弯曲状态判断石头剪刀布"""
    if hand_landmarks is None:
        return None
    center, radius = compute_palm_circle(hand_landmarks, width, height)
    tips = [4, 8, 12, 16, 20]   # 拇指尖, 食指尖, 中指尖, 无名指尖, 小指尖
    states = [is_finger_straight(hand_landmarks, t, center, radius, width, height) for t in tips]
    straight_count = sum(states)

    if straight_count == 0:
        return "rock"
    elif straight_count == 5:
        return "paper"
    elif states[1] and states[2] and straight_count == 2:   # 只有食指和中指伸直
        return "scissors"
    else:
        return "unknown"


# ---------- Web游戏状态管理 ----------
class Duel1GameState:
    """第一关游戏状态管理类"""
    def __init__(self, target_wins=3, max_rounds=5):
        self.target_wins = target_wins
        self.max_rounds = max_rounds
        self.player_wins = 0
        self.monster_wins = 0
        self.round_num = 1
        self.rounds = []
        self.is_active = False
        self.choices = ["rock", "paper", "scissors"]
    
    def start(self):
        """开始新游戏"""
        self.player_wins = 0
        self.monster_wins = 0
        self.round_num = 1
        self.rounds = []
        self.is_active = True
        return self.get_status()
    
    def get_status(self):
        """获取当前游戏状态"""
        return {
            "is_active": self.is_active,
            "round_num": self.round_num,
            "player_wins": self.player_wins,
            "monster_wins": self.monster_wins,
            "target_wins": self.target_wins,
            "max_rounds": self.max_rounds,
            "is_finished": self.player_wins >= self.target_wins or self.monster_wins >= self.target_wins or self.round_num > self.max_rounds,
            "overall_win": self.player_wins > self.monster_wins if (self.player_wins >= self.target_wins or self.monster_wins >= self.target_wins or self.round_num > self.max_rounds) else None,
            "rounds": self.rounds
        }
    
    def play_round(self, player_choice):
        """进行一轮游戏"""
        if not self.is_active:
            return {"error": "游戏未开始"}
        
        if self.player_wins >= self.target_wins or self.monster_wins >= self.target_wins or self.round_num > self.max_rounds:
            return {"error": "游戏已结束", "status": self.get_status()}
        
        # 三头怪随机出招
        monster_choice = random.choice(self.choices)
        
        # 判断胜负
        if player_choice == monster_choice:
            result = "draw"
            message = f"平局！你和三头怪都出 {player_choice}"
        elif (player_choice == "rock" and monster_choice == "scissors") or \
             (player_choice == "scissors" and monster_choice == "paper") or \
             (player_choice == "paper" and monster_choice == "rock"):
            self.player_wins += 1
            result = "player"
            message = f"你赢了！你出 {player_choice}，三头怪出 {monster_choice}"
        else:
            self.monster_wins += 1
            result = "monster"
            message = f"三头怪赢了！你出 {player_choice}，他出 {monster_choice}"
        
        round_data = {
            "round": self.round_num,
            "player_choice": player_choice,
            "monster_choice": monster_choice,
            "result": result,
            "message": message
        }
        self.rounds.append(round_data)
        self.round_num += 1
        
        # 检查游戏是否结束
        is_finished = self.player_wins >= self.target_wins or self.monster_wins >= self.target_wins or self.round_num > self.max_rounds
        if is_finished:
            self.is_active = False
        
        return {
            "round": round_data,
            "status": self.get_status(),
            "is_finished": is_finished,
            "overall_win": self.player_wins > self.monster_wins if is_finished else None
        }

# 全局游戏状态实例
_duel1_state = Duel1GameState()

def get_duel1_state():
    """获取全局游戏状态"""
    return _duel1_state

def detect_hand_gesture(frame):
    """检测单帧图像中的手势，返回识别到的手势类型"""
    if frame is None:
        return None
    
    detector = _get_hand_landmarker()
    frame = cv2.flip(frame, 1)
    h, w = frame.shape[:2]
    rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb)
    timestamp_ms = int(time.time() * 1000)
    results = detector.detect_for_video(mp_image, timestamp_ms)
    
    if results.hand_landmarks:
        gesture = classify_gesture(results.hand_landmarks[0], w, h)
        if gesture in ["rock", "paper", "scissors"]:
            return gesture
    return None


def rock_paper_scissors_duel_web(cap, target_wins=3, max_rounds=5, detection_time=2.5):
    """Web 后端可调用的石头剪刀布对战接口，返回每轮结果和总胜负。"""
    wins_player = 0
    wins_monster = 0
    round_num = 1
    rounds = []
    choices = ["rock", "paper", "scissors"]
    detector = _get_hand_landmarker()

    while wins_player < target_wins and wins_monster < target_wins and round_num <= max_rounds:
        player_choice = None
        start_time = time.time()

        while time.time() - start_time < detection_time:
            ret, frame = cap.read()
            if not ret:
                continue
            frame = cv2.flip(frame, 1)
            h, w = frame.shape[:2]
            rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb)
            timestamp_ms = int(time.time() * 1000)
            results = detector.detect_for_video(mp_image, timestamp_ms)
            if results.hand_landmarks:
                gesture = classify_gesture(results.hand_landmarks[0], w, h)
                if gesture in choices:
                    player_choice = gesture
                    break

        if player_choice is None:
            player_choice = random.choice(choices)

        monster_choice = random.choice(choices)
        if player_choice == monster_choice:
            result = "draw"
            message = f"平局：你和三头怪都出 {player_choice}。"
        elif (player_choice == "rock" and monster_choice == "scissors") or \
             (player_choice == "scissors" and monster_choice == "paper") or \
             (player_choice == "paper" and monster_choice == "rock"):
            wins_player += 1
            result = "player"
            message = f"你赢了！你出 {player_choice}，三头怪出 {monster_choice}。"
        else:
            wins_monster += 1
            result = "monster"
            message = f"三头怪赢了！你出 {player_choice}，他出 {monster_choice}。"

        rounds.append({
            "round": round_num,
            "player_choice": player_choice,
            "monster_choice": monster_choice,
            "result": result,
            "message": message
        })
        round_num += 1

    overall_win = wins_player > wins_monster
    return {
        "player_wins": wins_player,
        "monster_wins": wins_monster,
        "rounds": rounds,
        "overall_win": overall_win,
        "message": "你赢了第一关！继续向下一关进发吧！" if overall_win else "你输了第一关，三头怪笑了。"
    }

# ---------- 主对决函数 ----------
def rock_paper_scissors_duel(cap, screen):
    """五局三胜制，返回True表示玩家赢"""
    clock = pygame.time.Clock()
    font = get_game_font(36, "zh")   # 中文界面
    wins_player = 0
    wins_monster = 0
    round_num = 1
    countdown = 3
    last_time = time.time()
    player_choice = None
    monster_choice = None
    show_result = False
    result_text = ""
    frame_count = 0
    gesture = None  # 初始化手势

    choices = ["rock", "paper", "scissors"]

    while wins_player < 3 and wins_monster < 3:
        # 清屏，防止文字重叠
        screen.fill((0, 0, 0))
        
        ret, frame = cap.read()
        if not ret:
            break
        frame = cv2.flip(frame, 1)
        h, w = frame.shape[:2]

        # 每3帧做一次手势检测，降低延迟感
        frame_count += 1
        if frame_count % 3 == 1:
            rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb)
            detector = _get_hand_landmarker()
            timestamp_ms = int(time.time() * 1000)
            results = detector.detect_for_video(mp_image, timestamp_ms)
            if results.hand_landmarks:
                gesture = classify_gesture(results.hand_landmarks[0], w, h)
            else:
                gesture = None

        # 倒计时与提交
        now = time.time()
        if not show_result:
            if countdown > 0:
                if now - last_time >= 1:
                    countdown -= 1
                    last_time = now
            else:
                player_choice = gesture if gesture in choices else random.choice(choices)
                monster_choice = random.choice(choices)
                if player_choice == monster_choice:
                    result_text = f"平局！ 都出 {player_choice}"
                elif (player_choice == "rock" and monster_choice == "scissors") or \
                     (player_choice == "scissors" and monster_choice == "paper") or \
                     (player_choice == "paper" and monster_choice == "rock"):
                    wins_player += 1
                    result_text = f"你赢！ 你出 {player_choice}，三头怪出 {monster_choice}"
                else:
                    wins_monster += 1
                    result_text = f"三头怪赢！ 你出 {player_choice}，他出 {monster_choice}"
                show_result = True

        # 摄像头画面（缩小后绘制，提升性能）
        small = cv2.resize(frame, (CAM_WIDTH, CAM_HEIGHT))
        small = cv2.cvtColor(small, cv2.COLOR_BGR2RGB)
        small = np.rot90(small)
        frame_surf = pygame.surfarray.make_surface(small)
        screen.blit(frame_surf, (20, 50))

        # 带背景框的文字
        if not show_result:
            draw_text_with_bg(screen, f"第{round_num}局 倒计时:{countdown}  你:{wins_player}  三头怪:{wins_monster}", font, (20, 10))
        else:
            draw_text_with_bg(screen, result_text, font, (20, 10))

        pygame.display.flip()

        if show_result:
            pygame.time.wait(2000)
            show_result = False
            countdown = 3
            last_time = time.time()
            round_num += 1

        clock.tick(30)

    return wins_player == 3
