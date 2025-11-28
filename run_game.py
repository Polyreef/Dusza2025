import os

# Ne írja ki az üdvözlő üzenetet.
os.environ["PYGAME_HIDE_SUPPORT_PROMPT"] = "hide"

import pygame

import game

from core.storage import load_environment_from_file

from game.scene_manager import SceneManager

from game.scenes.menu_scene import MenuScene
from game.scenes.mode_scene import ModeScene


def run_ui_mode():
    environment = load_environment_from_file("Assets/classic.json")

    pygame.init()

    pygame.display.set_caption("Damareen")

    screen = pygame.display.set_mode(
        (game.WINDOW_WIDTH * game.scaling, game.WINDOW_HEIGHT * game.scaling)
    )

    scene_manager = SceneManager(screen)

    menu_scene = MenuScene(screen, scene_manager)
    scene_manager.add_scene("Menu", menu_scene)

    mode_scene = ModeScene(screen, scene_manager)
    scene_manager.add_scene("Mode", mode_scene)

    scene_manager.switch_scene("Menu")

    while scene_manager.is_running:
        scene_manager.run_frame()
        pygame.display.flip()

    pygame.quit()
