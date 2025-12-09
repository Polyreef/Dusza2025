from PySide6.QtWidgets import QLabel
from PySide6.QtGui import QPixmap
from PySide6.QtCore import Qt


class ClickableImageButton(QLabel):
    def __init__(self, normal_path, hover_path, parent=None, scale_factor: float = 0.60):
        super().__init__(parent)
        self.normal_pix_original = QPixmap(normal_path)
        self.hover_pix_original = QPixmap(hover_path)
        self.scale_factor = scale_factor
        self._callback = None

        self.setScaledContents(True)
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, False)
        self.update_scaled_pixmaps()

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

    def set_on_click(self, func):
        self._callback = func

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


class ClickableArrowButton(QLabel):
    def __init__(self, normal_path, hover_path, size=48, parent=None):
        super().__init__(parent)
        self.normal_pix = QPixmap(normal_path).scaled(
            size,
            size,
            Qt.AspectRatioMode.KeepAspectRatioByExpanding,
            Qt.TransformationMode.SmoothTransformation,
        )
        self.hover_pix = QPixmap(hover_path).scaled(
            size,
            size,
            Qt.AspectRatioMode.KeepAspectRatioByExpanding,
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
            window = self.window()
            if hasattr(window, "sound"):
                window.sound.play("click")
            self._callback()
