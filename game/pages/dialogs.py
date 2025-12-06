from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QFileDialog,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
)

from core.storage import load_environment_from_file


class EnvironmentChooseDialog(QDialog):
    def __init__(self, parent, env_files):
        super().__init__(parent)
        self.setWindowTitle("Játékkörnyezet választása")
        self.selected = None

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
            env = load_environment_from_file(path)
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
        self.selected = None

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
        self.selected = path
        self.accept()

    def on_accept(self):
        if self.list_widget:
            item = self.list_widget.currentItem()
            if item:
                self.selected = item.data(Qt.ItemDataRole.UserRole)
        self.accept()
