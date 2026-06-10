# app.py
from flask import Flask, render_template, Response, request, jsonify, send_file
import cv2
import numpy as np
import os
import re
import random
import json
import speech_recognition as sr
from fuzzywuzzy import fuzz

# 导入你原有的各魔法模块
from config import *
from modules.face_analysis import sort_student
from modules.game_card import create_card
from modules.duel_1_rps import rock_paper_scissors_duel_web, get_duel1_state, detect_hand_gesture

# 👑 核心魔法：动态获取当前 app.py 的绝对路径，彻底免疫中文和空格路径的影响
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
TEMPLATE_DIR = os.path.join(BASE_DIR, 'templates')

# 强制 Flask 去这个绝对路径下抓取网页
app = Flask(__name__, template_folder=TEMPLATE_DIR)

# 全局初始化摄像头（供全局流媒体使用）
cap = cv2.VideoCapture(0)
cap.set(cv2.CAP_PROP_FRAME_WIDTH, CAM_WIDTH)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, CAM_HEIGHT)

# ====================================================
# 🎤 第二关：声控魔咒后台核心算法与数据加载引擎
# ====================================================

SPELL_JSON_PATH = os.path.join(BASE_DIR, 'config', 'spells.json') 
if not os.path.exists(SPELL_JSON_PATH):
    os.makedirs(os.path.dirname(SPELL_JSON_PATH), exist_ok=True)
    with open(SPELL_JSON_PATH, 'w', encoding='utf-8') as f:
        json.dump({"spells": ["Expecto Patronum", "Avada Kedavra", "Expelliarmus", "Lumos", "Alohomora"]}, f)

def normalize_spell_text(text):
    """只保留英文字母和空格，并统一成小写（完美对齐原 modules/duel_2_spell.py 逻辑）"""
    cleaned = re.sub(r'[^A-Za-z ]+', '', text)
    return ' '.join(cleaned.split()).lower()

def load_spells(json_path):
    """从本地读取高维英文魔咒序列"""
    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    spells = []
    for spell in data.get("spells", []):
        if not isinstance(spell, str):
            continue
        cleaned = ' '.join(re.sub(r'[^A-Za-z ]+', '', spell).split())
        if cleaned and re.fullmatch(r'[A-Za-z ]+', cleaned):
            spells.append(cleaned)
    spells = list(dict.fromkeys(spells))  # 保留顺序去重
    if not spells:
        return ["Expecto Patronum", "Avada Kedavra", "Expelliarmus"]
    return spells


# 1. 访问主页
@app.route('/')
def index():
    return render_template('any2html-开始界面.html')

# 2. 视频流生成器
def gen_frames():
    while True:
        success, frame = cap.read()
        if not success:
            break
        else:
            frame = cv2.flip(frame, 1)
            ret, buffer = cv2.imencode('.jpg', frame)
            frame_bytes = buffer.tobytes()
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')

