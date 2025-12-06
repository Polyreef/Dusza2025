import random
from PySide6.QtCore import Qt
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import (
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

from core.models import Dungeon

from game.helpers import can_start_big_dungeon, show_error, show_info
from game.widgets.background import BackgroundWidget
from game.widgets.buttons import ClickableImageButton
from game.widgets.cards import CardWidget


class DungeonListItem(QFrame):
    BORDER_COLORS = {
        "egyszeru": "#50d6d6",
        "kis": "#7a3db8",
        "nagy": "#d4af37",
    }

    def __init__(
        self,
        dungeon,
        world,
        game,
        can_start_big: bool,
        *,
        show_battle=True,
        parent=None,
    ):
        super().__init__(parent)

        self.dungeon = dungeon
        self.world = world
        self.game = game

        border = self.BORDER_COLORS.get(dungeon.kind, "#ffffff")

        self.setObjectName("DungeonListItem")
        self.setStyleSheet(
            f"""
            QFrame#DungeonListItem {{
                background-color: rgba(0, 0, 0, 140);
                border-radius: 12px;
                border: 3px solid {border};
            }}
        """
        )

        main = QVBoxLayout(self)
        main.setContentsMargins(10, 10, 10, 10)
        main.setSpacing(10)

        top = QHBoxLayout()
        top.setSpacing(12)
        main.addLayout(top)

        kind_to_bg = {
            "egyszeru": "Assets/Images/Backgrounds/egyszeru.png",
            "kis": "Assets/Images/Backgrounds/kis.png",
            "nagy": "Assets/Images/Backgrounds/nagy.png",
        }

        img = QLabel()
        pix = QPixmap(kind_to_bg.get(dungeon.kind, ""))
        if not pix.isNull():
            pix = pix.scaled(
                150,
                90,
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation,
            )
            img.setPixmap(pix)
        img.setAlignment(Qt.AlignmentFlag.AlignCenter)
        top.addWidget(img)

        right = QVBoxLayout()
        right.setSpacing(6)
        top.addLayout(right, stretch=1)

        title = QLabel(dungeon.name)
        title.setStyleSheet("color: white; font-size: 18px; font-weight: bold;")
        right.addWidget(title)

        kind_hu = {
            "egyszeru": "Egyszerű találkozás",
            "kis": "Kis kazamata",
            "nagy": "Nagy kazamata",
        }.get(dungeon.kind, "Ismeretlen")

        reward = (
            "Jutalom: új sima világkártya"
            if dungeon.kind == "nagy"
            else (
                "Jutalom: +1 sebzés"
                if dungeon.reward_type == "sebzes"
                else "Jutalom: +2 életerő"
            )
        )

        info = QLabel(f"{kind_hu}\n{reward}")
        info.setWordWrap(True)
        info.setStyleSheet("color: white;")
        right.addWidget(info)

        cards_container = QWidget()
        cards_container.setStyleSheet("background: transparent;")

        grid = QGridLayout(cards_container)
        grid.setContentsMargins(0, 0, 0, 0)
        grid.setHorizontalSpacing(8)
        grid.setVerticalSpacing(8)

        is_mystery = False
        mystery_map = getattr(world, "mystery_dungeons", {})
        if isinstance(mystery_map, dict):
            is_mystery = mystery_map.get(dungeon.name, False)

        seq = dungeon.card_sequence(world)
        if seq:
            cols = 2

            if is_mystery:
                mystery_pix = QPixmap("Assets/Images/Misc/Mystery.png")
                for i, _card_def in enumerate(seq):
                    lbl = QLabel()
                    if not mystery_pix.isNull():
                        scaled = mystery_pix.scaled(
                            120,
                            160,
                            Qt.AspectRatioMode.KeepAspectRatio,
                            Qt.TransformationMode.SmoothTransformation,
                        )
                        lbl.setPixmap(scaled)
                    lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
                    row = i // cols
                    col = i % cols
                    grid.addWidget(lbl, row, col)
            else:
                for i, card_def in enumerate(seq):
                    cw = CardWidget(card_def, world)
                    row = i // cols
                    col = i % cols
                    grid.addWidget(cw, row, col)

        right.addWidget(cards_container)

        if show_battle:
            btn_layout = QHBoxLayout()
            btn_layout.addStretch(1)

            battle = ClickableImageButton(
                "Assets/Images/Buttons/BattleNormal.png",
                "Assets/Images/Buttons/BattleHover.png",
                scale_factor=0.45,
            )
            battle.set_on_click(
                lambda: self.game.start_battle_by_name(self.dungeon.name)
            )

            if dungeon.kind == "nagy" and not can_start_big:
                battle.setEnabled(False)

            btn_layout.addWidget(battle)
            btn_layout.addStretch(1)
            main.addLayout(btn_layout)


class MapPage(BackgroundWidget):
    def __init__(self, game):
        super().__init__("Assets/Images/Backgrounds/Game.png", game)
        self.game = game
        self._build_ui()

    def _build_ui(self):
        layout = self.get_container()
        layout.setContentsMargins(30, 20, 30, 20)
        layout.setSpacing(10)

        self.title_label = QLabel()
        title_pix = QPixmap("Assets/Images/Scrolls/Dungeons.png")
        if not title_pix.isNull():
            title_pix = title_pix.scaledToWidth(
                420, Qt.TransformationMode.SmoothTransformation
            )
        self.title_label.setPixmap(title_pix)
        self.title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.title_label)

        self.info_label = QLabel("")
        self.info_label.setStyleSheet("color: white; font-size: 14px;")
        self.info_label.setWordWrap(True)
        layout.addWidget(self.info_label)

        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setStyleSheet(
            "QScrollArea { background: transparent; border: none; }"
        )
        self.scroll_area.viewport().setStyleSheet("background: transparent;")
        self.list_container = QWidget()
        self.list_container.setStyleSheet("background: transparent;")
        self.list_layout = QVBoxLayout(self.list_container)
        self.list_layout.setContentsMargins(0, 0, 0, 0)
        self.list_layout.setSpacing(8)
        self.list_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.scroll_area.setWidget(self.list_container)
        layout.addWidget(self.scroll_area, 1)

        btn_row = QHBoxLayout()
        btn_row.setSpacing(20)
        layout.addLayout(btn_row)

        self.to_deck_btn = ClickableImageButton(
            "Assets/Images/Buttons/DeckNormal.png",
            "Assets/Images/Buttons/DeckHover.png",
            scale_factor=0.4,
        )
        self.to_deck_btn.set_on_click(self.game.show_deck_page)
        btn_row.addWidget(self.to_deck_btn)

        self.save_btn = ClickableImageButton(
            "Assets/Images/Buttons/SaveNormal.png",
            "Assets/Images/Buttons/SaveHover.png",
            scale_factor=0.4,
        )
        self.save_btn.set_on_click(self.game.save_game_dialog)
        btn_row.addWidget(self.save_btn)

        self.auto_btn = ClickableImageButton(
            "Assets/Images/Buttons/AutoNormal.png",
            "Assets/Images/Buttons/AutoHover.png",
            scale_factor=0.4,
        )
        self.auto_btn.set_on_click(self.generate_auto_dungeon)
        btn_row.addWidget(self.auto_btn)

        btn_row.addStretch(1)

        self.back_menu_btn = ClickableImageButton(
            "Assets/Images/Buttons/BackNormal.png",
            "Assets/Images/Buttons/BackHover.png",
            scale_factor=0.4,
        )
        self.back_menu_btn.set_on_click(self.game.show_library_page)
        btn_row.addWidget(self.back_menu_btn)

    def _clear_list(self):
        while self.list_layout.count():
            item = self.list_layout.takeAt(0)
            w = item.widget()
            if w:
                w.deleteLater()

    def refresh_from_environment(self):
        self._clear_list()

        env = self.game.environment
        state = self.game.state
        if not env or not state:
            self.info_label.setText(
                "Nincs aktív játék. Menj vissza a főmenübe, és indíts egy új játékot."
            )
            return

        world = env.world
        dungeons = list(world.iter_dungeons())
        if not dungeons:
            self.info_label.setText(
                "Ebben a világban nincsenek kazamaták. (Lehet, hogy szerkesztened kell a világot.)"
            )
            return

        can_big = can_start_big_dungeon(world, state.player)
        if not can_big:
            extra = "Jelenleg NEM indíthatsz nagy kazamatát – már minden sima kártyád megvan."
        else:
            extra = ""
        self.info_label.setText(extra)

        for dun in dungeons:
            row = DungeonListItem(dun, world, self.game, can_big)
            self.list_layout.addWidget(row)

        self.list_layout.addStretch(1)

    def generate_auto_dungeon(self):
        env = self.game.environment
        state = self.game.state

        if not env or not state:
            show_error(self, "Hiba", "Nincs aktív játék.")
            return

        world = env.world
        simple = list(world.simple_cards.keys())
        leaders = list(world.leader_cards.keys())

        if not simple or not leaders:
            show_error(self, "Hiba", "Nincs elég kártya a generáláshoz.")
            return

        missing = [c for c in simple if c not in state.player.collection]

        if missing:
            kind = random.choice(["egyszeru", "kis", "nagy"])
        else:
            kind = random.choice(["egyszeru", "kis"])

        if kind == "egyszeru":
            simple_cards = [random.choice(simple)]
            leader_name = None
            reward = random.choice(["sebzes", "eletero"])

        elif kind == "kis":
            if len(simple) < 3:
                show_error(self, "Hiba", "Nincs elég sima kártya kis kazamatához.")
                return

            simple_cards = random.sample(simple, 3)
            leader_name = random.choice(leaders)
            reward = random.choice(["sebzes", "eletero"])

        else:
            if len(simple) < 5:
                show_error(self, "Hiba", "Nincs elég sima kártya nagy kazamatához.")
                return

            simple_cards = random.sample(simple, 5)
            leader_name = random.choice(leaders)
            reward = None

        base = "Auto. kazamata"
        idx = 1
        name = f"{base} #{idx}"
        while name in world.dungeons:
            name = f"{base} #{idx}"
            idx += 1

        dungeon = Dungeon(
            name=name,
            kind=kind,
            simple_card_names=simple_cards,
            leader_name=leader_name,
            reward_type=reward,
        )

        ok = world.add_dungeon(dungeon, mystery=False)
        if not ok:
            show_error(self, "Hiba", "A kazamata hozzáadása sikertelen.")
            return

        total = len(simple_cards) + (1 if leader_name else 0)

        show_info(
            self,
            "Új automata kazamata",
            f"Név: {name}\n" f"Típus: {kind}\n" f"Lapok száma: {total}",
        )

        self.refresh_from_environment()
