import os

# Ne írja ki az üdvözlő üzenetet.
os.environ["PYGAME_HIDE_SUPPORT_PROMPT"] = "hide"


import pygame

from .classes.titlescreen import TitleScreen


def run_ui_mode():
    pygame.init()
    pygame.font.init()

    pygame.display.set_caption("Damareen")

    width = 1600
    height = 900

    win = pygame.display.set_mode((width, height))

    titlescreen = TitleScreen(win, width, height)
    titlescreen.run()

    pygame.quit()
