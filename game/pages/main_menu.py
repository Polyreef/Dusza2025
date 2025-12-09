from PySide6.QtWidgets import QVBoxLayout
from PySide6.QtCore import Qt

from game.widgets.background import BackgroundWidget
from game.widgets.buttons import ClickableImageButton


class MainMenuPage(BackgroundWidget):
    def __init__(self, game):
        super().__init__("Assets/Images/Backgrounds/Menu.png", game)
        self.game = game
        self._build_ui()

    def _build_ui(self):
        layout = self.get_container()
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        button_layout = QVBoxLayout()
        button_layout.setSpacing(10)
        button_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        new_btn = ClickableImageButton(
            "Assets/Images/Buttons/NewGameNormal.png",
            "Assets/Images/Buttons/NewGameHover.png",
        )
        new_btn.set_on_click(self.game.start_new_game_dialog)
        button_layout.addWidget(new_btn, alignment=Qt.AlignmentFlag.AlignCenter)

        load_btn = ClickableImageButton(
            "Assets/Images/Buttons/LoadNormal.png",
            "Assets/Images/Buttons/LoadHover.png",
        )
        load_btn.set_on_click(self.game.menu_load_game)
        button_layout.addWidget(load_btn, alignment=Qt.AlignmentFlag.AlignCenter)

        creator_btn = ClickableImageButton(
            "Assets/Images/Buttons/CreatorNormal.png",
            "Assets/Images/Buttons/CreatorHover.png",
        )
        creator_btn.set_on_click(self.game.open_creator_tool)
        button_layout.addWidget(creator_btn, alignment=Qt.AlignmentFlag.AlignCenter)

        quit_btn = ClickableImageButton(
            "Assets/Images/Buttons/QuitNormal.png",
            "Assets/Images/Buttons/QuitHover.png",
        )
        quit_btn.set_on_click(self.game.close)
        button_layout.addWidget(quit_btn, alignment=Qt.AlignmentFlag.AlignCenter)

        layout.addStretch(10)
        layout.addLayout(button_layout)
        layout.addStretch(1)
