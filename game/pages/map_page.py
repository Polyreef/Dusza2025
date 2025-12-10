import random
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont, QFontDatabase, QPixmap
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

        font_id = QFontDatabase.addApplicationFont(
            self.game.working_dir + "Assets/Font/AlmendraSC-Regular.ttf"
        )
        if font_id != -1:
            family = QFontDatabase.applicationFontFamilies(font_id)[0]
        else:
            family = "Times New Roman"
        self.font_family = QFont(family, 18)

        border = self.BORDER_COLORS.get(dungeon.kind, "#ffffff")

        self.setObjectName("DungeonListItem")
        self.setStyleSheet(
            f"""
            QFrame#DungeonListItem {{
                background: qlineargradient(
                    x1:0, y1:0, x2:0, y2:1,
                    stop:0 rgba(50,50,50,230),
                    stop:1 rgba(30,30,30,200)
                );
                border-radius: 16px;
                border: 3px solid {border};
                padding: 12px;
            }}
            QFrame#DungeonListItem:hover {{
                background: qlineargradient(
                    x1:0, y1:0, x2:0, y2:1,
                    stop:0 rgba(70,70,70,250),
                    stop:1 rgba(45,45,45,230)
                );
                border: 3px solid {border};
            }}
            QLabel {{
                color: white;
                font-weight: bold;
            }}
            QLabel#info_label {{
                color: #e0e0e0;
                font-size: 18px;
            }}
        """
        )

        main = QVBoxLayout(self)
        main.setContentsMargins(20, 20, 20, 20)
        main.setSpacing(10)

        top_row = QHBoxLayout()
        top_row.setSpacing(20)
        main.addLayout(top_row)

        left = QVBoxLayout()
        left.setAlignment(Qt.AlignmentFlag.AlignTop)
        top_row.addLayout(left)

        if show_battle:
            battle = ClickableImageButton(
                self.game.working_dir + "Assets/Images/Buttons/BattleNormal.png",
                self.game.working_dir + "Assets/Images/Buttons/BattleHover.png",
            )
            battle.set_on_click(
                lambda: self.game.start_battle_by_name(self.dungeon.name)
            )

            if dungeon.kind == "nagy" and not can_start_big:
                battle.setEnabled(False)

            left.addWidget(battle)

        right = QHBoxLayout()
        right.setSpacing(20)
        right.setAlignment(Qt.AlignmentFlag.AlignVCenter)
        top_row.addLayout(right, stretch=1)

        title = QLabel(dungeon.name)
        title.setFont(QFont(family, 26))
        title.setStyleSheet("color: white; font-size: 26px; font-weight: bold;")
        title.setWordWrap(True)
        right.addWidget(title, stretch=0, alignment=Qt.AlignmentFlag.AlignLeft)

        kind_hu = {
            "egyszeru": "Egyszerű találkozás",
            "kis": "Kis kazamata",
            "nagy": "Nagy kazamata",
        }.get(dungeon.kind, "Ismeretlen")

        reward_text = (
            "Jutalom: új sima világkártya"
            if dungeon.kind == "nagy"
            else (
                "Jutalom: +1 sebzés"
                if dungeon.reward_type == "sebzes"
                else "Jutalom: +2 életerő"
            )
        )

        info_box = QVBoxLayout()
        info_box.setSpacing(2)
        info_box.setAlignment(Qt.AlignmentFlag.AlignVCenter)

        info = QLabel(f"{kind_hu}\n{reward_text}")
        info.setFont(QFont(family, 18))
        info.setStyleSheet("color: #e0e0e0; font-size: 18px;")
        info.setWordWrap(True)
        info_box.addWidget(info)

        right.addLayout(info_box, stretch=1)

        cards_container = QWidget()
        grid = QGridLayout(cards_container)
        grid.setContentsMargins(0, 10, 0, 0)
        grid.setHorizontalSpacing(12)
        grid.setVerticalSpacing(12)

        seq = dungeon.card_sequence(world)
        is_mystery = getattr(world, "mystery_dungeons", {}).get(dungeon.name, False)

        if seq:
            cols = 3
            for i, card_def in enumerate(seq):
                cw = CardWidget(card_def, world, self.game.working_dir)

                if is_mystery:
                    cw.name_label.setText("???")
                    cw.hp_label.setText("❤️ ???")
                    cw.dmg_label.setText("⚔️ ???")

                    cw.border_color = "#8B4513"
                    cw.border_hover = "#A0522D"

                    mystery_pix = QPixmap(
                        self.game.working_dir + "Assets/Images/Misc/Mystery.png"
                    )
                    if not mystery_pix.isNull():
                        cw.pixmap = mystery_pix
                        scaled = cw.pixmap.scaled(
                            cw.IMAGE_WIDTH,
                            160,
                            Qt.AspectRatioMode.KeepAspectRatio,
                            Qt.TransformationMode.SmoothTransformation,
                        )
                        cw.image_label.setPixmap(scaled)

                    cw._apply_style(False)

                grid.addWidget(cw, i // cols, i % cols)

        main.addWidget(cards_container)


class MapPage(BackgroundWidget):
    def __init__(self, game):
        super().__init__(game.working_dir + "Assets/Images/Backgrounds/Game.png", game)
        self.game = game
        self._build_ui()

    def _build_ui(self):
        layout = self.get_container()
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(10)

        self.title_label = QLabel()
        title_pix = QPixmap(
            self.game.working_dir + "Assets/Images/Scrolls/Dungeons.png"
        )
        if not title_pix.isNull():
            title_pix = title_pix.scaledToWidth(
                300, Qt.TransformationMode.SmoothTransformation
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

        self.back_menu_btn = ClickableImageButton(
            self.game.working_dir + "Assets/Images/Buttons/BackNormal.png",
            self.game.working_dir + "Assets/Images/Buttons/BackHover.png",
        )
        self.back_menu_btn.set_on_click(self.game.show_library_page)
        btn_row.addWidget(self.back_menu_btn)

        btn_row.addStretch(1)

        self.to_deck_btn = ClickableImageButton(
            self.game.working_dir + "Assets/Images/Buttons/DeckNormal.png",
            self.game.working_dir + "Assets/Images/Buttons/DeckHover.png",
        )
        self.to_deck_btn.set_on_click(self.game.show_deck_page)
        btn_row.addWidget(self.to_deck_btn)

        self.save_btn = ClickableImageButton(
            self.game.working_dir + "Assets/Images/Buttons/SaveNormal.png",
            self.game.working_dir + "Assets/Images/Buttons/SaveHover.png",
        )
        self.save_btn.set_on_click(self.game.save_game_dialog)
        btn_row.addWidget(self.save_btn)

        self.auto_btn = ClickableImageButton(
            self.game.working_dir + "Assets/Images/Buttons/AutoNormal.png",
            self.game.working_dir + "Assets/Images/Buttons/AutoHover.png",
        )
        self.auto_btn.set_on_click(self.generate_auto_dungeon)
        btn_row.addWidget(self.auto_btn)

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
            extra = "Jelenleg NEM indíthatsz nagy kazamatát - már minden sima kártyád megvan."
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

        mystery = random.randint(0, 1)

        ok = world.add_dungeon(dungeon, mystery)
        if not ok:
            show_error(self, "Hiba", "A kazamata hozzáadása sikertelen.")
            return

        total = len(simple_cards) + (1 if leader_name else 0)

        show_info(
            self,
            "Új automata kazamata",
            f"Név: {name}\n"
            f"Típus: {kind}\n"
            f"Lapok száma: {total}\n"
            f"Titokzatos: {"Igen" if mystery else "Nem"}",
        )

        self.refresh_from_environment()
