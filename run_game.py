from __future__ import annotations

import json
import os
from typing import Optional

from PySide6.QtCore import Property, QRect, QSize, Qt, QTimer
from PySide6.QtGui import QAction, QColor, QFont, QFontDatabase, QPainter, QPen
from PySide6.QtWidgets import (
    QApplication,
    QDialog,
    QDialogButtonBox,
    QFileDialog,
    QFormLayout,
    QFrame,
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QSlider,
    QStackedWidget,
    QTextEdit,
    QVBoxLayout,
    QWidget,
    QInputDialog,
)

from PySide6.QtGui import QPixmap
from PySide6.QtMultimedia import QSoundEffect
from PySide6.QtCore import QUrl

from core import ELEMENT_ORDER
from core.battle import run_battle, BattleResult
from core.environment import Environment
from core.models import World, Player, State, Dungeon, CardDefinition
from core import storage as storage_module


class SoundManager:
    def __init__(self):
        self.sounds = {}

    def load(self, name, path, volume=0.7):
        eff = QSoundEffect()
        eff.setSource(QUrl.fromLocalFile(path))
        eff.setVolume(volume)
        self.sounds[name] = eff

    def play(self, name):
        if name in self.sounds:
            self.sounds[name].play()


# ----------------------------------------------------------------------
# Segédfüggvények - szabályok, jutalmak
# ----------------------------------------------------------------------


def can_start_big_dungeon(world: World, player: Player) -> bool:
    """Van-e még olyan sima világkártya, ami nincs a gyűjteményben?"""
    for c in world.iter_simple_cards():
        if c.name not in player.collection:
            return True
    return False


def apply_battle_rewards(
    world: World, state: State, dungeon: Dungeon, result: BattleResult
) -> tuple[str, str]:
    """
    Harc utáni jutalom feldolgozása.

    Visszaad:
        (felhasználóbarát üzenet, log utolsó sora)
    """
    player = state.player

    if result.outcome != "win":
        return ("A hős elbukott… most nincs jutalom.", "jatekos vesztett")

    # Egyszerű / kis kazamata: utolsó támadó lap buffolása
    if dungeon.kind in ("egyszeru", "kis"):
        reward_type = dungeon.reward_type or "eletero"
        card_name = result.last_player_attacker_name
        if not card_name:
            return (
                "Győztél, de az utolsó támadó lap nem ismert (nincs jutalom).",
                "jatekos nyert",
            )

        card = player.collection.get(card_name)
        if not card:
            return (
                f"Győztél, de a(z) {card_name} lap nem található a gyűjteményben.",
                "jatekos nyert",
            )

        if reward_type == "sebzes":
            card.damage += 1
            msg = f"Győzelem! {card.name} +1 sebzést kapott."
            last_line = f"jatekos nyert;sebzes;{card.name}"
        else:
            card.health += 2
            msg = f"Győzelem! {card.name} +2 életerőt kapott."
            last_line = f"jatekos nyert;eletero;{card.name}"

        return msg, last_line

    # Nagy kazamata: első olyan sima lap a világból, ami nincs gyűjteményben
    if dungeon.kind == "nagy":
        for c in world.iter_simple_cards():
            if c.name not in player.collection:
                player.add_card_from_world(world, c.name)
                msg = f"Hatalmas győzelem! Új kártyát kaptál: {c.name}."
                last_line = f"jatekos nyert;{c.name}"
                return msg, last_line

        return (
            "Győztél, de már az összes sima kártyát megszerezted ebből a világból.",
            "jatekos nyert",
        )

    return (
        "Győztél, de ismeretlen kazamata típus miatt nincs jutalom.",
        "jatekos nyert",
    )


def ask_yes_no(parent: QWidget, title: str, text: str) -> bool:
    mb = QMessageBox(parent)
    mb.setWindowTitle(title)
    mb.setText(text)
    mb.setIcon(QMessageBox.Icon.Question)
    mb.setStandardButtons(
        QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
    )
    mb.setDefaultButton(QMessageBox.StandardButton.No)
    res = mb.exec()
    return res == QMessageBox.StandardButton.Yes


def show_error(parent: QWidget, title: str, text: str):
    mb = QMessageBox(parent)
    mb.setWindowTitle(title)
    mb.setText(text)
    mb.setIcon(QMessageBox.Icon.Critical)
    mb.exec()


def show_info(parent: QWidget, title: str, text: str):
    mb = QMessageBox(parent)
    mb.setWindowTitle(title)
    mb.setText(text)
    mb.setIcon(QMessageBox.Icon.Information)
    mb.exec()


class ClickableImageButton(QLabel):
    def __init__(
        self,
        normal_path: str,
        hover_path: str,
        parent=None,
        scale_factor: float = 1.0,
    ):
        """
        Egyszerű, stabil kép-gomb:
        - scale_factor: az EREDETI képszélesség szorzója (nem az ablaké!)
          pl. 0.6 = 60%-os méret
        """
        super().__init__(parent)
        self.normal_pix_original = QPixmap(normal_path)
        self.hover_pix_original = QPixmap(hover_path)

        self.scale_factor = scale_factor
        self._callback = None

        self.setScaledContents(True)
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, False)

        self.update_scaled_pixmaps()

    def set_on_click(self, func):
        self._callback = func

    def update_scaled_pixmaps(self):
        if self.normal_pix_original.isNull():
            return

        if self.scale_factor <= 0:
            target_w = self.normal_pix_original.width()
        else:
            target_w = int(self.normal_pix_original.width() * self.scale_factor)

        self.normal_pix = self.normal_pix_original.scaledToWidth(
            target_w, Qt.TransformationMode.SmoothTransformation
        )
        self.hover_pix = self.hover_pix_original.scaledToWidth(
            target_w, Qt.TransformationMode.SmoothTransformation
        )

        self.setPixmap(self.normal_pix)
        self.setFixedSize(self.normal_pix.size())

    def enterEvent(self, event):
        if hasattr(self, "hover_pix"):
            self.setPixmap(self.hover_pix)

    def leaveEvent(self, event):
        if hasattr(self, "normal_pix"):
            self.setPixmap(self.normal_pix)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton and self._callback:
            window = self.window()
            if hasattr(window, "sound"):
                window.sound.play("click")
            self._callback()


class ScalableBannerLabel(QLabel):
    def __init__(self, image_path, width_ratio=0.6, parent=None):
        super().__init__(parent)
        self.pix_original = QPixmap(image_path)
        self.width_ratio = width_ratio

        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setScaledContents(False)

        self.update_scaled()

        # figyeli az ablak méretét
        self.window().installEventFilter(self)

    def eventFilter(self, watched, event):
        from PySide6.QtCore import QEvent

        if watched == self.window() and event.type() == QEvent.Type.Resize:
            self.update_scaled()
        return super().eventFilter(watched, event)

    def update_scaled(self):
        win = self.window()
        if not win:
            return

        target_w = int(win.width() * self.width_ratio)
        scaled = self.pix_original.scaledToWidth(
            target_w, Qt.TransformationMode.SmoothTransformation
        )
        self.setPixmap(scaled)
        self.setFixedHeight(scaled.height())


