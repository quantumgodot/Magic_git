import sys
import os
sys.path.append(os.path.dirname(__file__))

import cv2
import pygame
from modules.duel_1_rps import rock_paper_scissors_duel, cleanup_hand_landmarker, get_game_font, draw_text_with_bg

pygame.init()
screen = pygame.display.set_mode((800, 600))
pygame.display.set_caption("石头剪刀布测试")
clock = pygame.time.Clock()

cap = cv2.VideoCapture(0)
if not cap.isOpened():
    print("摄像头打不开")
    exit()

win = False
try:
    win = rock_paper_scissors_duel(cap, screen)
except Exception as e:
    import traceback
    traceback.print_exc()
finally:
    cap.release()
    cleanup_hand_landmarker()

# ========== 结果展示画面 ==========
font_large = get_game_font(48, "zh")
font_small = get_game_font(28, "zh")

while True:
    screen.fill((20, 0, 50))   # 深色魔法背景

    if win:
        title = font_large.render("🎉 你击败了三头怪！", True, (255, 215, 0))
    else:
        title = font_large.render("💀 三头怪赢了...", True, (180, 180, 180))

    hint = font_small.render("按 Q 键退出", True, (255, 255, 255))

    screen.blit(title, title.get_rect(center=(400, 200)))
    screen.blit(hint, hint.get_rect(center=(400, 320)))
    pygame.display.flip()

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
            exit()
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_q:
                pygame.quit()
                exit()

    clock.tick(30)