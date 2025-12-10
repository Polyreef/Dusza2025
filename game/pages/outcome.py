from PySide6.QtCore import Qt, Property, QPropertyAnimation
from PySide6.QtGui import QColor, QPainter, QPixmap, QFontDatabase, QFont
from PySide6.QtWidgets import QLabel, QVBoxLayout, QWidget

from game.widgets.background import BackgroundWidget
from game.widgets.buttons import ClickableImageButton


class FadeOverlay(QWidget):
    def __init__(self, parent):
        super().__init__(parent)
        self._opacity = 0.0
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)

    def get_opacity(self):
        return self._opacity

    def set_opacity(self, value):
        self._opacity = value
        self.update()

    opacity = Property(float, get_opacity, set_opacity)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setOpacity(self._opacity * 0.7)
        painter.fillRect(self.rect(), QColor(0, 0, 0))
        painter.end()


class VictoryLosePage(BackgroundWidget):
    def __init__(self, game):
        super().__init__(
            game.working_dir + "Assets/Images/Backgrounds/Victory.png", game
        )
        self.game = game

        font_id = QFontDatabase.addApplicationFont(
            self.game.working_dir + "Assets/Font/AlmendraSC-Regular.ttf"
        )
        if font_id != -1:
            family = QFontDatabase.applicationFontFamilies(font_id)[0]
        else:
            family = "Times New Roman"
        self.font_family = QFont(family, 22, QFont.Weight.Bold)

        self.overlay = FadeOverlay(self)
        self.overlay.raise_()

        root = self.get_container()
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(20)

        self.vbox = QVBoxLayout()
        self.vbox.setContentsMargins(0, 60, 0, 40)
        self.vbox.setSpacing(20)
        self.vbox.setAlignment(Qt.AlignmentFlag.AlignCenter)
        root.addLayout(self.vbox)

        self.scroll_label = QLabel()
        self.scroll_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.vbox.addWidget(self.scroll_label)

        self.text_label = QLabel("")
        self.text_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.text_label.setFont(self.font_family)
        self.text_label.setStyleSheet("color: white;")
        self.vbox.addWidget(self.text_label)

        self.done_btn = ClickableImageButton(
            self.game.working_dir + "Assets/Images/Buttons/DoneNormal.png",
            self.game.working_dir + "Assets/Images/Buttons/DoneHover.png",
        )
        self.done_btn.set_on_click(lambda: self.game.show_deck_page())
        self.vbox.addWidget(self.done_btn, alignment=Qt.AlignmentFlag.AlignCenter)

    def resizeEvent(self, event):
        self.overlay.setGeometry(self.rect())
        return super().resizeEvent(event)

    def show_result(self, outcome, reward_msg=""):
        window = self.window()

        if outcome == "win":
            self.set_background(
                self.game.working_dir + "Assets/Images/Backgrounds/Victory.png"
            )
            scroll_path = self.game.working_dir + "Assets/Images/Scrolls/Victory.png"
            main_text = ""

            if hasattr(window, "sound"):
                window.sound.play("trumpets")
        else:
            self.set_background(
                self.game.working_dir + "Assets/Images/Backgrounds/Lose.png"
            )
            scroll_path = self.game.working_dir + "Assets/Images/Scrolls/Lose.png"
            main_text = "Vereség…"

            if hasattr(window, "sound"):
                window.sound.play("sword")

        pix = QPixmap(scroll_path)
        pix = pix.scaledToWidth(480, Qt.TransformationMode.SmoothTransformation)
        self.scroll_label.setPixmap(pix)

        full_text = main_text
        if reward_msg:
            full_text += f" {reward_msg}"

        self.text_label.setText(full_text)

        self.overlay.set_opacity(0.0)

        anim = QPropertyAnimation(self.overlay, b"opacity")
        anim.setDuration(1500)
        anim.setStartValue(0.0)
        anim.setEndValue(1.0)
        anim.start()

        self.game.stack.setCurrentWidget(self)