class EnvironmentChooseDialog(QDialog):
    def __init__(self, parent, env_files):
        super().__init__(parent)
        self.setWindowTitle("Játékkörnyezet választása")
        self.selected = None  # (name, path, env)

        layout = QVBoxLayout(self)

        if env_files:
            layout.addWidget(QLabel("Válassz egy környezetet a listából:"))
            self.list_widget = QListWidget()
            for name, path, env in env_files:
                item = QListWidgetItem(name)
                item.setData(Qt.ItemDataRole.UserRole, (name, path, env))
                self.list_widget.addItem(item)
            layout.addWidget(self.list_widget)
        else:
            layout.addWidget(
                QLabel("Nincsenek környezetek az Environments mappában. Tallózz egyet!")
            )
            self.list_widget = None

        browse_btn = QPushButton("Tallózás…")
        browse_btn.clicked.connect(self.on_browse)
        layout.addWidget(browse_btn)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self.on_accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def on_browse(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "Környezet betöltése", "", "Játékkörnyezet (*.json)"
        )
        if not path:
            return
        try:
            env = storage_module.load_environment_from_file(path)
            self.selected = (env.name, path, env)
            self.accept()
        except Exception as e:
            QMessageBox.critical(self, "Hiba", f"A fájl nem tölthető be:\n{e}")

    def on_accept(self):
        if self.list_widget:
            item = self.list_widget.currentItem()
            if item:
                self.selected = item.data(Qt.ItemDataRole.UserRole)
        self.accept()


class StateChooseDialog(QDialog):
    def __init__(self, parent, state_files):
        super().__init__(parent)
        self.setWindowTitle("Játék betöltése")
        self.selected = None  # path string

        layout = QVBoxLayout(self)

        if state_files:
            layout.addWidget(QLabel("Válassz egy mentést a listából:"))
            self.list_widget = QListWidget()
            for name, path in state_files:
                item = QListWidgetItem(name)
                item.setData(Qt.ItemDataRole.UserRole, path)
                self.list_widget.addItem(item)
            layout.addWidget(self.list_widget)
        else:
            layout.addWidget(
                QLabel("Nincsenek mentések a States mappában. Tallózz egyet!")
            )
            self.list_widget = None

        browse_btn = QPushButton("Tallózás…")
        browse_btn.clicked.connect(self.on_browse)
        layout.addWidget(browse_btn)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self.on_accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def on_browse(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "Mentés betöltése", "", "Damareen mentés (*.json)"
        )
        if not path:
            return
        # Tallózott mentést mindig elfogadjuk
        self.selected = path
        self.accept()

    def on_accept(self):
        if self.list_widget:
            item = self.list_widget.currentItem()
            if item:
                self.selected = item.data(Qt.ItemDataRole.UserRole)
        self.accept()


# Background widget


class BackgroundWidget(QWidget):
    def __init__(self, background_path: str, parent=None):
        super().__init__(parent)
        self.background_path = background_path

        # Háttérkép label - teljes widgetet lefedi
        self.bg_label = QLabel(self)
        self.bg_label.setScaledContents(True)
        # Ne fogja meg az egérkattintást, csak “dísz”
        self.bg_label.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        # Menjen a háttérbe
        self.bg_label.lower()

        # Egyetlen fő layout, amit a gyerek-oldalak is használnak
        self._container_layout = QVBoxLayout(self)
        self._container_layout.setContentsMargins(0, 0, 0, 0)
        self._container_layout.setSpacing(0)

        # Rögtön töltsük be a hátteret
        self.update_background()

    def set_background(self, path: str):
        self.background_path = path
        self.update_background()

    def update_background(self):
        if not self.background_path:
            return
        pix = QPixmap(self.background_path)
        if not pix.isNull():
            self.bg_label.setPixmap(pix)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        # Mindig a teljes widgetet fedje le a háttér
        self.bg_label.resize(self.size())
        self.update_background()

    def get_container(self) -> QVBoxLayout:
        """Ezt a layoutot használd a gyerek-oldalakban."""
        return self._container_layout


# ----------------------------------------------------------------------
# Oldal 1 - Főmenü
# ----------------------------------------------------------------------


class MainMenuPage(BackgroundWidget):
    def __init__(self, game: "DamareenGameWindow"):
        super().__init__("Assets/Images/Backgrounds/Menu.png", game)
        self.game = game
        self._build_ui()

    def _build_ui(self):
        layout = self.get_container()
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        button_layout = QVBoxLayout()
        button_layout.setSpacing(10)
        button_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # --- ÚJ JÁTÉK ---
        new_btn = ClickableImageButton(
            "Assets/Images/Buttons/NewGameNormal.png",
            "Assets/Images/Buttons/NewGameHover.png",
            scale_factor=0.60,
        )
        new_btn.set_on_click(self.game.start_new_game_dialog)
        button_layout.addWidget(new_btn, alignment=Qt.AlignmentFlag.AlignCenter)

        # --- JÁTÉK BETÖLTÉSE ---
        load_btn = ClickableImageButton(
            "Assets/Images/Buttons/LoadNormal.png",
            "Assets/Images/Buttons/LoadHover.png",
            scale_factor=0.60,
        )
        load_btn.set_on_click(self.game.menu_load_game)
        button_layout.addWidget(load_btn, alignment=Qt.AlignmentFlag.AlignCenter)

        # --- CREATOR MÓD ---
        creator_btn = ClickableImageButton(
            "Assets/Images/Buttons/CreatorNormal.png",
            "Assets/Images/Buttons/CreatorHover.png",
            scale_factor=0.60,
        )
        creator_btn.set_on_click(self.game.open_creator_tool)
        button_layout.addWidget(creator_btn, alignment=Qt.AlignmentFlag.AlignCenter)

        # --- KILÉPÉS ---
        quit_btn = ClickableImageButton(
            "Assets/Images/Buttons/QuitNormal.png",
            "Assets/Images/Buttons/QuitHover.png",
            scale_factor=0.60,
        )
        quit_btn.set_on_click(self.game.close)
        button_layout.addWidget(quit_btn, alignment=Qt.AlignmentFlag.AlignCenter)

        layout.addStretch(10)
        layout.addLayout(button_layout)
        layout.addStretch(1)


# ----------------------------------------------------------------------
# Oldal 3 - Pakliépítő
# ----------------------------------------------------------------------


class ClickableArrowButton(QLabel):
    def __init__(self, normal_path, hover_path, size=48, parent=None):
        super().__init__(parent)
        self.normal_pix = QPixmap(normal_path).scaled(
            size,
            size,
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation,
        )
        self.hover_pix = QPixmap(hover_path).scaled(
            size,
            size,
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation,
        )
        self.setPixmap(self.normal_pix)
        self._callback = None
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, False)

    def set_on_click(self, func):
        self._callback = func

    def enterEvent(self, event):
        self.setPixmap(self.hover_pix)

    def leaveEvent(self, event):
        self.setPixmap(self.normal_pix)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton and self._callback:
            self._callback()


