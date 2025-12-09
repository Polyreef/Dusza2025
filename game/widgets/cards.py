from PySide6.QtCore import Qt
from PySide6.QtGui import QFont, QFontDatabase, QPixmap
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)


class CardWidget(QFrame):
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

    def __init__(self, card, world, working_dir, parent=None):
        super().__init__(parent)

        self.card = card

        if card.name in world.simple_styles:
            style_id = world.simple_styles[card.name]
        elif card.name in world.leader_styles:
            style_id = world.leader_styles[card.name]
        else:
            style_id = 1

        element = card.element.capitalize()
        img_path = working_dir + f"Assets/Images/Cards/{element}{style_id}.png"
        self.pixmap = QPixmap(img_path)

        self.border_color = self.BORDER_COLORS.get(element, "#888888")
        self.border_hover = self.BORDER_COLORS_HOVER.get(element, "#bbbbbb")

        self.setFrameStyle(QFrame.Shape.StyledPanel)
        self.setObjectName("CardWidgetFrame")
        self._apply_style(hover=False)

        font_id = QFontDatabase.addApplicationFont(working_dir + "Assets/Font/AlmendraSC-Regular.ttf")
        if font_id != -1:
            family = QFontDatabase.applicationFontFamilies(font_id)[0]
        else:
            family = "Times New Roman"

        name_font = QFont(family, 14)
        stat_font = QFont(family, 11)

        self.name_label = QLabel(card.name)
        self.name_label.setFont(name_font)
        self.name_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.name_label.setStyleSheet(
            "color: white; padding: 2px 6px; "
            "background: rgba(0, 0, 0, 150); border-radius: 6px;"
        )

        self.image_label = QLabel()
        self.image_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        if not self.pixmap.isNull():
            scaled = self.pixmap.scaledToWidth(
                self.IMAGE_WIDTH, Qt.TransformationMode.SmoothTransformation
            )
            self.image_label.setPixmap(scaled)

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
