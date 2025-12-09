from __future__ import annotations

import json, os
from typing import Optional

from PySide6.QtWidgets import (
    QApplication,
    QDialog,
    QMainWindow,
    QStackedWidget,
    QFileDialog,
    QInputDialog,
    QMessageBox,
)
from PySide6.QtGui import QAction

from core.environment import Environment
from core.models import State, Dungeon
from core.battle import run_battle, BattleResult

from core.storage import (
    environment_from_dict,
    environment_to_dict,
    load_environment_from_file,
    state_from_dict,
    state_to_dict,
)
from game.sound import SoundManager
from game.helpers import (
    apply_battle_rewards,
    can_start_big_dungeon,
    show_error,
    show_info,
)
from game.pages.main_menu import MainMenuPage
from game.pages.library import WorldLibraryPage, WorldCardsPage, CollectionPage
from game.pages.deck_builder import DeckBuilderPage
from game.pages.map_page import MapPage
from game.pages.battle import BattleAnimationPage
from game.pages.outcome import VictoryLosePage
from game.pages.dialogs import (
    EnvironmentChooseDialog,
    StateChooseDialog,
)


class DamareenGameWindow(QMainWindow):
    def __init__(self, working_dir: str):
        super().__init__()

        self.working_dir = working_dir

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

        for page in (
            self.main_menu,
            self.library_page,
            self.world_cards_page,
            self.collection_page,
            self.deck_page,
            self.map_page,
            self.battle_animation_page,
            self.victory_lose_page,
        ):
            self.stack.addWidget(page)

        self._build_menu_bar()

        self.sound = SoundManager()
        self._load_sounds()

        self.sound.play("ambience")

    def _load_sounds(self):
        SOUNDS = {
            "ambience": ("Assets/Sounds/ambience.wav", 0.8, True),
            "arrow": ("Assets/Sounds/arrow.wav", 0.8, False),
            "click": ("Assets/Sounds/click.wav", 0.8, False),
            "door": ("Assets/Sounds/door.wav", 0.8, False),
            "shuffle": ("Assets/Sounds/shuffle.wav", 0.8, False),
            "stapling": ("Assets/Sounds/stapling.wav", 0.8, False),
            "strike": ("Assets/Sounds/strike.wav", 0.8, False),
            "sword": ("Assets/Sounds/sword.wav", 0.8, False),
            "throw": ("Assets/Sounds/throw.wav", 0.8, False),
            "trumpets": ("Assets/Sounds/trumpets.wav", 0.8, False),
            "whoosh": ("Assets/Sounds/whoosh.wav", 0.8, False),
            "wind": ("Assets/Sounds/wind.wav", 0.8, False),
        }

        for name, (path, volume, loop) in SOUNDS.items():
            self.sound.load(name, self.working_dir + path, volume, loop)

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
                "Damareen - Lords of the Strings - 2025\n"
                "PySide6 alapú felhasználói felület.\n\n",
            )

        about_action.triggered.connect(on_about)
        help_menu.addAction(about_action)

    def show_main_menu(self):
        self.stack.setCurrentWidget(self.main_menu)

    def open_creator_tool(self):
        from run_tool import MainWindow as ToolMainWindow

        self.tool_window = ToolMainWindow(self.working_dir)
        self.tool_window.show()

    def show_library_page(self):
        if not (self.environment and self.state):
            show_error(self, "Hiba", "Előbb indíts vagy tölts be egy játékot.")
            return
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
        env_dir = self.working_dir + "Environments"
        env_files = []

        if os.path.isdir(env_dir):
            for fname in os.listdir(env_dir):
                if fname.endswith(".json"):
                    path = os.path.join(env_dir, fname)
                    try:
                        env = load_environment_from_file(path)
                        env_files.append((env.name, path, env))
                    except:
                        pass

        dlg = EnvironmentChooseDialog(self, env_files)
        if dlg.exec() != QDialog.DialogCode.Accepted or not dlg.selected:
            return

        chosen_name, chosen_path, chosen_env = dlg.selected

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

    def start_new_game(self, environment: Environment, difficulty: int):
        self.environment = environment
        self.state = environment.new_game(difficulty)

        self.deck_page.refresh_from_state()

        self.show_library_page()

    def menu_load_game(self):
        state_dir = self.working_dir + "States"
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
            env = environment_from_dict(env_data)
            state = state_from_dict(state_data)
        except Exception as e:
            show_error(self, "Hiba", f"A mentés formátuma hibás:\n{e}")
            return

        self.environment = env
        self.state = state

        self.deck_page.refresh_from_state()

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
            "environment": environment_to_dict(self.environment),
            "state": state_to_dict(self.state),
        }
        try:
            with open(path, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            show_error(self, "Hiba", f"A mentés írása nem sikerült:\n{e}")
            return
        show_info(self, "Mentve", "A játékállapot sikeresen elmentve.")

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

        self.deck_page.refresh_from_state()
        self.map_page.refresh_from_environment()

        self.battle_animation_page.start_battle(dungeon, result, reward_msg)
        self.show_battle_animation_page()


def run_game_mode(working_dir: str):
    app = QApplication([])
    window = DamareenGameWindow(working_dir)
    window.show()
    app.exec()
