# modules/scene_manager.py
import pygame
import time

def show_text_scene(screen, lines, color=(255,255,255), wait=2):
    """逐行显示文字，用于剧情/转场"""
    font = pygame.font.SysFont("simhei", 30)
    screen.fill((10, 0, 30))
    y = 100
    for line in lines:
        text = font.render(line, True, color)
        screen.blit(text, (50, y))
        y += 40
    pygame.display.flip()
    pygame.time.wait(wait * 1000)