class CardWidget(QFrame):
    """
    Kompakt, elemi színezésű kártya:

    - fix szélesség: 180 px
    - nem vágja le a kártya képét
    - a keret színe az elemhez igazodik (Air / Earth / Fire / Water)
    - a style_id csak a kártyakép kiválasztására szolgál
    - hoverkor finom világosítás
    """

    CARD_WIDTH = 180
    IMAGE_WIDTH = 140
    MIN_HEIGHT = 190

    BORDER_COLORS = {
        "Levego": "#70c7ff",
        "Fold": "#7a8b4d",
        "Tuz": "#d04a29",
        "Viz": "#5ab7d4",
    }

    BORDER_COLORS_HOVER = {
        "Levego": "#a2e0ff",
        "Fold": "#a2c06b",
        "Tuz": "#ff6a4a",
        "Viz": "#7bd5f2",
    }

    def __init__(self, card, world, parent=None):
        super().__init__(parent)

        self.card = card

        # ---- STYLE A WORLD-BŐL (csak a képhez) ----
        if card.name in world.simple_styles:
            style_id = world.simple_styles[card.name]
        elif card.name in world.leader_styles:
            style_id = world.leader_styles[card.name]
        else:
            style_id = 1

        element = card.element.capitalize()
        img_path = f"Assets/Images/Cards/{element}{style_id}.png"
        self.pixmap = QPixmap(img_path)

        # ---- ELEMI SZÍNPALETTA ----
        self.border_color = self.BORDER_COLORS.get(element, "#888888")
        self.border_hover = self.BORDER_COLORS_HOVER.get(element, "#bbbbbb")

        # ---- ALAP KINÉZET ----
        self.setFrameStyle(QFrame.Shape.StyledPanel)
        self.setObjectName("CardWidgetFrame")
        self._apply_style(hover=False)

        # ---- FONTOK ----
        font_id = QFontDatabase.addApplicationFont("Assets/Font/AlmendraSC-Regular.ttf")
        if font_id != -1:
            family = QFontDatabase.applicationFontFamilies(font_id)[0]
        else:
            family = "Times New Roman"

        name_font = QFont(family, 14)
        stat_font = QFont(family, 11)

        # ---- NÉV ----
        self.name_label = QLabel(card.name)
        self.name_label.setFont(name_font)
        self.name_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.name_label.setStyleSheet(
            "color: white; padding: 2px 6px; "
            "background: rgba(0, 0, 0, 150); border-radius: 6px;"
        )

        # ---- KÉP ----
        self.image_label = QLabel()
        self.image_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        if not self.pixmap.isNull():
            scaled = self.pixmap.scaledToWidth(
                self.IMAGE_WIDTH, Qt.TransformationMode.SmoothTransformation
            )
            self.image_label.setPixmap(scaled)

        # ---- STAT BOX ----
        stats_widget = QWidget()
        stats_layout = QHBoxLayout(stats_widget)
        stats_layout.setContentsMargins(0, 0, 0, 0)
        stats_layout.setSpacing(0)

        hp_label = QLabel(f"❤️ {card.health}")
        hp_label.setFont(stat_font)
        hp_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        hp_label.setStyleSheet(
            "color: #ffb3b3; background: rgba(0,0,0,160); padding: 2px 10px; "
            "border-top-left-radius: 8px; border-bottom-left-radius: 8px;"
        )

        dmg_label = QLabel(f"⚔️ {card.damage}")
        dmg_label.setFont(stat_font)
        dmg_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        dmg_label.setStyleSheet(
            "color: #ffd0aa; background: rgba(0,0,0,160); padding: 2px 10px; "
            "border-top-right-radius: 8px; border-bottom-right-radius: 8px;"
        )

        stats_layout.addWidget(hp_label)
        stats_layout.addWidget(dmg_label)

        # ---- LAYOUT ----
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(6, 6, 6, 6)
        main_layout.setSpacing(4)
        main_layout.addWidget(self.name_label)
        main_layout.addWidget(self.image_label)
        main_layout.addWidget(stats_widget)

        self.setFixedWidth(self.CARD_WIDTH)
        self.setMinimumHeight(self.MIN_HEIGHT)
        self.setMaximumHeight(self.MIN_HEIGHT + 10)
        self.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)

    def _apply_style(self, hover: bool):
        border = self.border_hover if hover else self.border_color
        bg = "rgba(25,25,25,180)" if not hover else "rgba(40,40,40,210)"
        self.setStyleSheet(
            f"""
            QFrame#CardWidgetFrame {{
                border: 3px solid {border};
                border-radius: 12px;
                background-color: {bg};
            }}
            """
        )

    def enterEvent(self, event):
        self._apply_style(hover=True)
        return super().enterEvent(event)

    def leaveEvent(self, event):
        self._apply_style(hover=False)
        return super().leaveEvent(event)

    def resizeEvent(self, event):
        if not self.pixmap.isNull():
            target_w = min(self.IMAGE_WIDTH, self.width() - 20)
            scaled = self.pixmap.scaledToWidth(
                target_w, Qt.TransformationMode.SmoothTransformation
            )
            self.image_label.setPixmap(scaled)
        return super().resizeEvent(event)


