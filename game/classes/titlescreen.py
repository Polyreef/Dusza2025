import pygame

from .buttonclass import Button


class TitleScreen:
    def __init__(self, screen, screen_width, screen_height):
        self.screen = screen

        self.screen_width = screen_width
        self.screen_height = screen_height

        self.buttons = []

        spacing = screen_height / 10.5

        default_width = self.screen_width / 7
        default_height = screen_height / 13
        default_y = screen_height / 2 + screen_height / 11
        default_x = screen_width / 2

        self.enable_menu_click = True

        self.dict_modes = {
            "game": "Játék",
            "options": "Beállítások",
            "load": "Betöltés",
            "player": "Játékos",
            "gamemaster": "Játékmester",
        }

        self.mode = "menu"
        self.font = pygame.font.SysFont("comicsans", 30)

        self.background_raw = pygame.image.load("Assets/Images/Misc/MainMenuBG.png")

        self.background = pygame.transform.smoothscale(self.background_raw, (screen_width, screen_height))


        self.popup_win_raw = pygame.image.load("Assets/Images/Misc/Popup_window.png")

        popup_scale = 0.6
        popup_scaled_w = int(self.screen_width * popup_scale)
        ratio = popup_scaled_w / self.popup_win_raw.get_width()

        popup_scaled_h = int(self.screen_height * ratio)

        

        self.popup_win_scaled = pygame.transform.smoothscale(
            self.popup_win_raw, (popup_scaled_w, popup_scaled_h)
        )



        self.popup_x = self.screen_width / 2 - popup_scaled_w / 2
        self.popup_y = self.screen_height / 2 - popup_scaled_h / 2

        pgm_button_w = default_width * self.screen_height/1000 * 3
        pgm_button_h = default_height * self.screen_height/1000 * 3
        player_y = self.popup_y + self.popup_y / 2 - self.popup_y / 5
        gamemaster_y = self.popup_y + self.popup_y / 2 + self.popup_y / 3

        player_gm_x = self.screen_width / 2 - pgm_button_w / 2

        self.start_button = Button(
            pos=(default_x - default_width / 2, default_y),
            normal_path="Assets/Images/Buttons/NormalStart.png",
            callback_func=self.start_pressed,
            hover_path="Assets/Images/Buttons/HoverStart.png",
            scale_w=default_width,
            scale_h=default_height,
        )

        self.load_button = Button(
            pos=(default_x - default_width / 2, default_y + spacing),
            normal_path="Assets/Images/Buttons/NormalLoad.png",
            callback_func=self.load_pressed,
            hover_path="Assets/Images/Buttons/HoverLoad.png",
            scale_w=default_width,
            scale_h=default_height,
        )

        self.options_button = Button(
            pos=(default_x - default_width / 2, default_y + spacing * 2),
            normal_path="Assets/Images/Buttons/NormalOption.png",
            callback_func=self.options_pressed,
            hover_path="Assets/Images/Buttons/HoverOption.png",
            scale_w=default_width,
            scale_h=default_height,
        )

        self.quit_button = Button(
            pos=(default_x - default_width / 2, default_y + spacing * 3),
            normal_path="Assets/Images/Buttons/NormalQuit.png",
            callback_func=self.quit_pressed,
            hover_path="Assets/Images/Buttons/HoverQuit.png",
            scale_w=default_width,
            scale_h=default_height,
        )

        self.player_button = Button(
            pos=(player_gm_x, player_y),
            normal_path="Assets/Images/Buttons/NoHoverPlayerNotSized.png",
            callback_func=self.player_pressed,
            hover_path="Assets/Images/Buttons/HoverPlayerNotSized.png",
            scale_w=pgm_button_w,
            scale_h=pgm_button_h,
        )

        self.gamemaster_button = Button(
            pos=(player_gm_x, gamemaster_y),
            normal_path="Assets/Images/Buttons/NoHoverGameMasterNotSized.png",
            callback_func=self.gamemaster_pressed,
            hover_path="Assets/Images/Buttons/HoverGameMasterNotSized.png",
            scale_w=pgm_button_w,
            scale_h=pgm_button_h,
        )

        

        self.buttons.append(self.start_button)
        self.buttons.append(self.load_button)
        self.buttons.append(self.options_button)
        self.buttons.append(self.quit_button)

        self.running = True

    def start_pressed(self):
        self.mode = "game"

        overlay = pygame.Surface((self.screen_width, self.screen_height))
        overlay.set_alpha(230)
        overlay.fill((20, 20, 20))
        self.screen.blit(overlay, (0, 0))
        self.screen.blit(
            self.popup_win_scaled,
            (
                self.popup_x,
                self.popup_y
            ),
        )

        self.enable_menu_click = False

    def load_pressed(self):
        self.mode = "load"

    def options_pressed(self):
        self.mode = "options"

    def quit_pressed(self):
        self.running = False

    def player_pressed(self):
        self.mode = "player"

    def gamemaster_pressed(self):
        self.mode = "gamemaster"

    def _drawmode(self):
        if self.mode != "menu" and self.mode != "game":
            self.screen.fill("black")
            title = f"{self.dict_modes[self.mode].upper()} MÓD"
            text = self.font.render(title, 1, "white")
            self.screen.blit(
                text,
                (
                    self.screen_width / 2 - text.get_width() / 2,
                    self.screen_height / 2 - text.get_height() / 2,
                ),
            )

            info = self.font.render("Nyomj ESC-et a visszatéréshez", 1, "white")
            self.screen.blit(
                info,
                (
                    self.screen_width / 2 - info.get_width() / 2,
                    self.screen_height / 2 - text.get_height() / 2 + 60,
                ),
            )

    def run(self):
        clock = pygame.time.Clock()

        while self.running:
            clock.tick(60)

            mouse_pos = pygame.mouse.get_pos()

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False

                if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    if self.enable_menu_click:
                        for button in self.buttons:
                            if button.b_hover == True:
                                button.do_callback()

                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        self.mode = "menu"
                        self.enable_menu_click = True

            if self.mode == "menu":
                self.screen.blit(self.background, (0, 0))

                for button in self.buttons:
                    button.update(mouse_pos)
                    button.screen_update(self.screen)

            elif self.mode == "game":
                self.player_button.update(mouse_pos)
                self.player_button.screen_update(self.screen)
                self.gamemaster_button.update(mouse_pos)
                self.gamemaster_button.screen_update(self.screen)

            else:
                self._drawmode()

            pygame.display.flip()
