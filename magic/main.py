# main.py
import pygame
import cv2
import sys
import os
import numpy as np
from config import *
from modules.face_analysis import sort_student
from modules.game_card import create_card
from modules.duel_1_rps import rock_paper_scissors_duel
from modules.duel_2_spell import spell_duel
from modules.duel_3_dodge import dodge_fireballs
from modules.prank import prank_player
from modules.scene_manager import show_text_scene

pygame.init()
screen = pygame.display.set_mode((WIN_WIDTH, WIN_HEIGHT))
pygame.display.set_caption("魔法试炼")
clock = pygame.time.Clock()
font = pygame.font.SysFont("simhei", 32)

# 打开摄像头
cap = cv2.VideoCapture(0)
cap.set(cv2.CAP_PROP_FRAME_WIDTH, CAM_WIDTH)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, CAM_HEIGHT)

# 播放开始音乐
try:
    pygame.mixer.init()
    pygame.mixer.music.load(MUSIC_START)
    pygame.mixer.music.play(-1)
except:
    pass

def text_input(screen, prompt):
    """简单的pygame文本输入"""
    input_text = ""
    input_active = True
    while input_active:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit(); sys.exit()
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_RETURN:
                    input_active = False
                elif event.key == pygame.K_BACKSPACE:
                    input_text = input_text[:-1]
                else:
                    if len(input_text) < 10 and event.unicode.isprintable():
                        input_text += event.unicode
        screen.fill((30,0,60))
        prompt_surf = font.render(prompt, True, (255,255,255))
        screen.blit(prompt_surf, (50,200))
        name_surf = font.render(input_text, True, (255,255,0))
        screen.blit(name_surf, (50,250))
        pygame.display.flip()
        clock.tick(30)
    return input_text

def main():
    state = "START"
    player_name = ""
    house = ""
    features_text = ""
    card_path = ""

    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                cap.release(); pygame.quit(); sys.exit()

        if state == "START":
            screen.fill((30,0,60))
            # 输入昵称
            player_name = text_input(screen, "请输入你的魔法昵称:")
            # 拍照
            show_text_scene(screen, ["准备拍照，请面对镜头", "按空格键拍照"])
            waiting_capture = True
            while waiting_capture:
                ret, frame = cap.read()
                if ret:
                    frame = cv2.flip(frame, 1)
                    frame_surf = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                    frame_surf = np.rot90(frame_surf)
                    frame_surf = pygame.surfarray.make_surface(frame_surf)
                    screen.blit(pygame.transform.scale(frame_surf, (CAM_WIDTH, CAM_HEIGHT)), (20,50))
                pygame.display.flip()
                for event in pygame.event.get():
                    if event.type == pygame.KEYDOWN and event.key == pygame.K_SPACE:
                        cv2.imwrite(PLAYER_FACE, frame)
                        waiting_capture = False
            # 分院
            show_text_scene(screen, ["分析你的面部特征...", "与魔法世界人物进行匹配..."])
            house, features_text = sort_student(PLAYER_FACE)
            if house is None:
                show_text_scene(screen, ["未检测到人脸，请重新启动"], wait=3)
                continue
            # 生成卡牌
            create_card(PLAYER_FACE, player_name, house, features_text, PLAYER_CARD)
            show_text_scene(screen, ["分院完成！", f"你属于 {house}", features_text], wait=3)
            state = "PLOT"

        elif state == "PLOT":
            # 展示剧情画面
            show_text_scene(screen, ["一只三头怪挡住了去路！", "只有通过他的三重考验才能继续前进。"], wait=3)
            # 切换战斗音乐
            try:
                pygame.mixer.music.load(MUSIC_BATTLE)
                pygame.mixer.music.play(-1)
            except: pass
            state = "DUEL1"

        elif state == "DUEL1":
            show_text_scene(screen, ["第一关：不到十", "石头剪刀布，五局三胜！"], wait=2)
            win1 = rock_paper_scissors_duel(cap, screen)
            if win1:
                show_text_scene(screen, ["你赢了！继续前进"], wait=2)
                state = "DUEL2"
            else:
                show_text_scene(screen, ["你输了！遭受三头怪的嘲笑"], wait=2)
                state = "PRANK"

        elif state == "DUEL2":
            show_text_scene(screen, ["第二关：魔法咒语"], wait=2)
            win2 = spell_duel(screen, SPELLS_FILE)
            if win2:
                show_text_scene(screen, ["咒语击中三头怪！"], wait=2)
                state = "DUEL3"
            else:
                show_text_scene(screen, ["咒语失败！"], wait=2)
                state = "PRANK"

        elif state == "DUEL3":
            show_text_scene(screen, ["第三关：躲避火球", "坚持30秒！"], wait=2)
            win3 = dodge_fireballs(cap, screen)
            if win3:
                show_text_scene(screen, ["你成功躲开了所有火球！", "三头怪认输了！"], wait=3)
                state = "ENDING"
            else:
                show_text_scene(screen, ["被火球击中了！"], wait=2)
                state = "PRANK"

        elif state == "PRANK":
            show_text_scene(screen, ["三头怪给你留下了恶作剧..."], wait=2)
            pranked_img = prank_player()
            if pranked_img:
                img = cv2.imread(pranked_img)
                img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
                img = pygame.surfarray.make_surface(np.rot90(img))
                screen.fill((0,0,0))
                screen.blit(pygame.transform.scale(img, (400,300)), (200,150))
                show_text_scene(screen, ["看看你的脸！哈哈哈哈！"], wait=3)
            state = "RESTART"

        elif state == "ENDING":
            # 胜利结算
            try:
                pygame.mixer.music.load(MUSIC_VICTORY)
                pygame.mixer.music.play()
            except: pass
            card_img = pygame.image.load(PLAYER_CARD)
            screen.fill((0,0,0))
            screen.blit(pygame.transform.scale(card_img, (400,200)), (300,100))
            lines = [
                f"恭喜 {player_name}！",
                f"你已被 {house} 学院正式接纳。",
                "你的勇气与智慧将载入史册！"
            ]
            show_text_scene(screen, lines, color=(255,215,0), wait=4)
            state = "RESTART"

        elif state == "RESTART":
            screen.fill((0,0,0))
            prompt = font.render("按 R 重新开始，按 ESC 退出", True, (255,255,255))
            screen.blit(prompt, (200,300))
            pygame.display.flip()
            waiting = True
            while waiting:
                for event in pygame.event.get():
                    if event.type == pygame.KEYDOWN:
                        if event.key == pygame.K_r:
                            # 重置状态
                            state = "START"
                            waiting = False
                            break
                        elif event.key == pygame.K_ESCAPE:
                            cap.release(); pygame.quit(); sys.exit()

        clock.tick(FPS)

if __name__ == "__main__":
    main()