class DeckBuilderPage(BackgroundWidget):
    def __init__(self, game):
        super().__init__("Assets/Images/Backgrounds/Game.png", game)
        self.game = game
        self._build_ui()

    # -------------------------------------------------------------
    def _build_ui(self):
        layout = self.get_container()
        layout.setContentsMargins(30, 20, 30, 20)
        layout.setSpacing(10)

        # --- TOP TITLE: AssembleDeck PNG (ésszerű méretben) ---
        title_label = QLabel()
        title_pix = QPixmap("Assets/Images/Scrolls/AssembleDeck.png")
        if not title_pix.isNull():
            title_pix = title_pix.scaledToWidth(
                420, Qt.TransformationMode.SmoothTransformation
            )
        title_label.setPixmap(title_pix)
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title_label)

        # --- KÖZÉPSŐ TERÜLET: kártyalista + pakli ---
        middle = QHBoxLayout()
        middle.setSpacing(40)
        layout.addLayout(middle, stretch=1)

        # ---------------- BAL (Cards) ----------------
        left_box = QVBoxLayout()
        left_box.setSpacing(8)
        middle.addLayout(left_box, stretch=1)

        left_title = QLabel()
        left_title_pix = QPixmap("Assets/Images/Scrolls/Cards.png")
        if not left_title_pix.isNull():
            left_title_pix = left_title_pix.scaledToWidth(
                350, Qt.TransformationMode.SmoothTransformation
            )
        left_title.setPixmap(left_title_pix)
        left_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        left_box.addWidget(left_title)

        self.collection_area = QScrollArea()
        self.collection_area.setWidgetResizable(True)
        self.collection_area.setStyleSheet(
            "QScrollArea {{ background: transparent; border: none; }}"
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

        # ---------------- JOBB (Deck) ----------------
        right_box = QVBoxLayout()
        right_box.setSpacing(8)
        middle.addLayout(right_box, stretch=1)

        right_title = QLabel()
        right_title_pix = QPixmap("Assets/Images/Scrolls/Deck.png")
        if not right_title_pix.isNull():
            right_title_pix = right_title_pix.scaledToWidth(
                350, Qt.TransformationMode.SmoothTransformation
            )
        right_title.setPixmap(right_title_pix)
        right_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        right_box.addWidget(right_title)

        self.deck_area = QScrollArea()
        self.deck_area.setWidgetResizable(True)
        self.deck_area.setStyleSheet(
            "QScrollArea {{ background: transparent; border: none; }}"
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

        # Info + vissza
        self.deck_info_label = QLabel("")
        self.deck_info_label.setStyleSheet("font-size: 11px; color: white;")
        self.deck_info_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.deck_info_label)

        back_btn = ClickableImageButton(
            "Assets/Images/Buttons/QuitNormal.png",
            "Assets/Images/Buttons/QuitHover.png",
            scale_factor=0.25,
        )
        # Vissza a világnézetbe
        back_btn.set_on_click(self.game.show_library_page)
        layout.addWidget(back_btn, alignment=Qt.AlignmentFlag.AlignCenter)

    # -------------------------------------------------------------
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

        # --- Gyűjtemény ---
        for card in player.collection.values():
            row = self._create_collection_row(card, deck_full)
            self.collection_layout.addWidget(row)

        # --- Pakli ---
        for name in player.deck:
            card = player.collection.get(name)
            if card:
                row = self._create_deck_row(card)
                self.deck_layout.addWidget(row)

        self.deck_info_label.setText(
            f"Gyűjtemény: {len(player.collection)} kártya • Pakli: {len(player.deck)}/{max_size}"
        )

    def _create_collection_row(self, card, deck_full: bool):
        row = QWidget()
        row.setMaximumHeight(220)  # elég hely az új kompakt kártyához
        h = QHBoxLayout(row)
        h.setContentsMargins(0, 0, 0, 0)
        h.setSpacing(8)
        h.setAlignment(Qt.AlignmentFlag.AlignVCenter)

        card_widget = CardWidget(card, self.game.environment.world)
        h.addWidget(card_widget)

        btn = ClickableArrowButton(
            "Assets/Images/Arrows/RightNormal.png",
            "Assets/Images/Arrows/RightHover.png",
            size=40,
        )
        btn.set_on_click(lambda: self._add_to_deck(card.name))
        btn.setEnabled(not deck_full)
        h.addWidget(btn)

        return row

    def _create_deck_row(self, card):
        row = QWidget()
        row.setMaximumHeight(220)
        h = QHBoxLayout(row)
        h.setContentsMargins(0, 0, 0, 0)
        h.setSpacing(8)
        h.setAlignment(Qt.AlignmentFlag.AlignVCenter)

        btn = ClickableArrowButton(
            "Assets/Images/Arrows/LeftNormal.png",
            "Assets/Images/Arrows/LeftHover.png",
            size=40,
        )
        btn.set_on_click(lambda: self._remove_from_deck(card.name))
        h.addWidget(btn)

        card_widget = CardWidget(card, self.game.environment.world)
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


# ----------------------------------------------------------------------
# Oldal 4 - Kazamatatérkép
# ----------------------------------------------------------------------


class DungeonListItem(QFrame):
    """
    Egy kazamata listaelem:
    - Balra: dungeon háttérképe
    - Jobbra: név + leírás + kártyák (2×2 grid)
    - Legeslegalul középen: Harc gomb
    """

    BORDER_COLORS = {
        "egyszeru": "#50d6d6",  # türkiz
        "kis": "#7a3db8",  # sötét lila
        "nagy": "#d4af37",  # arany
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

        # -- Felső rész: kép + szöveg --
        top = QHBoxLayout()
        top.setSpacing(12)
        main.addLayout(top)

        # Dungeon háttérképe
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

        # Jobb oldal: név, info, kártyák grid
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

        # ---- 2×2-es GRID a dungeon kártyáknak ----
        cards_container = QWidget()
        cards_container.setStyleSheet("background: transparent;")

        grid = QGridLayout(cards_container)
        grid.setContentsMargins(0, 0, 0, 0)
        grid.setHorizontalSpacing(8)
        grid.setVerticalSpacing(8)

        seq = dungeon.card_sequence(world)
        if seq:
            cols = 2
            for i, card_def in enumerate(seq):
                cw = CardWidget(card_def, world)
                row = i // cols
                col = i % cols
                grid.addWidget(cw, row, col)

        right.addWidget(cards_container)

        # ---- Harc gomb középen ----
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

        # Címsor: pergamen kép (Dungeons.png)
        self.title_label = QLabel()
        title_pix = QPixmap("Assets/Images/Scrolls/Dungeons.png")
        if not title_pix.isNull():
            title_pix = title_pix.scaledToWidth(
                420, Qt.TransformationMode.SmoothTransformation
            )
        self.title_label.setPixmap(title_pix)
        self.title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.title_label)

        # Információs szöveg (hiba / nagy kazamata infó)
        self.info_label = QLabel("")
        self.info_label.setStyleSheet("color: white; font-size: 14px;")
        self.info_label.setWordWrap(True)
        layout.addWidget(self.info_label)

        # Kazamaták listája (scrollozható)
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

        # Alsó gombsor: Pakli módosítása / Mentés / Vissza
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

        btn_row.addStretch(1)

        self.back_menu_btn = ClickableImageButton(
            "Assets/Images/Buttons/BackNormal.png",
            "Assets/Images/Buttons/BackHover.png",
            scale_factor=0.4,
        )
        # Vissza a világnézetbe (könyvtár)
        self.back_menu_btn.set_on_click(self.game.show_library_page)
        btn_row.addWidget(self.back_menu_btn)

    def _clear_list(self):
        while self.list_layout.count():
            item = self.list_layout.takeAt(0)
            w = item.widget()
            if w:
                w.deleteLater()

    def refresh_from_environment(self):
        # lista ürítése
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


# ----------------------------------------------------------------------
# Új oldal - Világnézet / Könyvtár
# ----------------------------------------------------------------------


class WorldLibraryPage(BackgroundWidget):
    """
    Világnézet / Könyvtár HUB:
    Innen éred el külön nézetben
    - a világkártyákat,
    - a kazamatákat (kazamataválasztó),
    - a saját gyűjteményedet,
    - a pakliépítőt,
    - és vissza tudsz lépni a főmenübe.
    """

    def __init__(self, game: "DamareenGameWindow"):
        super().__init__("Assets/Images/Backgrounds/Library.png", game)
        self.game = game
        self._build_ui()

    def _build_ui(self):
        layout = self.get_container()
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(20)

        # Felső információk: világ neve, nehézség
        self.header_label = QLabel("")
        self.header_label.setStyleSheet("color: white; font-size: 14px;")
        self.header_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.header_label)

        layout.addStretch(1)

        # Középső nagy gombok
        center_layout = QVBoxLayout()
        center_layout.setSpacing(12)
        center_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addLayout(center_layout, stretch=0)

        # Világkártyák nézet
        cards_view_btn = ClickableImageButton(
            "Assets/Images/Buttons/CardsNormal.png",
            "Assets/Images/Buttons/CardsHover.png",
            scale_factor=0.5,
        )
        cards_view_btn.set_on_click(self.game.show_world_cards_page)
        center_layout.addWidget(cards_view_btn, alignment=Qt.AlignmentFlag.AlignCenter)

        # Kazamaták (kazamataválasztó nézet / MapPage)
        dungeons_btn = ClickableImageButton(
            "Assets/Images/Buttons/DungeonsNormal.png",
            "Assets/Images/Buttons/DungeonsHover.png",
            scale_factor=0.5,
        )
        dungeons_btn.set_on_click(self.game.show_map_page)
        center_layout.addWidget(dungeons_btn, alignment=Qt.AlignmentFlag.AlignCenter)

        # Gyűjtemény nézet
        collection_btn = ClickableImageButton(
            "Assets/Images/Buttons/CollectionNormal.png",
            "Assets/Images/Buttons/CollectionHover.png",
            scale_factor=0.5,
        )
        collection_btn.set_on_click(self.game.show_collection_page)
        center_layout.addWidget(collection_btn, alignment=Qt.AlignmentFlag.AlignCenter)

        layout.addStretch(1)

        # Alsó gombsor: Pakliépítő + Főmenü
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

        back_btn = ClickableImageButton(
            "Assets/Images/Buttons/BackNormal.png",
            "Assets/Images/Buttons/BackHover.png",
            scale_factor=0.4,
        )
        back_btn.set_on_click(self.game.show_main_menu)
        bottom_row.addWidget(back_btn)

    def refresh_from_game(self):
        env = self.game.environment
        state = self.game.state
        if not (env and state):
            self.header_label.setText(
                "Nincs aktív játék. Indíts vagy tölts be egy kalandot."
            )
            return

        world = env.world
        self.header_label.setText(
            f"Világ: {getattr(world, 'name', 'ismeretlen')} • Nehézség: {state.difficulty}"
        )


