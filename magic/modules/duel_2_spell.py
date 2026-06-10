# modules/duel_2_spell.py
import re
import speech_recognition as sr
from fuzzywuzzy import fuzz
import json
import random
import pygame
import time

import requests
import json
import random

def generate_spells_by_ai(house_name="Gryffindor"):
    """
    ⚡ 真正的 AI 驱动：链接大语言模型，根据玩家学院动态生成 3 个英文魔咒
    """
    # 💡 这里替换成你申请的大模型 API Key（比如 DeepSeek、智谱、零一万物等）
    API_KEY = "sk-7119646c7c744bac91bcede1b7ae89c1" 
    API_URL = "https://api.deepseek.com/v1/chat/completions" # 或者其他大模型底座 URL

    # 🧙‍♂️ 精心设计的魔法提示词
    prompt = f"""
    You are the Spell Professor at Hogwarts. 
    The user is a wizard from {house_name} house.
    Generate exactly 3 authentic or highly creative Harry Potter universe spells in English that fit this house's character.
    Each spell must be a short English phrase (1-3 words).
    
    You MUST respond with a raw JSON list of strings, containing exactly 3 spells.
    Example output format:
    ["Expecto Patronum", "Wingardium Leviosa", "Expelliarmus"]
    
    Do not inclusion any markdown formatting, do not include ```json, just return the raw JSON array text.
    """

    # 🔒 极其稳固的离线兜底魔咒（防止网络断开或 API 额度耗尽导致游戏崩溃）
    fallback_spells = {
        "Gryffindor": ["Expecto Patronum", "Expelliarmus", "Stupefy"],
        "Slytherin": ["Avada Kedavra", "Crucio", "Crucify"],
        "Ravenclaw": ["Alohomora", "Lumos Maxima", "Expecto Patronum"],
        "Hufflepuff": ["Wingardium Leviosa", "Riddikulus", "Diffindo"]
    }.get(house_name, ["Lumos", "Nox", "Incedio"])

    try:
        headers = {
            "Authorization": f"Bearer {API_KEY}",
            "Content-Type": "application/json"
        }
        payload = {
            "model": "deepseek-chat", # 根据你选的平台修改模型名
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.7
        }
        
        response = requests.post(API_URL, json=payload, headers=headers, timeout=5)
        if response.status_code == 200:
            result = response.json()
            ai_content = result['choices'][0]['message']['content'].strip()
            
            # 清洗可能夹带的 markdown 尾巴
            ai_content = ai_content.replace("```json", "").replace("```", "").strip()
            
            spell_list = json.loads(ai_content)
            if isinstance(spell_list, list) and len(spell_list) >= 3:
                return spell_list[:3] # 完美拿到 AI 生成的 3 个魔咒
                
    except Exception as e:
        print(f"🔮 [魔法波动] AI 魔咒生成失败，已自动触发远古防御咒语（启用本地兜底）: {e}")
        
    # 网络失败或解析失败时，无缝切换到对应学院的本地随机咒语
    return random.sample(fallback_spells, 3)

def normalize_spell_text(text):
    """只保留英文字母和空格，并统一成小写。"""
    cleaned = re.sub(r'[^A-Za-z ]+', '', text)
    return ' '.join(cleaned.split()).lower()

def load_spells(json_path):
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
        raise ValueError("Spell file must contain at least one English spell phrase.")
    return spells

def spell_duel(screen, spell_file):
    """魔法咒语关卡，返回True/False"""
    spells = load_spells(spell_file)
    # 选择三个咒语
    # 直接让 AI 现场吐出 3 个魔咒
    chosen = generate_spells_by_ai("Gryffindor")

    font = pygame.font.SysFont("simhei", 32)
    screen.fill((30, 0, 60))
    y = 100
    texts = [
        "三头怪要求你施展咒语！",
        "请从以下咒语中选择一个并大声念出："
    ]
    for t in texts:
        surf = font.render(t, True, (255,255,255))
        screen.blit(surf, (50, y))
        y += 40

    for i, spell in enumerate(chosen):
        surf = font.render(f"{i+1}. {spell}", True, (200,200,0))
        screen.blit(surf, (100, y))
        y += 35
    pygame.display.flip()

    # 等待玩家选择（这里简化，按数字键1-3选择并自动录音）
    selected = None
    waiting = True
    while waiting:
        for event in pygame.event.get():
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_1:
                    selected = chosen[0]
                    waiting = False
                elif event.key == pygame.K_2:
                    selected = chosen[1]
                    waiting = False
                elif event.key == pygame.K_3:
                    selected = chosen[2]
                    waiting = False

    # 录音识别
    r = sr.Recognizer()
    try:
        mic = sr.Microphone()
    except AttributeError:
        error_text = "未安装 PyAudio，无法使用麦克风。"
        print(error_text)
        screen.fill((30,0,60))
        surf = font.render(error_text, True, (255,0,0))
        screen.blit(surf, (50, 250))
        pygame.display.flip()
        pygame.time.wait(3000)
        return False
    except OSError as e:
        error_text = f"麦克风错误：{e}"
        print(error_text)
        screen.fill((30,0,60))
        surf = font.render(error_text, True, (255,0,0))
        screen.blit(surf, (50, 250))
        pygame.display.flip()
        pygame.time.wait(3000)
        return False

    screen.fill((30,0,60))
    prompt = font.render(f"请说出: {selected}  正在聆听...", True, (255,255,0))
    screen.blit(prompt, (50, 200))
    pygame.display.flip()

    try:
        with mic as source:
            r.adjust_for_ambient_noise(source)
            audio = r.listen(source, timeout=3)
        text = r.recognize_google(audio, language='en')
        norm_text = normalize_spell_text(text)
        norm_selected = normalize_spell_text(selected)
        similarity = fuzz.ratio(norm_text, norm_selected)
        success = similarity >= 75
        text = text if norm_text else "无法识别"
    except Exception as e:
        success = False
        text = "无法识别"

    # 显示结果
    screen.fill((30,0,60))
    if success:
        result_text = f"咒语生效！ 你说: {text}"
        color = (0,255,0)
    else:
        result_text = f"咒语失败... 识别为: {text}"
        color = (255,0,0)
    surf = font.render(result_text, True, color)
    screen.blit(surf, (50, 250))
    pygame.display.flip()
    pygame.time.wait(3000)
    return success