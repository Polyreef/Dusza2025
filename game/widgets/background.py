from PySide6.QtWidgets import QWidget, QLabel, QVBoxLayout
from PySide6.QtGui import QPixmap
from PySide6.QtCore import Qt, QEvent


class BackgroundWidget(QWidget):
    def __init__(self, background_path: str, parent=None):
        super().__init__(parent)
        self.background_path = background_path

        self.bg_label = QLabel(self)
        self.bg_label.setScaledContents(True)
        self.bg_label.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        self.bg_label.lower()

        self._container_layout = QVBoxLayout(self)
        self._container_layout.setContentsMargins(0, 0, 0, 0)
        self._container_layout.setSpacing(0)

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
        self.bg_label.resize(self.size())
        self.update_background()

    def get_container(self):
        return self._container_layout


class ScalableBannerLabel(QLabel):
    def __init__(self, image_path, width_ratio=0.6, parent=None):
        super().__init__(parent)
        self.pix_original = QPixmap(image_path)
        self.width_ratio = width_ratio

        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setScaledContents(False)

    def showEvent(self, event):
        win = self.window()
        if win:
            win.installEventFilter(self)
        self.update_scaled()
        super().showEvent(event)

    def eventFilter(self, watched, event):
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
