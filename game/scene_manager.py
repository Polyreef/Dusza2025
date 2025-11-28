import pygame

import game


class SceneManager:
    def __init__(self, screen):
        self.screen = screen

        self.scenes = {}
        self.current_scene = None

        self.clock = pygame.time.Clock()
        self.is_running = True

    def add_scene(self, scene_name, scene):
        self.scenes[scene_name] = scene

    def switch_scene(self, scene_name):
        if self.current_scene:
            self.current_scene.cleanup()

        self.current_scene = self.scenes.get(scene_name)

        if self.current_scene:
            self.current_scene.setup()

    def quit(self):
        self.is_running = False

    def run_frame(self):
        time_delta = self.clock.tick(60) / 1000.0

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.quit()
            elif self.current_scene:
                self.current_scene.handle_event(event)

        if self.current_scene:
            self.current_scene.update(time_delta)
            self.current_scene.render()

    def scale_screen(self, new_scaling):
        game.scaling = new_scaling
        self.screen = pygame.display.set_mode(
            (game.WINDOW_WIDTH * game.scaling, game.WINDOW_HEIGHT * game.scaling)
        )
        if self.current_scene:
            self.current_scene.rescale(game.scaling)