class WorldCardsPage(BackgroundWidget):
    """
    Világkártyák külön nézetben:
    - minden világkártya GRID-ben
    - lefelé scrollozható
    """

    def __init__(self, game: "DamareenGameWindow"):
        super().__init__("Assets/Images/Backgrounds/Library.png", game)
        self.game = game
        self._build_ui()

    def _build_ui(self):
        layout = self.get_container()
        layout.setContentsMargins(20, 20, 20, 10)
        layout.setSpacing(10)

        self.header_label = QLabel("Világkártyák")
        self.header_label.setStyleSheet("color: white; font-size: 14px;")
        self.header_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.header_label)

        # Címsor pergamennel
        title_label = QLabel()
        title_pix = QPixmap("Assets/Images/Scrolls/WorldCards.png")
        if not title_pix.isNull():
            title_pix = title_pix.scaledToWidth(
                320, Qt.TransformationMode.SmoothTransformation
            )
        title_label.setPixmap(title_pix)
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title_label)

        # Scroll + GRID
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

        # Alsó gombsor
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
            self.header_label.setText("Nincs aktív játék.")
            return

        world = env.world
        self.header_label.setText(
            f"Világ: {getattr(world, 'name', 'ismeretlen')} • Nehézség: {state.difficulty}"
        )

        world_cards = []
        if hasattr(world, "iter_simple_cards"):
            world_cards.extend(world.iter_simple_cards())
        if hasattr(world, "iter_leader_cards"):
            world_cards.extend(world.iter_leader_cards())

        cols = 4  # 4 oszlopos GRID (4 * 180px ~ 720px szélesség)
        row = col = 0
        for c in world_cards:
            w = CardWidget(c, world)
            self.grid_layout.addWidget(w, row, col)
            col += 1
            if col >= cols:
                col = 0
                row += 1

        # Az alján legyen egy kis rugalmasság
        self.grid_layout.setRowStretch(row + 1, 1)


class CollectionPage(BackgroundWidget):
    """
    Játékos gyűjteménye külön nézetben:
    - a játékos összes kártyája GRID-ben
    - lefelé scrollozható
    """

    def __init__(self, game: "DamareenGameWindow"):
        super().__init__("Assets/Images/Backgrounds/Library.png", game)
        self.game = game
        self._build_ui()

    def _build_ui(self):
        layout = self.get_container()
        layout.setContentsMargins(20, 20, 20, 10)
        layout.setSpacing(10)

        self.header_label = QLabel("Gyűjteményed")
        self.header_label.setStyleSheet("color: white; font-size: 14px;")
        self.header_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.header_label)

        # Címsor (itt egyszerű szöveg, vagy tehetsz Scrolls/Cards.png-t is)
        title_lbl = QLabel("Gyűjteményed")
        title_font = QFont()
        title_font.setPointSize(16)
        title_font.setBold(True)
        title_lbl.setFont(title_font)
        title_lbl.setStyleSheet("color: white;")
        title_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title_lbl)

        # Scroll + GRID
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

        # Alsó gombsor
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
            self.header_label.setText("Nincs aktív játék.")
            return

        world = env.world
        player = state.player

        self.header_label.setText(
            f"Világ: {getattr(world, 'name', 'ismeretlen')} • Nehézség: {state.difficulty}"
        )

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


# ----------------------------------------------------------------------
# Oldal 5 - Harcnézet
# ----------------------------------------------------------------------


