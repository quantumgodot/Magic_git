# modules/duel_2_spell.py
import re
import speech_recognition as sr
from fuzzywuzzy import fuzz
import json
import random
import pygame
import time

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
    chosen = random.sample(spells, 3)
    target = random.choice(chosen)

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