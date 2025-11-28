import pygame
import pygame_gui

import game


class ModeScene:
    def __init__(self, screen, scene_manager):
        self.screen = screen
        self.scene_manager = scene_manager
        self.manager = None

        self.background = None
        self.popup = None
        self.player_btn = None
        self.master_btn = None
        self.back_btn = None

    def rescale(self, new_scaling):
        game.scaling = new_scaling
        self.cleanup()
        self.setup()

    def setup(self):
        self.manager = pygame_gui.UIManager(
            self.screen.get_size(), "Assets/Themes/mode.json"
        )

        raw_bg = pygame.image.load(
            "Assets/1, MainMenu/MainMenuEmptySizedCorrect.png"
        ).convert_alpha()
        bg_scaled = pygame.transform.smoothscale(raw_bg, self.screen.get_size())

        overlay = pygame.Surface(bg_scaled.get_size(), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 128))
        bg_dark = bg_scaled.copy()
        bg_dark.blit(overlay, (0, 0))

        self.background = pygame_gui.elements.UIImage(
            relative_rect=pygame.Rect(0, 0, *self.screen.get_size()),
            image_surface=bg_dark,
            manager=self.manager,
        )

        raw_popup = pygame.image.load(
            "Assets/2, Admin or Player/PlayerOrAdminPopUp.png"
        ).convert_alpha()
        popup_w = self.screen.get_width() // 2
        popup_h = self.screen.get_height() // 2
        popup_scaled = pygame.transform.smoothscale(raw_popup, (popup_w, popup_h))

        popup_rect = pygame.Rect(
            self.screen.get_width() // 2 - popup_w // 2,
            self.screen.get_height() // 2 - popup_h // 2,
            popup_w,
            popup_h,
        )

        self.popup = pygame_gui.elements.UIPanel(
            relative_rect=popup_rect,
            manager=self.manager,
        )

        self.popup_image = pygame_gui.elements.UIImage(
            relative_rect=pygame.Rect(0, 0, popup_w, popup_h),
            image_surface=popup_scaled,
            manager=self.manager,
            container=self.popup,
        )

        btn_w = 50 * game.scaling
        btn_h = 15 * game.scaling
        spacing = 2 * game.scaling

        total_height = btn_h * 2 + spacing

        player_y = popup_h // 2 - total_height // 2 + 10 * game.scaling
        master_y = player_y + (btn_h + spacing)

        popup_rect = self.popup.get_relative_rect()
        back_y = popup_rect.bottom + 10 * game.scaling

        self.player_btn = pygame_gui.elements.UIButton(
            relative_rect=pygame.Rect(0, player_y, btn_w, btn_h),
            text="",
            manager=self.manager,
            object_id="#player_btn",
            container=self.popup,
            anchors={"centerx": "centerx"},
        )

        self.master_btn = pygame_gui.elements.UIButton(
            relative_rect=pygame.Rect(0, master_y, btn_w, btn_h),
            text="",
            manager=self.manager,
            object_id="#master_btn",
            container=self.popup,
            anchors={"centerx": "centerx"},
        )

        self.back_btn = pygame_gui.elements.UIButton(
            relative_rect=pygame.Rect(0, back_y, btn_w, btn_h),
            text="",
            manager=self.manager,
            object_id="#back_btn",
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
            if event.ui_element == self.player_btn:
                self.scene_manager.switch_scene("Player")
            elif event.ui_element == self.master_btn:
                self.scene_manager.switch_scene("Master")
            elif event.ui_element == self.back_btn:
                self.scene_manager.switch_scene("Menu")

        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            self.scene_manager.quit()

    def update(self, time_delta):
        if self.manager:
            self.manager.update(time_delta)

    def render(self):
        if self.manager:
            self.manager.draw_ui(self.screen)