class BattleAnimationPage(BackgroundWidget):
    """
    Harci animáció log alapján.
    """

    def __init__(self, game):
        super().__init__("Assets/Images/Backgrounds/egyszeru.png", game)
        self.game = game

        self.log = []
        self.index = 0

        self.player_label = QLabel(self)
        self.enemy_label = QLabel(self)
        self.player_hp_label = QLabel(self)
        self.enemy_hp_label = QLabel(self)

        self.player_current = None
        self.enemy_current = None

        self.player_hp = 0
        self.enemy_hp = 0

        # futó animáció referencia, hogy ne gyűjtse ki a GC
        self._current_attack_anim = None

        self._build_ui()

    # -------------------------------------------------------------
    # Segédfüggvény: kártya lekérése a worldből (sima vagy vezér)
    # -------------------------------------------------------------
    def get_any_card_from_world(self, world, name):
        c = world.get_simple_card(name)
        if c not in (-1, False):
            return c
        c = world.get_leader_card(name)
        if c not in (-1, False):
            return c
        return None

    # -------------------------------------------------------------
    def _build_ui(self):
        layout = self.get_container()
        layout.setContentsMargins(20, 20, 20, 20)

        title = QLabel("Harc kezdődik…")
        title.setStyleSheet("color: white; font-size: 24px; font-weight: bold;")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.title_label = title
        layout.addWidget(title)

        field = QWidget()
        f = QHBoxLayout(field)
        f.setContentsMargins(0, 40, 0, 40)
        f.setSpacing(80)

        # játékos sprite
        self.player_label.setScaledContents(True)
        self.player_label.setFixedSize(260, 300)
        f.addWidget(
            self.player_label,
            alignment=Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignBottom,
        )

        # ellenfél sprite
        self.enemy_label.setScaledContents(True)
        self.enemy_label.setFixedSize(260, 300)
        f.addWidget(
            self.enemy_label,
            alignment=Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignBottom,
        )

        layout.addWidget(field)

        # HP-k
        hp = QHBoxLayout()
        self.player_hp_label.setStyleSheet("color: white; font-size: 18px;")
        self.enemy_hp_label.setStyleSheet("color: white; font-size: 18px;")

        hp.addWidget(self.player_hp_label, alignment=Qt.AlignmentFlag.AlignLeft)
        hp.addWidget(self.enemy_hp_label, alignment=Qt.AlignmentFlag.AlignRight)
        layout.addLayout(hp)

    # -------------------------------------------------------------
    # Harc indítása
    # -------------------------------------------------------------
    def start_battle(self, dungeon, result, reward_msg):
        self.log = list(result.log_lines)
        self.index = 0
        self.result = result
        self.reward_msg = reward_msg

        bg = {
            "egyszeru": "Assets/Images/Backgrounds/egyszeru.png",
            "kis": "Assets/Images/Backgrounds/kis.png",
            "nagy": "Assets/Images/Backgrounds/nagy.png",
        }.get(dungeon.kind, "Assets/Images/Backgrounds/egyszeru.png")
        self.set_background(bg)

        self.player_current = None
        self.enemy_current = None
        self.player_hp = 0
        self.enemy_hp = 0

        self._preprocess_initial_cards()

        if self.player_current:
            self.load_character_sprite(self.player_label, self.player_current)
        if self.enemy_current:
            self.load_character_sprite(self.enemy_label, self.enemy_current)

        self.update_hp_labels()

        QTimer.singleShot(600, self.next_step)

    # -------------------------------------------------------------
    def _preprocess_initial_cards(self):
        for line in self.log:
            parts = line.split(";")
            if len(parts) < 4:
                continue

            actor = parts[1]
            action = parts[2]

            if action != "kijatszik":
                continue

            name = parts[3]
            hp = int(parts[5])  # log: ...;damage;hp;element

            if actor == "jatekos" and not self.player_current:
                self.player_current = name
                self.player_hp = hp

            elif actor == "kazamata" and not self.enemy_current:
                self.enemy_current = name
                self.enemy_hp = hp

            if self.player_current and self.enemy_current:
                return

    # -------------------------------------------------------------
    # Sprite betöltés
    # -------------------------------------------------------------
    def load_character_sprite(self, label, card_name):
        world = self.game.environment.world
        card = self.get_any_card_from_world(world, card_name)

        if not card:
            pix = QPixmap("Assets/Images/Characters/Fold1.png")
        else:
            elem = card.element.capitalize()
            style = world.simple_styles.get(card.name) or world.leader_styles.get(
                card.name, 1
            )
            path = f"Assets/Images/Characters/{elem}{style}.png"
            pix = QPixmap(path)
            if pix.isNull():
                pix = QPixmap("Assets/Images/Characters/Fold1.png")

        label.setPixmap(
            pix.scaled(
                label.width(),
                label.height(),
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation,
            )
        )

    # -------------------------------------------------------------
    def update_hp_labels(self):
        self.player_hp_label.setText(f"❤️ {self.player_hp}")
        self.enemy_hp_label.setText(f"❤️ {self.enemy_hp}")

    # -------------------------------------------------------------
    def next_step(self):
        if self.index >= len(self.log):
            self.finish_battle()
            return

        line = self.log[self.index]
        self.index += 1

        parts = line.split(";")
        if not parts:
            QTimer.singleShot(10, self.next_step)
            return

        # kezdeti sor: "harc kezdodik;KazamataNev"
        if parts[0].startswith("harc kezdodik"):
            QTimer.singleShot(10, self.next_step)
            return

        if len(parts) < 3:
            # biztonsági: ha valami furcsa sor jön, lépjünk tovább
            QTimer.singleShot(10, self.next_step)
            return

        actor = parts[1]
        action = parts[2]

        # új kijátszott lap
        if action == "kijatszik":
            name = parts[3]
            hp = int(parts[5])

            if actor == "jatekos":
                self.player_current = name
                self.player_hp = hp
                self.load_character_sprite(self.player_label, name)
            else:
                self.enemy_current = name
                self.enemy_hp = hp
                self.load_character_sprite(self.enemy_label, name)

            self.update_hp_labels()
            QTimer.singleShot(400, self.next_step)
            return

        # támadás
        if action == "tamad":
            dmg = int(parts[4])
            attacker = "enemy" if actor == "kazamata" else "player"
            self.animate_attack(attacker, dmg)
            return

        # ismeretlen akció – lépjünk tovább
        QTimer.singleShot(300, self.next_step)

    # -------------------------------------------------------------
    def animate_attack(self, attacker, dmg):
        from PySide6.QtCore import (
            QPropertyAnimation,
            QPoint,
            QEasingCurve,
            QSequentialAnimationGroup,
        )

        if attacker == "player":
            mover = self.player_label
            target = self.enemy_label
        else:
            mover = self.enemy_label
            target = self.player_label

        start = mover.pos()
        hit = start + QPoint(40 if attacker == "player" else -40, -10)

        anim1 = QPropertyAnimation(mover, b"pos")
        anim1.setDuration(200)
        anim1.setEndValue(hit)
        anim1.setEasingCurve(QEasingCurve.Type.OutQuad)

        shake = QPropertyAnimation(target, b"pos")
        shake.setDuration(160)
        shake.setKeyValueAt(0.3, target.pos() + QPoint(8, -4))
        shake.setKeyValueAt(0.6, target.pos() + QPoint(-8, 4))
        shake.setEndValue(target.pos())

        anim2 = QPropertyAnimation(mover, b"pos")
        anim2.setDuration(200)
        anim2.setEndValue(start)
        anim2.setEasingCurve(QEasingCurve.Type.InQuad)

        # fontos: adjunk szülőt, és tartsunk referenciát
        grp = QSequentialAnimationGroup(self)
        grp.addAnimation(anim1)
        grp.addAnimation(shake)
        grp.addAnimation(anim2)

        self._current_attack_anim = grp

        grp.finished.connect(lambda: self._on_attack_anim_finished(attacker, dmg, grp))
        grp.start()

    def _on_attack_anim_finished(self, attacker, dmg, grp):
        # takarítás + sebzés alkalmazása
        self._current_attack_anim = None
        grp.deleteLater()
        self.apply_damage(attacker, dmg)

    # -------------------------------------------------------------
    def apply_damage(self, attacker, dmg):
        if attacker == "player":
            self.enemy_hp -= dmg
            if self.enemy_hp <= 0:
                self.enemy_hp = 0
                self.kill_character(self.enemy_label)
        else:
            self.player_hp -= dmg
            if self.player_hp <= 0:
                self.player_hp = 0
                self.kill_character(self.player_label)

        self.update_hp_labels()
        QTimer.singleShot(600, self.next_step)

    # -------------------------------------------------------------
    def kill_character(self, label):
        from PySide6.QtCore import QPropertyAnimation

        fade = QPropertyAnimation(label, b"windowOpacity", label)
        fade.setDuration(600)
        fade.setEndValue(0)
        fade.start()

    # -------------------------------------------------------------
    def finish_battle(self):
        outcome = self.result.outcome
        self.game.show_battle_end_screen(outcome, self.reward_msg)


