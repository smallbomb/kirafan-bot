import os
os.environ['PYGAME_HIDE_SUPPORT_PROMPT'] = "hide"
import pygame
import threading
import win32api
import win32con
import win32gui
import time
from data import uData


def square():
    game_region = uData.setting['game_region']
    if all(x <= y for x, y in zip(game_region, (0, 0, 1, 1))):
        print('seting.json[game_region]: invaild value')
        exit()
    os.environ['SDL_VIDEO_WINDOW_POS'] = str(game_region[0]) + "," + str(game_region[1])
    size = (game_region[2], game_region[3])
    pygame.init()
    screen = pygame.display.set_mode(size, pygame.NOFRAME) # For borderless, use pygame.NOFRAME
    black = (1, 1, 1)  # Transparency color, can't be (0,0,0) or (255,255,255)
    green = (0, 255, 0)
    surface  = pygame.Surface(size, pygame.SRCALPHA)
    clock = pygame.time.Clock()
    # Create layered window
    hwnd = pygame.display.get_wm_info()["window"]
    win32gui.SetWindowLong(hwnd, win32con.GWL_EXSTYLE,
                           win32gui.GetWindowLong(hwnd, win32con.GWL_EXSTYLE) | win32con.WS_EX_LAYERED)
    win32gui.SetLayeredWindowAttributes(hwnd, win32api.RGB(*black), 0, win32con.LWA_COLORKEY)
    thread = threading.currentThread()
    while thread.is_running():
        clock.tick(60)
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                thread.stop()
        screen.fill(black)  # Transparent background
        pygame.draw.rect(screen, green, surface.get_rect(), 2)
        pygame.display.update()
    pygame.quit()
