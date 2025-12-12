from PySide6.QtCore import Qt
from PySide6.QtGui import QFont, QFontDatabase, QPixmap
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QVBoxLayout,
    QWidget,
)


class CardWidget(QFrame):
    CARD_WIDTH = 180
    IMAGE_WIDTH = 140
    MIN_HEIGHT = 200

    BORDER_COLORS = {
        "Levego": "#70c7ff",
        "Fold": "#7a8b4d",
        "Tuz": "#d04a29",
        "Viz": "#5ab7d4",
    }

    BORDER_COLORS_HOVER = {
        "Levego": "#bde9ff",
        "Fold": "#c4dfa0",
        "Tuz": "#ff917c",
        "Viz": "#9ee6ff",
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

        if card.name in world.leader_styles:
            prefix = "V"
        else:
            prefix = ""

        element = card.element.capitalize()
        img_path = working_dir + f"Assets/Images/Cards/{element}{prefix}{style_id}.png"
        self.pixmap = QPixmap(img_path)

        self.border_color = self.BORDER_COLORS.get(element, "#888")
        self.border_hover = self.BORDER_COLORS_HOVER.get(element, "#bbb")

        self.setObjectName("CardWidgetFrame")
        self._apply_style(hover=False)

        font_id = QFontDatabase.addApplicationFont(
            working_dir + "Assets/Font/AlmendraSC-Regular.ttf"
        )
        family = (
            QFontDatabase.applicationFontFamilies(font_id)[0]
            if font_id != -1
            else "Times New Roman"
        )

        name_font = QFont(family, 16)
        stat_font = QFont(family, 11)

        self.name_label = QLabel(card.name)
        self.name_label.setFont(name_font)
        self.name_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.name_label.setStyleSheet(
            """
            color: white;
            padding: 4px 8px;
            letter-spacing: 1px;
            background: rgba(0,0,0,130);
            border-radius: 10px;
            font-weight: bold;
        """
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

        dmg_label = QLabel(f"⚔️ {card.damage}")
        dmg_label.setFont(stat_font)
        dmg_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        dmg_label.setStyleSheet(
            """
            color: #ffe0c0;
            background: rgba(120, 80, 20, 180);
            padding: 5px 14px;
            border-top-left-radius: 10px;
            border-bottom-left-radius: 10px;
            border-top-right-radius: 0px;
            border-bottom-right-radius: 0px;
            font-weight: bold;
        """
        )

        hp_label = QLabel(f"❤️ {card.health}")
        hp_label.setFont(stat_font)
        hp_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        hp_label.setStyleSheet(
            """
            color: #ffb3b3;
            background: rgba(100,0,0,180);
            padding: 5px 14px;
            border-top-left-radius: 0px;
            border-bottom-left-radius: 0px;
            border-top-right-radius: 10px;
            border-bottom-right-radius: 10px;
            font-weight: bold;
        """
        )

        stats_layout.addWidget(dmg_label)
        stats_layout.addWidget(hp_label)

        self.dmg_label = dmg_label
        self.hp_label = hp_label

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(8, 8, 8, 8)
        main_layout.setSpacing(6)
        main_layout.addWidget(self.name_label)
        main_layout.addWidget(self.image_label)
        main_layout.addWidget(stats_widget)

        self.setFixedWidth(self.CARD_WIDTH)
        self.setMinimumHeight(self.MIN_HEIGHT)

    def _apply_style(self, hover: bool):
        border = self.border_hover if hover else self.border_color

        bg_gradient = (
            f"qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 rgba(50,50,50,230), stop:1 rgba(30,30,30,200))"
            if not hover
            else f"qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 rgba(70,70,70,250), stop:1 rgba(45,45,45,230))"
        )

        self.setStyleSheet(
            f"""
            QFrame#CardWidgetFrame {{
                border: 3px solid {border};
                border-radius: 14px;
                background: {bg_gradient};
            }}

            /* Name label */
            QLabel {{
                color: white;
                font-weight: bold;
                letter-spacing: 1px;
                padding: 4px 8px;
                background: rgba(0,0,0,150);
                border-radius: 10px;
            }}

            /* Damage label */
            QLabel#dmg_label {{
                color: #ffe0c0;
                background: qlineargradient(
                    x1:0, y1:0, x2:1, y2:1,
                    stop:0 rgba(120,80,20,180),
                    stop:1 rgba(180,120,50,180)
                );
                padding: 5px 14px;
                border-top-left-radius: 10px;
                border-bottom-left-radius: 10px;
                border-top-right-radius: 0px;
                border-bottom-right-radius: 0px;
                font-weight: bold;
            }}

            /* Health label */
            QLabel#hp_label {{
                color: #ffb3b3;
                background: qlineargradient(
                    x1:0, y1:0, x2:1, y2:1,
                    stop:0 rgba(100,0,0,180),
                    stop:1 rgba(150,0,0,180)
                );
                padding: 5px 14px;
                border-top-left-radius: 0px;
                border-bottom-left-radius: 0px;
                border-top-right-radius: 10px;
                border-bottom-right-radius: 10px;
                font-weight: bold;
            }}
        """
        )

    def enterEvent(self, event):
        self._apply_style(True)
        return super().enterEvent(event)

    def leaveEvent(self, event):
        self._apply_style(False)
        return super().leaveEvent(event)

    def resizeEvent(self, event):
        if not self.pixmap.isNull():
            target_w = min(self.IMAGE_WIDTH, self.width() - 20)
            scaled = self.pixmap.scaledToWidth(
                target_w, Qt.TransformationMode.SmoothTransformation
            )
            self.image_label.setPixmap(scaled)
        return super().resizeEvent(event)