class VictoryLosePage(BackgroundWidget):
    """
    Győzelem / Vereség végképernyő
    - háttér: Victory.png vagy Lose.png
    - középen pergamen: Scrolls/Victory.png vagy Scrolls/Lose.png
    - középen Done gomb
    - fade-in animáció
    """

    def __init__(self, game):
        # ideiglenes háttér, később beállítjuk .show_result()-ban
        super().__init__("Assets/Images/Backgrounds/Victory.png", game)
        self.game = game

        # konténer a tartalomnak
        self.root = self.get_container()
        self.root.setContentsMargins(0, 0, 0, 0)
        self.root.setSpacing(20)

        # Fade-in overlay
        self.overlay_opacity = 0.0
        self.overlay = QWidget(self)
        self.overlay.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        self.overlay.raise_()

        self.vbox = QVBoxLayout()
        self.vbox.setContentsMargins(0, 60, 0, 40)
        self.vbox.setSpacing(20)
        self.vbox.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.root.addLayout(self.vbox)

        # Pergamen
        self.scroll_label = QLabel()
        self.scroll_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.vbox.addWidget(self.scroll_label)

        # Szöveg a pergamenen (opcionális)
        self.text_label = QLabel("")
        self.text_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.text_label.setStyleSheet(
            "color: #2b1a08; font-size: 22px; font-weight: bold;"
        )
        self.vbox.addWidget(self.text_label)

        # Done gomb
        self.done_btn = ClickableImageButton(
            "Assets/Images/Buttons/DoneNormal.png",
            "Assets/Images/Buttons/DoneHover.png",
            scale_factor=0.6,
        )
        self.done_btn.set_on_click(
            lambda: self.game.show_deck_page()
        )  # Vissza a paklihoz

        self.vbox.addWidget(self.done_btn, alignment=Qt.AlignmentFlag.AlignCenter)

    # -------------------------------------------------------------------------
    # Fade overlay paint
    # -------------------------------------------------------------------------
    def resizeEvent(self, event):
        self.overlay.setGeometry(self.rect())
        return super().resizeEvent(event)

    def paintEvent(self, event):
        if not self.overlay.isVisible() or self.overlay.width() == 0:
            return super().paintEvent(event)

        super().paintEvent(event)

        painter = QPainter(self.overlay)
        if not painter.isActive():
            return
        painter.setOpacity(1.0 - self.overlay_opacity)
        painter.fillRect(self.overlay.rect(), QColor(0, 0, 0))
        painter.end()

    # -------------------------------------------------------------------------
    # Eredmény megjelenítése
    # -------------------------------------------------------------------------
    def show_result(self, outcome, reward_msg=""):
        """
        outcome: "win" vagy "lose"
        reward_msg: pl. "+1 sebzés...", "+2 HP..."
        """

        if outcome == "win":
            self.set_background("Assets/Images/Backgrounds/Victory.png")
            scroll_path = "Assets/Images/Scrolls/Victory.png"
            main_text = "Győzelem!"
        else:
            self.set_background("Assets/Images/Backgrounds/Lose.png")
            scroll_path = "Assets/Images/Scrolls/Lose.png"
            main_text = "Vereség…"

        # Pergamen beállítása
        pix = QPixmap(scroll_path)
        pix = pix.scaledToWidth(480, Qt.TransformationMode.SmoothTransformation)
        self.scroll_label.setPixmap(pix)

        # Szöveg
        full_text = main_text
        if reward_msg:
            full_text += f"\n\n{reward_msg}"

        self.text_label.setText(full_text)

        # Fade-in animáció
        from PySide6.QtCore import QPropertyAnimation

        anim = QPropertyAnimation(self, b"overlay_opacity")
        anim.setDuration(1500)
        anim.setStartValue(0.0)
        anim.setEndValue(1.0)
        anim.start()

        # betöltés a stackbe
        self.game.stack.setCurrentWidget(self)

    # Property hogy lehessen animálni a fade-et
    def get_overlay_opacity(self):
        return self.overlay_opacity

    def set_overlay_opacity(self, value):
        self.overlay_opacity = value
        self.update()

    overlay_opacity_prop = Property(float, get_overlay_opacity, set_overlay_opacity)


# ----------------------------------------------------------------------
# Fő ablak - játékvezérlés
# ----------------------------------------------------------------------


class DamareenGameWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.environment: Optional[Environment] = None
        self.state: Optional[State] = None

        self.current_dungeon: Optional[Dungeon] = None
        self.last_battle_result: Optional[BattleResult] = None
        self.last_battle_reward_msg: str = ""
        self.last_battle_final_log_line: str = ""

        self.setWindowTitle("Damareen")
        self.resize(800, 600)

        self.stack = QStackedWidget()
        self.setCentralWidget(self.stack)

        self.main_menu = MainMenuPage(self)
        self.library_page = WorldLibraryPage(self)
        self.world_cards_page = WorldCardsPage(self)
        self.collection_page = CollectionPage(self)
        self.deck_page = DeckBuilderPage(self)
        self.map_page = MapPage(self)
        self.battle_animation_page = BattleAnimationPage(self)
        self.victory_lose_page = VictoryLosePage(self)

        self.stack.addWidget(self.main_menu)  # index 0
        self.stack.addWidget(self.library_page)  # index 1
        self.stack.addWidget(self.world_cards_page)  # index 2
        self.stack.addWidget(self.collection_page)  # index 3
        self.stack.addWidget(self.deck_page)  # index 4
        self.stack.addWidget(self.map_page)  # index 5
        self.stack.addWidget(self.battle_animation_page)  # index 6
        self.stack.addWidget(self.victory_lose_page)  # index 7

        self._build_menu_bar()

        self.sound = SoundManager()

        self.sound.load("click", "Assets/Sounds/click.wav", 0.8)
        self.sound.load("door", "Assets/Sounds/door.wav", 0.9)
        self.sound.load("ambience", "Assets/Sounds/ambience.wav", 0.5)
        self.sound.load("trumpets", "Assets/Sounds/trumpets.wav", 0.9)
        self.sound.load("whoosh", "Assets/Sounds/whoosh.wav", 0.9)
        self.sound.load("strike", "Assets/Sounds/strike.wav", 0.9)
        self.sound.load("wind", "Assets/Sounds/wind.wav", 0.7)
        self.sound.load("shuffle", "Assets/Sounds/shuffle.wav", 0.7)
        self.sound.load("throw", "Assets/Sounds/throw.wav", 0.7)
        self.sound.load("sword", "Assets/Sounds/sword.wav", 0.7)
        self.sound.load("arrow", "Assets/Sounds/arrow.wav", 0.7)
        self.sound.load("stapling", "Assets/Sounds/stapling.wav", 0.7)

    # ---- Menü / navigáció ----

    def _build_menu_bar(self):
        menubar = self.menuBar()
        game_menu = menubar.addMenu("&Játék")

        new_game_action = QAction("Új játék", self)
        load_action = QAction("Játék betöltése…", self)
        save_action = QAction("Játék mentése…", self)
        exit_action = QAction("Kilépés", self)

        new_game_action.triggered.connect(self.start_new_game_dialog)
        load_action.triggered.connect(self.menu_load_game)
        save_action.triggered.connect(self.save_game_dialog)
        exit_action.triggered.connect(self.close)

        game_menu.addAction(new_game_action)
        game_menu.addAction(load_action)
        game_menu.addAction(save_action)
        game_menu.addSeparator()
        game_menu.addAction(exit_action)

        help_menu = menubar.addMenu("&Súgó")
        about_action = QAction("Névjegy", self)

        def on_about():
            QMessageBox.information(
                self,
                "Damareen - Névjegy",
                "Damareen kártyajáték - II. forduló\n\n"
                "Ez egy játékos, gyerekbarát grafikus felület.\n"
                "A háttérben a hivatalos játékmotor (core csomag) fut.",
            )

        about_action.triggered.connect(on_about)
        help_menu.addAction(about_action)

    # Egyszerűen hívható navigációk

    def show_main_menu(self):
        self.stack.setCurrentWidget(self.main_menu)

    def open_creator_tool(self):
        # Lazán importáljuk, hogy a két UI ne függjön egymástól induláskor
        from run_tool import MainWindow as ToolMainWindow

        # Új ablakot nyitunk - a tool külön fut
        self.tool_window = ToolMainWindow()
        self.tool_window.show()

    def show_library_page(self):
        if not (self.environment and self.state):
            show_error(self, "Hiba", "Előbb indíts vagy tölts be egy játékot.")
            return
        self.library_page.refresh_from_game()
        self.stack.setCurrentWidget(self.library_page)

    def show_deck_page(self):
        if not self.state:
            show_error(self, "Hiba", "Előbb indíts vagy tölts be egy játékot.")
            return
        self.deck_page.refresh_from_state()
        self.stack.setCurrentWidget(self.deck_page)

    def show_map_page(self):
        if not self.environment or not self.state:
            show_error(self, "Hiba", "Előbb indíts vagy tölts be egy játékot.")
            return
        self.map_page.refresh_from_environment()
        self.stack.setCurrentWidget(self.map_page)

    def show_world_cards_page(self):
        if not (self.environment and self.state):
            show_error(self, "Hiba", "Előbb indíts vagy tölts be egy játékot.")
            return
        self.world_cards_page.refresh_from_game()
        self.stack.setCurrentWidget(self.world_cards_page)

    def show_collection_page(self):
        if not (self.environment and self.state):
            show_error(self, "Hiba", "Előbb indíts vagy tölts be egy játékot.")
            return
        self.collection_page.refresh_from_game()
        self.stack.setCurrentWidget(self.collection_page)

    def show_battle_animation_page(self):
        self.stack.setCurrentWidget(self.battle_animation_page)

    def show_battle_end_screen(self, outcome, reward_msg):
        self.victory_lose_page.show_result(outcome, reward_msg)

    def start_new_game_dialog(self):
        env_dir = "Environments"
        env_files = []

        if os.path.isdir(env_dir):
            for fname in os.listdir(env_dir):
                if fname.endswith(".json"):
                    path = os.path.join(env_dir, fname)
                    try:
                        env = storage_module.load_environment_from_file(path)
                        env_files.append((env.name, path, env))
                    except:
                        pass

        dlg = EnvironmentChooseDialog(self, env_files)
        if dlg.exec() != QDialog.DialogCode.Accepted or not dlg.selected:
            return

        chosen_name, chosen_path, chosen_env = dlg.selected

        # Nehézség választás
        diff, ok = QInputDialog.getInt(
            self,
            "Nehézség",
            "Válassz nehézséget (0-10):",
            value=0,
            minValue=0,
            maxValue=10,
        )
        if not ok:
            return

        self.start_new_game(chosen_env, diff)

    # ---- Játék indítás / betöltés ----

    def start_new_game(self, environment: Environment, difficulty: int):
        if self.environment and self.state:
            if not ask_yes_no(
                self,
                "Új játék",
                "Ha új játékot indítasz, a jelenlegi kaland mentés nélkül elveszik.\n"
                "Biztosan folytatod?",
            ):
                return
        self.environment = environment
        self.state = environment.new_game(difficulty)

        # Pakliépítő előkészítése
        self.deck_page.refresh_from_state()

        # Világnézet frissítése és megjelenítése
        self.library_page.refresh_from_game()
        self.show_library_page()

    def menu_load_game(self):
        state_dir = "States"
        state_files = []

        if os.path.isdir(state_dir):
            for fname in os.listdir(state_dir):
                if fname.endswith(".json"):
                    path = os.path.join(state_dir, fname)
                    state_files.append((fname, path))

        dlg = StateChooseDialog(self, state_files)
        if dlg.exec() != QDialog.DialogCode.Accepted or not dlg.selected:
            return

        self.load_game_from_path(dlg.selected)

    def load_game_from_path(self, path: str):
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
        except Exception as e:
            show_error(self, "Hiba", f"A mentés betöltése nem sikerült:\n{e}")
            return

        try:
            env_data = data["environment"]
            state_data = data["state"]
            env = storage_module.environment_from_dict(env_data)
            state = storage_module.state_from_dict(state_data)
        except Exception as e:
            show_error(self, "Hiba", f"A mentés formátuma hibás:\n{e}")
            return

        self.environment = env
        self.state = state

        self.deck_page.refresh_from_state()
        self.library_page.refresh_from_game()

        self.show_library_page()
        show_info(self, "Betöltve", "A játékállapot sikeresen betöltve.")

    def save_game_dialog(self):
        if not (self.environment and self.state):
            show_error(self, "Hiba", "Nincs aktív játék, amit menteni lehetne.")
            return
        path, _ = QFileDialog.getSaveFileName(
            self,
            "Játék mentése",
            "damareen_save.json",
            "Damareen mentés (*.json)",
        )
        if not path:
            return
        self.save_game_to_path(path)

    def save_game_to_path(self, path: str):
        assert self.environment and self.state
        data = {
            "environment": storage_module.environment_to_dict(self.environment),
            "state": storage_module.state_to_dict(self.state),
        }
        try:
            with open(path, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            show_error(self, "Hiba", f"A mentés írása nem sikerült:\n{e}")
            return
        show_info(self, "Mentve", "A játékállapot sikeresen elmentve.")

    # ---- Harc indítása ----

    def start_battle_by_name(self, dungeon_name: str):
        if not (self.environment and self.state):
            return
        dungeon = self.environment.world.get_dungeon(dungeon_name)
        if not dungeon:
            show_error(self, "Hiba", f"Ismeretlen kazamata: {dungeon_name}")
            return
        self.start_battle(dungeon)

    def start_battle(self, dungeon: Dungeon):
        if not (self.environment and self.state):
            show_error(self, "Hiba", "Nincs aktív játék.")
            return

        world = self.environment.world
        player = self.state.player

        if dungeon.kind == "nagy" and not can_start_big_dungeon(world, player):
            show_error(
                self,
                "Hiba",
                "Már minden sima világkártyát megszereztél, ezért nagy kazamata ellen nem harcolhatsz.",
            )
            return

        if not player.has_deck():
            show_error(
                self,
                "Hiba",
                "Előbb állíts össze egy érvényes paklit a pakliépítő képernyőn.",
            )
            return

        result = run_battle(world, player, dungeon, difficulty=self.state.difficulty)
        if not result:
            show_error(
                self, "Hiba", "A harc nem indítható (hibás pakli vagy kazamata)."
            )
            return

        reward_msg, final_log_line = apply_battle_rewards(
            world, self.state, dungeon, result
        )

        self.current_dungeon = dungeon
        self.last_battle_result = result
        self.last_battle_reward_msg = reward_msg
        self.last_battle_final_log_line = final_log_line

        # Jutalom után frissítjük a nézeteket
        self.deck_page.refresh_from_state()
        self.map_page.refresh_from_environment()

        self.battle_animation_page.start_battle(dungeon, result, reward_msg)
        self.show_battle_animation_page()


def run_game_mode():
    app = QApplication([])
    window = DamareenGameWindow()
    window.show()
    app.exec()
