from PySide6.QtCore import Qt
from PySide6.QtGui import QFont, QFontDatabase, QPixmap
from PySide6.QtWidgets import QHBoxLayout, QLabel, QScrollArea, QVBoxLayout, QWidget

from game.helpers import show_info
from game.widgets.background import BackgroundWidget
from game.widgets.buttons import ClickableArrowButton, ClickableImageButton
from game.widgets.cards import CardWidget


class DeckBuilderPage(BackgroundWidget):
    def __init__(self, game):
        super().__init__(game.working_dir + "Assets/Images/Backgrounds/Game.png", game)
        self.game = game
        self._build_ui()

    def _build_ui(self):
        layout = self.get_container()
        layout.setContentsMargins(20, 0, 20, 20)
        layout.setSpacing(10)

        title_label = QLabel()
        title_pix = QPixmap(self.game.working_dir + "Assets/Images/Scrolls/AssembleDeck.png")
        if not title_pix.isNull():
            title_pix = title_pix.scaledToWidth(
                300, Qt.TransformationMode.SmoothTransformation
            )
        title_label.setPixmap(title_pix)
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title_label)

        middle = QHBoxLayout()
        middle.setSpacing(40)
        layout.addLayout(middle, stretch=1)

        left_box = QVBoxLayout()
        left_box.setSpacing(8)
        middle.addLayout(left_box, stretch=1)

        left_title = QLabel()
        left_title_pix = QPixmap(self.game.working_dir + "Assets/Images/Scrolls/Cards.png")
        if not left_title_pix.isNull():
            left_title_pix = left_title_pix.scaledToWidth(
                200, Qt.TransformationMode.SmoothTransformation
            )
        left_title.setPixmap(left_title_pix)
        left_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        left_box.addWidget(left_title)

        self.collection_area = QScrollArea()
        self.collection_area.setWidgetResizable(True)
        self.collection_area.setStyleSheet(
            "QScrollArea { background: transparent; border: none; }"
        )
        self.collection_area.viewport().setStyleSheet("background: transparent;")
        self.collection_container = QWidget()
        self.collection_container.setStyleSheet("background: transparent;")
        self.collection_layout = QVBoxLayout(self.collection_container)
        self.collection_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.collection_layout.setContentsMargins(0, 0, 0, 0)
        self.collection_layout.setSpacing(6)
        self.collection_area.setWidget(self.collection_container)
        self.collection_area.setMinimumHeight(260)
        left_box.addWidget(self.collection_area)

        right_box = QVBoxLayout()
        right_box.setSpacing(8)
        middle.addLayout(right_box, stretch=1)

        right_title = QLabel()
        right_title_pix = QPixmap(self.game.working_dir + "Assets/Images/Scrolls/Deck.png")
        if not right_title_pix.isNull():
            right_title_pix = right_title_pix.scaledToWidth(
                200, Qt.TransformationMode.SmoothTransformation
            )
        right_title.setPixmap(right_title_pix)
        right_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        right_box.addWidget(right_title)

        self.deck_area = QScrollArea()
        self.deck_area.setWidgetResizable(True)
        self.deck_area.setStyleSheet(
            "QScrollArea { background: transparent; border: none; }"
        )
        self.deck_area.viewport().setStyleSheet("background: transparent;")
        self.deck_container = QWidget()
        self.deck_container.setStyleSheet("background: transparent;")
        self.deck_layout = QVBoxLayout(self.deck_container)
        self.deck_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.deck_layout.setContentsMargins(0, 0, 0, 0)
        self.deck_layout.setSpacing(6)
        self.deck_area.setWidget(self.deck_container)
        self.deck_area.setMinimumHeight(260)
        right_box.addWidget(self.deck_area)

        font_id = QFontDatabase.addApplicationFont(self.game.working_dir + "Assets/Font/AlmendraSC-Regular.ttf")
        if font_id != -1:
            family = QFontDatabase.applicationFontFamilies(font_id)[0]
        else:
            family = "Times New Roman"
        
        font = QFont(family, 20)

        self.deck_info_label = QLabel("")
        self.deck_info_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.deck_info_label.setFont(font)
        self.deck_info_label.setStyleSheet(
            "color: white"
        )
        layout.addWidget(self.deck_info_label)

        back_btn = ClickableImageButton(
            self.game.working_dir + "Assets/Images/Buttons/QuitNormal.png",
            self.game.working_dir + "Assets/Images/Buttons/QuitHover.png",
        )
        back_btn.set_on_click(self.game.show_library_page)
        layout.addWidget(back_btn, alignment=Qt.AlignmentFlag.AlignCenter)

    def _clear_lists(self):
        for l in (self.collection_layout, self.deck_layout):
            while l.count():
                item = l.takeAt(0)
                w = item.widget()
                if w:
                    w.deleteLater()

    def refresh_from_state(self):
        state = self.game.state
        self._clear_lists()

        if not state:
            self.deck_info_label.setText("Nincs aktív játék.")
            return

        player = state.player
        max_size = player.max_deck_size()
        deck_full = len(player.deck) >= max_size

        for card in player.collection.values():
            row = self._create_collection_row(card, deck_full)
            self.collection_layout.addWidget(row)

        for name in player.deck:
            card = player.collection.get(name)
            if card:
                row = self._create_deck_row(card)
                self.deck_layout.addWidget(row)

        self.deck_info_label.setText(
            f"Gyűjtemény: {len(player.collection)} kártya • Pakli: {len(player.deck)}/{max_size}"
        )

        if len(player.deck) == max_size:
            self.deck_info_label.setStyleSheet(
            "color: #adff2f"
        )
        else:
            self.deck_info_label.setStyleSheet(
            "color: white"
        )

    def _create_collection_row(self, card, deck_full: bool):
        row = QWidget()
        row.setMaximumHeight(220)
        h = QHBoxLayout(row)
        h.setContentsMargins(0, 0, 0, 0)
        h.setSpacing(8)

        card_widget = CardWidget(card, self.game.environment.world, self.game.working_dir)
        h.addWidget(card_widget)

        btn = ClickableArrowButton(
            self.game.working_dir + "Assets/Images/Arrows/RightNormal.png",
            self.game.working_dir + "Assets/Images/Arrows/RightHover.png",
            size=40,
        )
        btn.set_on_click(lambda: self._add_to_deck(card.name))
        btn.setEnabled(not deck_full)

        arrow_col = QVBoxLayout()
        arrow_col.addStretch(1)
        arrow_col.addWidget(btn, alignment=Qt.AlignmentFlag.AlignCenter)
        arrow_col.addStretch(1)
        h.addLayout(arrow_col)

        return row

    def _create_deck_row(self, card):
        row = QWidget()
        row.setMaximumHeight(220)
        h = QHBoxLayout(row)
        h.setContentsMargins(0, 0, 0, 0)
        h.setSpacing(8)

        btn = ClickableArrowButton(
            self.game.working_dir + "Assets/Images/Arrows/LeftNormal.png",
            self.game.working_dir + "Assets/Images/Arrows/LeftHover.png",
            size=40,
        )
        btn.set_on_click(lambda: self._remove_from_deck(card.name))

        arrow_col = QVBoxLayout()
        arrow_col.addStretch(1)
        arrow_col.addWidget(btn, alignment=Qt.AlignmentFlag.AlignCenter)
        arrow_col.addStretch(1)
        h.addLayout(arrow_col)

        card_widget = CardWidget(card, self.game.environment.world, self.game.working_dir)
        h.addWidget(card_widget)

        return row

    def _add_to_deck(self, name):
        state = self.game.state
        if not state:
            return

        player = state.player
        max_size = player.max_deck_size()

        if len(player.deck) >= max_size:
            show_info(self, "Pakli tele", "A pakli elérte a maximális méretet.")
            return

        if name not in player.deck:
            player.deck.append(name)

        self.refresh_from_state()

    def _remove_from_deck(self, name):
        player = self.game.state.player
        if name in player.deck:
            player.deck.remove(name)
        self.refresh_from_state()
