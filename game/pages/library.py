from PySide6.QtCore import Qt
from PySide6.QtGui import QFont, QPixmap
from PySide6.QtWidgets import (
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

from game.widgets.background import BackgroundWidget
from game.widgets.buttons import ClickableImageButton
from game.widgets.cards import CardWidget


class WorldLibraryPage(BackgroundWidget):
    def __init__(self, game: "DamareenGameWindow"):
        super().__init__("Assets/Images/Backgrounds/Library.png", game)
        self.game = game
        self._build_ui()

    def _build_ui(self):
        layout = self.get_container()
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(20)

        layout.addStretch(1)

        center_layout = QVBoxLayout()
        center_layout.setSpacing(12)
        center_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addLayout(center_layout, stretch=0)

        cards_view_btn = ClickableImageButton(
            "Assets/Images/Buttons/CardsNormal.png",
            "Assets/Images/Buttons/CardsHover.png",
            scale_factor=0.5,
        )
        cards_view_btn.set_on_click(self.game.show_world_cards_page)
        center_layout.addWidget(cards_view_btn, alignment=Qt.AlignmentFlag.AlignCenter)

        dungeons_btn = ClickableImageButton(
            "Assets/Images/Buttons/DungeonsNormal.png",
            "Assets/Images/Buttons/DungeonsHover.png",
            scale_factor=0.5,
        )
        dungeons_btn.set_on_click(self.game.show_map_page)
        center_layout.addWidget(dungeons_btn, alignment=Qt.AlignmentFlag.AlignCenter)

        collection_btn = ClickableImageButton(
            "Assets/Images/Buttons/CollectionNormal.png",
            "Assets/Images/Buttons/CollectionHover.png",
            scale_factor=0.5,
        )
        collection_btn.set_on_click(self.game.show_collection_page)
        center_layout.addWidget(collection_btn, alignment=Qt.AlignmentFlag.AlignCenter)

        layout.addStretch(1)

        bottom_row = QHBoxLayout()
        bottom_row.setSpacing(20)
        layout.addLayout(bottom_row)

        deck_btn = ClickableImageButton(
            "Assets/Images/Buttons/DeckNormal.png",
            "Assets/Images/Buttons/DeckHover.png",
            scale_factor=0.4,
        )
        deck_btn.set_on_click(self.game.show_deck_page)
        bottom_row.addWidget(deck_btn)

        bottom_row.addStretch(1)

        quit_btn = ClickableImageButton(
            "Assets/Images/Buttons/QuitNormal.png",
            "Assets/Images/Buttons/QuitHover.png",
            scale_factor=0.4,
        )
        quit_btn.set_on_click(self.game.show_main_menu)
        bottom_row.addWidget(quit_btn)


class WorldCardsPage(BackgroundWidget):
    def __init__(self, game: "DamareenGameWindow"):
        super().__init__("Assets/Images/Backgrounds/Library.png", game)
        self.game = game
        self._build_ui()

    def _build_ui(self):
        layout = self.get_container()
        layout.setContentsMargins(20, 20, 20, 10)
        layout.setSpacing(10)

        title_label = QLabel()
        title_pix = QPixmap("Assets/Images/Scrolls/WorldCards.png")
        if not title_pix.isNull():
            title_pix = title_pix.scaledToWidth(
                320, Qt.TransformationMode.SmoothTransformation
            )
        title_label.setPixmap(title_pix)
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title_label)

        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.scroll.setStyleSheet(
            """
    QScrollArea { background: transparent; border: none; }
"""
        )

        self.scroll.viewport().setStyleSheet("background: transparent;")
        layout.addWidget(self.scroll, 1)

        container = QWidget()
        container.setStyleSheet("background: transparent;")
        self.grid_layout = QGridLayout(container)
        self.grid_layout.setContentsMargins(0, 0, 0, 0)
        self.grid_layout.setHorizontalSpacing(10)
        self.grid_layout.setVerticalSpacing(10)
        self.scroll.setWidget(container)

        btn_row = QHBoxLayout()
        btn_row.setSpacing(10)
        layout.addLayout(btn_row)

        back_lib_btn = ClickableImageButton(
            "Assets/Images/Buttons/BackNormal.png",
            "Assets/Images/Buttons/BackHover.png",
            scale_factor=0.35,
        )
        back_lib_btn.set_on_click(self.game.show_library_page)
        btn_row.addWidget(back_lib_btn)

        btn_row.addStretch(1)

        deck_btn = ClickableImageButton(
            "Assets/Images/Buttons/DeckNormal.png",
            "Assets/Images/Buttons/DeckHover.png",
            scale_factor=0.35,
        )
        deck_btn.set_on_click(self.game.show_deck_page)
        btn_row.addWidget(deck_btn)

        map_btn = ClickableImageButton(
            "Assets/Images/Buttons/DungeonsNormal.png",
            "Assets/Images/Buttons/DungeonsHover.png",
            scale_factor=0.35,
        )
        map_btn.set_on_click(self.game.show_map_page)
        btn_row.addWidget(map_btn)

    def _clear_grid(self):
        while self.grid_layout.count():
            item = self.grid_layout.takeAt(0)
            w = item.widget()
            if w:
                w.deleteLater()

    def refresh_from_game(self):
        env = self.game.environment
        state = self.game.state
        self._clear_grid()

        if not (env and state):
            return

        world = env.world

        world_cards = []
        if hasattr(world, "iter_simple_cards"):
            world_cards.extend(world.iter_simple_cards())
        if hasattr(world, "iter_leader_cards"):
            world_cards.extend(world.iter_leader_cards())

        cols = 4
        row = col = 0
        for c in world_cards:
            w = CardWidget(c, world)
            self.grid_layout.addWidget(w, row, col)
            col += 1
            if col >= cols:
                col = 0
                row += 1

        self.grid_layout.setRowStretch(row + 1, 1)


