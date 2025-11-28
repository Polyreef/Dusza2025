import pygame
import pygame_gui

import game


class PlayerScene:
    def __init__(self, screen, scene_manager, environment):
        self.screen = screen
        self.scene_manager = scene_manager
        self.environment = environment
        self.manager = None

        self.background = None
        self.battle_btn = None
        self.back_btn = None
        self.simple_cards = []

    def rescale(self, new_scaling):
        game.scaling = new_scaling
        self.cleanup()
        self.setup()

    def setup(self):
        self.manager = pygame_gui.UIManager(
            self.screen.get_size(), "Assets/Themes/player.json"
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

        card_w = 25 * game.scaling
        card_h = 35 * game.scaling

        card_earth = []
        card_air = []
        card_water = []
        card_fire = []

        raw_earth_1 = pygame.image.load("Assets/4, Inventory/Cards/EarthwKnight1.png")
        raw_earth_2 = pygame.image.load("Assets/4, Inventory/Cards/EarthwKnight2.png")
        raw_earth_3 = pygame.image.load("Assets/4, Inventory/Cards/EarthwKnight3.png")
        raw_earth_4 = pygame.image.load("Assets/4, Inventory/Cards/EarthwKnight4.png")
        card_earth.append(pygame.transform.smoothscale(raw_earth_1, (card_w, card_h)))
        card_earth.append(pygame.transform.smoothscale(raw_earth_2, (card_w, card_h)))
        card_earth.append(pygame.transform.smoothscale(raw_earth_3, (card_w, card_h)))
        card_earth.append(pygame.transform.smoothscale(raw_earth_4, (card_w, card_h)))

        raw_air_1 = pygame.image.load("Assets/4, Inventory/Cards/WindwArcher1.png")
        raw_air_2 = pygame.image.load("Assets/4, Inventory/Cards/WindwArcher2.png")
        raw_air_3 = pygame.image.load("Assets/4, Inventory/Cards/WindwArcher3.png")
        raw_air_4 = pygame.image.load("Assets/4, Inventory/Cards/WindwArcher4.png")
        card_air.append(pygame.transform.smoothscale(raw_air_1, (card_w, card_h)))
        card_air.append(pygame.transform.smoothscale(raw_air_2, (card_w, card_h)))
        card_air.append(pygame.transform.smoothscale(raw_air_3, (card_w, card_h)))
        card_air.append(pygame.transform.smoothscale(raw_air_4, (card_w, card_h)))

        raw_water_1 = pygame.image.load("Assets/4, Inventory/Cards/WaterwSchema1.png")
        raw_water_2 = pygame.image.load("Assets/4, Inventory/Cards/WaterwSchema2.png")
        raw_water_3 = pygame.image.load("Assets/4, Inventory/Cards/WaterwSchema3.png")
        raw_water_4 = pygame.image.load("Assets/4, Inventory/Cards/WaterwSchema4.png")
        card_water.append(pygame.transform.smoothscale(raw_water_1, (card_w, card_h)))
        card_water.append(pygame.transform.smoothscale(raw_water_2, (card_w, card_h)))
        card_water.append(pygame.transform.smoothscale(raw_water_3, (card_w, card_h)))
        card_water.append(pygame.transform.smoothscale(raw_water_4, (card_w, card_h)))

        raw_fire_1 = pygame.image.load("Assets/4, Inventory/Cards/FirewHorse1.png")
        raw_fire_2 = pygame.image.load("Assets/4, Inventory/Cards/FirewHorse2.png")
        raw_fire_3 = pygame.image.load("Assets/4, Inventory/Cards/FirewHorse3.png")
        raw_fire_4 = pygame.image.load("Assets/4, Inventory/Cards/FirewHorse4.png")
        card_fire.append(pygame.transform.smoothscale(raw_fire_1, (card_w, card_h)))
        card_fire.append(pygame.transform.smoothscale(raw_fire_2, (card_w, card_h)))
        card_fire.append(pygame.transform.smoothscale(raw_fire_3, (card_w, card_h)))
        card_fire.append(pygame.transform.smoothscale(raw_fire_4, (card_w, card_h)))

        spacing = 3 * game.scaling

        card_x = 4 * game.scaling
        card_y = 4 * game.scaling

        grid_x = 0
        grid_y = 0
        for card in self.environment.world.simple_cards.values():
            image_surface = card_earth[0]
            if card.element == "fold":
                image_surface = card_earth[
                    self.environment.world.simple_styles[card.name] - 1
                ]
            elif card.element == "levego":
                image_surface = card_air[
                    self.environment.world.simple_styles[card.name] - 1
                ]
            elif card.element == "viz":
                image_surface = card_water[
                    self.environment.world.simple_styles[card.name] - 1
                ]
            elif card.element == "tuz":
                image_surface = card_fire[
                    self.environment.world.simple_styles[card.name] - 1
                ]

            card_c = pygame_gui.elements.UIImage(
                relative_rect=pygame.Rect(
                    card_x + (card_w + spacing) * grid_x,
                    card_y + (card_h + spacing) * grid_y,
                    card_w,
                    card_h,
                ),
                image_surface=image_surface,
                manager=self.manager,
            )

            self.simple_cards.append(card_c)

            grid_x += 1
            if grid_x % 4 == 0:
                grid_x = 0
                grid_y += 1

    def cleanup(self):
        self.manager = None

    def handle_event(self, event):
        if self.manager:
            self.manager.process_events(event)

        if (
            event.type == pygame.USEREVENT
            and event.user_type == pygame_gui.UI_BUTTON_PRESSED
        ):
            if event.ui_element == self.battle_btn:
                self.scene_manager.switch_scene("Battle")
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