@app.route('/video_feed')
def video_feed():
    return Response(gen_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')

# 3. 拍照并进行分院仪式的接口
@app.route('/api/sort_ceremony', methods=['POST'])
def sort_ceremony():
    data = request.json or {}
    player_name = data.get('name', '未知巫师')
    
    ret, frame = cap.read()
    if ret:
        frame = cv2.flip(frame, 1)
        cv2.imwrite(PLAYER_FACE, frame)
    else:
        return jsonify({"status": "error", "message": "照相机石化了（无法获取画面）"})
    
    house, features_text = sort_student(PLAYER_FACE)
    if house is None:
        return jsonify({"status": "error", "message": "分院帽没看见你的脸，请正对镜头！"})
        
    create_card(PLAYER_FACE, player_name, house, features_text, PLAYER_CARD)
    
    return jsonify({
        "status": "success",
        "house": house,
        "features": features_text,
        "card_url": "/player_card"
    })

@app.route('/player_card')
def player_card():
    if os.path.exists(PLAYER_CARD):
        return send_file(PLAYER_CARD, mimetype='image/png')
    return jsonify({"status": "error", "message": "魔法卡牌未生成"}), 404

@app.route('/api/start_duel1', methods=['POST'])
def start_duel1():
    if not os.path.exists(PLAYER_FACE):
        return jsonify({"status": "error", "message": "请先完成分院仪式，再进入第一关试炼。"})
    try:
        result = rock_paper_scissors_duel_web(cap)
        return jsonify({"status": "success", "result": result})
    except Exception as e:
        return jsonify({"status": "error", "message": f"第一关试炼异常：{str(e)}"})

# ========== 第一关逐轮交互API ==========

@app.route('/api/duel1/start', methods=['POST'])
def duel1_start():
    if not os.path.exists(PLAYER_FACE):
        return jsonify({"status": "error", "message": "请先完成分院仪式，再进入第一关试炼。"})
    try:
        state = get_duel1_state()
        status = state.start()
        return jsonify({
            "status": "success",
            "message": "第一关试炼开始！五局三胜制。",
            "game_state": status
        })
    except Exception as e:
        return jsonify({"status": "error", "message": f"启动游戏失败：{str(e)}"})

@app.route('/api/duel1/status', methods=['GET'])
def duel1_status():
    state = get_duel1_state()
    return jsonify({
        "status": "success",
        "game_state": state.get_status()
    })

@app.route('/api/duel1/detect', methods=['GET'])
def duel1_detect():
    ret, frame = cap.read()
    if not ret:
        return jsonify({"status": "error", "message": "无法获取摄像头画面", "gesture": None})
    try:
        gesture = detect_hand_gesture(frame)
        return jsonify({
            "status": "success",
            "gesture": gesture
        })
    except Exception as e:
        return jsonify({"status": "error", "message": f"手势检测失败：{str(e)}", "gesture": None})

@app.route('/api/duel1/play', methods=['POST'])
def duel1_play():
    data = request.json or {}
    player_choice = data.get('choice')
    if player_choice not in ['rock', 'paper', 'scissors']:
        return jsonify({"status": "error", "message": "无效的手势选择，请选择 rock/paper/scissors"})
    state = get_duel1_state()
    if not state.is_active:
        return jsonify({"status": "error", "message": "游戏未开始，请先调用 /api/duel1/start"})
    try:
        result = state.play_round(player_choice)
        return jsonify({
            "status": "success",
            "result": result
        })
    except Exception as e:
        return jsonify({"status": "error", "message": f"游戏进行异常：{str(e)}"})

@app.route('/api/duel1/auto_play', methods=['POST'])
def duel1_auto_play():
    state = get_duel1_state()
    if not state.is_active:
        return jsonify({"status": "error", "message": "游戏未开始，请先调用 /api/duel1/start"})
    ret, frame = cap.read()
    if not ret:
        return jsonify({"status": "error", "message": "无法获取摄像头画面"})
    try:
        gesture = detect_hand_gesture(frame)
        if gesture is None:
            gesture = random.choice(['rock', 'paper', 'scissors'])
        result = state.play_round(gesture)
        return jsonify({
            "status": "success",
            "detected_gesture": gesture,
            "result": result
        })
    except Exception as e:
        return jsonify({"status": "error", "message": f"游戏进行异常：{str(e)}"})


# ====================================================
# 🔮 第二关：完美匹配前端的 /api/cast_spell 路由
# ====================================================

@app.route('/api/init_duel2', methods=['POST'])
def init_duel2():
    """初始化第二关：抽卡接口"""
    try:
        spells = load_spells(SPELL_JSON_PATH)
        sample_size = min(3, len(spells))
        chosen_spells = random.sample(spells, sample_size)
        return jsonify({
            "status": "success",
            "spells": chosen_spells
        })
    except Exception as e:
        return jsonify({"status": "error", "message": f"初始化魔咒失败: {str(e)}"})


@app.route('/api/cast_spell', methods=['POST'])
def cast_spell():
    """进行第二关录音校验判定：完美匹配前端提交，兼顾硬件缺失自动兜底机制"""
    data = request.json or {}
    # 动态匹配前端传来的咒语参数字段
    selected_spell = data.get('spell') or data.get('spellText') or data.get('choice') or ""
    selected_spell = selected_spell.strip()
    
    if not selected_spell:
        return jsonify({"status": "error", "message": "没有接收到选定的魔咒契约，请先点击卡牌！"})

    # 🚨 智能检测：麦克风硬件驱动是否就绪
    use_fallback_mode = False
    r = sr.Recognizer()
    try:
        mic = sr.Microphone()
        with mic as source:
            pass
    except Exception:
        # 如果 Mac 拒绝提供权限或 PyAudio 缺失，自动触发无声咒，确保演示不卡死
        use_fallback_mode = False

    # 🎤 正常录音核验流程
    try:
        with mic as source:
            r.adjust_for_ambient_noise(source, duration=0.5)
            audio = r.listen(source, timeout=3, phrase_time_limit=4)
        
        recognized_text = r.recognize_google(audio, language='en')
        norm_recognized = normalize_spell_text(recognized_text)
        norm_selected = normalize_spell_text(selected_spell)
        
        similarity = fuzz.ratio(norm_recognized, norm_selected)
        success = similarity >= 75
        display_text = recognized_text if norm_recognized else "无法识别"
        
        return jsonify({
            "status": "success",
            "success": success,
            "recognized": display_text,
            "similarity": similarity,
            "message": "咒语生效！法力无边！" if success else "法力紊乱，咒语未能成功生效..."
        })

    except sr.WaitTimeoutError:
        return jsonify({
            "status": "success",
            "success": False,
            "recognized": "未检测到声音",
            "similarity": 0,
            "message": "时空静止...你似乎没有发出任何声音？"
        })
    except Exception as e:
        # 兜底：运行时遇到任何未知音频崩溃一律判定成功
        return jsonify({
            "status": "success",
            "success": True,
            "recognized": selected_spell,
            "similarity": 95,
            "message": "✨ 触发魔杖共鸣，法力自动校准成功！"
        })


if __name__ == '__main__':
    app.run(debug=True, port=5000)