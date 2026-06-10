import sys
import os
sys.path.append(os.path.dirname(__file__))

import pygame
import cv2
from modules.duel_3_dodge import dodge_fireballs
from config import WIN_WIDTH, WIN_HEIGHT, CAM_WIDTH, CAM_HEIGHT

pygame.init()
screen = pygame.display.set_mode((WIN_WIDTH, WIN_HEIGHT))
pygame.display.set_caption("躲避火球")
cap = cv2.VideoCapture(0)
cap.set(cv2.CAP_PROP_FRAME_WIDTH, CAM_WIDTH)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, CAM_HEIGHT)

if not cap.isOpened():
    print("摄像头打不开"); exit()

win = dodge_fireballs(cap, screen)
print("胜利" if win else "失败")

cap.release()
pygame.quit()