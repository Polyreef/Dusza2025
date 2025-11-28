import pygame
import pygame_gui

import game


class MenuScene:
    def __init__(self, screen, scene_manager):
        self.screen = screen
        self.scene_manager = scene_manager

        self.manager = None

        self.background = None
        self.start_btn = None
        self.load_btn = None
        self.options_btn = None
        self.quit_btn = None

    def rescale(self, new_scaling):
        game.scaling = new_scaling
        self.cleanup()
        self.setup()

    def setup(self):
        self.manager = pygame_gui.UIManager(
            self.screen.get_size(), "Assets/Themes/menu.json"
        )

        raw_bg = pygame.image.load(
            "Assets/1, MainMenu/MainMenuEmptySizedCorrect.png"
        ).convert_alpha()
        bg_scaled = pygame.transform.smoothscale(raw_bg, self.screen.get_size())

        self.background = pygame_gui.elements.UIImage(
            relative_rect=pygame.Rect(0, 0, *self.screen.get_size()),
            image_surface=bg_scaled,
            manager=self.manager,
        )

        btn_w = 50 * game.scaling
        btn_h = 15 * game.scaling
        spacing = 2 * game.scaling

        total_height = btn_h * 4 + spacing * 3

        start_y = self.screen.get_height() // 2 - total_height // 2 + 35 * game.scaling
        load_y = start_y + (btn_h + spacing)
        options_y = start_y + (btn_h + spacing) * 2
        quit_y = start_y + (btn_h + spacing) * 3

        self.start_btn = pygame_gui.elements.UIButton(
            relative_rect=pygame.Rect(0, start_y, btn_w, btn_h),
            text="",
            manager=self.manager,
            object_id="#start_btn",
            anchors={"centerx": "centerx"},
        )

        self.load_btn = pygame_gui.elements.UIButton(
            relative_rect=pygame.Rect(0, load_y, btn_w, btn_h),
            text="",
            manager=self.manager,
            object_id="#load_btn",
            anchors={"centerx": "centerx"},
        )

        self.options_btn = pygame_gui.elements.UIButton(
            relative_rect=pygame.Rect(0, options_y, btn_w, btn_h),
            text="",
            manager=self.manager,
            object_id="#options_btn",
            anchors={"centerx": "centerx"},
        )

        self.quit_btn = pygame_gui.elements.UIButton(
            relative_rect=pygame.Rect(0, quit_y, btn_w, btn_h),
            text="",
            manager=self.manager,
            object_id="#quit_btn",
            anchors={"centerx": "centerx"},
        )

    def cleanup(self):
        self.manager = None

    def handle_event(self, event):
        if self.manager:
            self.manager.process_events(event)

        if (
            event.type == pygame.USEREVENT
            and event.user_type == pygame_gui.UI_BUTTON_PRESSED
        ):
            if event.ui_element == self.start_btn:
                self.scene_manager.switch_scene("Mode")
            elif event.ui_element == self.load_btn:
                self.scene_manager.switch_scene("Load")
            elif event.ui_element == self.options_btn:
                self.scene_manager.switch_scene("Options")
            elif event.ui_element == self.quit_btn:
                self.scene_manager.quit()

        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            self.scene_manager.quit()

    def update(self, time_delta):
        if self.manager:
            self.manager.update(time_delta)

    def render(self):
        if self.manager:
            self.manager.draw_ui(self.screen)