class CollectionPage(BackgroundWidget):
    def __init__(self, game: "DamareenGameWindow"):
        super().__init__("Assets/Images/Backgrounds/Library.png", game)
        self.game = game
        self._build_ui()

    def _build_ui(self):
        layout = self.get_container()
        layout.setContentsMargins(20, 20, 20, 10)
        layout.setSpacing(10)

        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.scroll.setStyleSheet(
            """
    QScrollArea { background: transparent; border: none; }
"""
        )

        self.scroll.viewport().setStyleSheet("background: transparent;")
        layout.addWidget(self.scroll, 1)

        container = QWidget()
        container.setStyleSheet("background: transparent;")
        self.grid_layout = QGridLayout(container)
        self.grid_layout.setContentsMargins(0, 0, 0, 0)
        self.grid_layout.setHorizontalSpacing(10)
        self.grid_layout.setVerticalSpacing(10)
        self.scroll.setWidget(container)

        btn_row = QHBoxLayout()
        btn_row.setSpacing(10)
        layout.addLayout(btn_row)

        back_lib_btn = ClickableImageButton(
            "Assets/Images/Buttons/BackNormal.png",
            "Assets/Images/Buttons/BackHover.png",
            scale_factor=0.35,
        )
        back_lib_btn.set_on_click(self.game.show_library_page)
        btn_row.addWidget(back_lib_btn)

        btn_row.addStretch(1)

        deck_btn = ClickableImageButton(
            "Assets/Images/Buttons/DeckNormal.png",
            "Assets/Images/Buttons/DeckHover.png",
            scale_factor=0.35,
        )
        deck_btn.set_on_click(self.game.show_deck_page)
        btn_row.addWidget(deck_btn)

        map_btn = ClickableImageButton(
            "Assets/Images/Buttons/DungeonsNormal.png",
            "Assets/Images/Buttons/DungeonsHover.png",
            scale_factor=0.35,
        )
        map_btn.set_on_click(self.game.show_map_page)
        btn_row.addWidget(map_btn)

    def _clear_grid(self):
        while self.grid_layout.count():
            item = self.grid_layout.takeAt(0)
            w = item.widget()
            if w:
                w.deleteLater()

    def refresh_from_game(self):
        env = self.game.environment
        state = self.game.state
        self._clear_grid()

        if not (env and state):
            return

        world = env.world
        player = state.player

        cards = list(player.collection.values())
        cols = 4
        row = col = 0
        for c in cards:
            w = CardWidget(c, world)
            self.grid_layout.addWidget(w, row, col)
            col += 1
            if col >= cols:
                col = 0
                row += 1

        self.grid_layout.setRowStretch(row + 1, 1)
