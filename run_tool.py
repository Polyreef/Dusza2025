from __future__ import annotations

import json

from typing import Optional

from PySide6.QtCore import Qt
from PySide6.QtGui import QAction
from PySide6.QtWidgets import (
    QApplication,
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFileDialog,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QSpinBox,
    QSplitter,
    QTabWidget,
    QTableWidget,
    QTableWidgetItem,
    QTextEdit,
    QToolBar,
    QVBoxLayout,
    QWidget,
)

from core import ELEMENT_ORDER
from core.battle import run_battle, BattleResult
from core.environment import Environment
from core.models import World, Player, State, Dungeon, CardDefinition
from core import storage as storage_module


def can_start_big_dungeon(world: World, player: Player) -> bool:
    """
    Nagy kazamata ellen csak akkor lehet harcolni, ha van még a világban olyan
    sima kártya, ami nincs a játékos gyűjteményében.
    """

    for c in world.iter_simple_cards():
        if c.name not in player.collection:
            return True
    return False


def apply_battle_rewards(
    world: World, state: State, dungeon: Dungeon, result: BattleResult
) -> tuple[str, str]:
    """
    Harc utáni jutalom feldolgozása.

    Visszatérés:
        user_message, log_last_line
    """

    player = state.player

    if result.outcome != "win":
        return ("A játékos vesztett - nincs jutalom.", "jatekos vesztett")

    # Egyszerű és kis kazamata: utolsó támadó lap sebzés / életerő bónuszt kap
    if dungeon.kind in ("egyszeru", "kis"):
        reward_type = dungeon.reward_type or "eletero"
        card_name = result.last_player_attacker_name
        if not card_name:
            return (
                "A játékos nyert, de az utolsó támadó lap nem ismert.",
                "jatekos nyert",
            )

        card = player.collection.get(card_name)
        if not card:
            return (
                f"A játékos nyert, de a(z) {card_name} lap nem található a gyűjteményben.",
                "jatekos nyert",
            )

        if reward_type == "sebzes":
            card.damage += 1
            msg = f"A játékos nyert; {card.name} +1 sebzést kapott."
            last_line = f"jatekos nyert;sebzes;{card.name}"
        else:
            # alapértelmezésként életerő
            card.health += 2
            msg = f"A játékos nyert; {card.name} +2 életerőt kapott."
            last_line = f"jatekos nyert;eletero;{card.name}"

        return msg, last_line

    # Nagy kazamata: első olyan sima világlap, ami még nincs a gyűjteményben
    if dungeon.kind == "nagy":
        for c in world.iter_simple_cards():
            if c.name not in player.collection:
                player.add_card_from_world(world, c.name)
                msg = f"A játékos nyert; új kártyát kapott: {c.name}."
                last_line = f"jatekos nyert;{c.name}"
                return msg, last_line

        # Elvileg nagy kazamata elé nem is engedjük a játékost ilyen esetben,
        # de legyünk hibatűrők.
        return (
            "A játékos nyert, de már nincs a világban új sima kártya jutalomként.",
            "jatekos nyert",
        )

    # Ismeretlen típus - ne omoljon össze az alkalmazás
    return ("A játékos nyert, de ismeretlen kazamata típus.", "jatekos nyert")


def ask_difficulty(parent: QWidget) -> Optional[int]:
    dlg = QDialog(parent)
    dlg.setWindowTitle("Nehézségi szint")
    layout = QVBoxLayout(dlg)

    form = QFormLayout()
    sb = QSpinBox()
    sb.setRange(0, 10)
    sb.setValue(0)
    form.addRow("Nehézségi szint (0-10):", sb)
    layout.addLayout(form)

    buttons = QDialogButtonBox(
        QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
    )
    layout.addWidget(buttons)

    def on_accept():
        dlg.accept()

    def on_reject():
        dlg.reject()

    buttons.accepted.connect(on_accept)
    buttons.rejected.connect(on_reject)

    if dlg.exec() == QDialog.DialogCode.Accepted:
        return int(sb.value())
    return None


def show_error(parent: QWidget, title: str, text: str):
    mb = QMessageBox(parent)
    mb.setIcon(QMessageBox.Icon.Critical)
    mb.setWindowTitle(title)
    mb.setText(text)
    mb.exec()


def show_info(parent: QWidget, title: str, text: str):
    mb = QMessageBox(parent)
    mb.setIcon(QMessageBox.Icon.Information)
    mb.setWindowTitle(title)
    mb.setText(text)
    mb.exec()


class GameMasterWidget(QWidget):
    """
    Játékmester szerepkör: világ + kezdő gyűjtemény szerkesztése,
    majd ezek mentése / betöltése játékkörnyezetként.
    """

    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)

        self.environment: Optional[Environment] = None
        self.world = World()
        self.starting_collection: dict[str, CardDefinition] = {}

        self._build_ui()

    def _build_ui(self):
        root = QVBoxLayout(self)

        # Felső eszköztár - név + mentés/betöltés
        top_layout = QHBoxLayout()
        top_layout.addWidget(QLabel("Környezet neve:"))
        self.env_name_edit = QLineEdit("Új környezet")
        top_layout.addWidget(self.env_name_edit)

        self.load_env_btn = QPushButton("Környezet betöltése…")
        self.save_env_btn = QPushButton("Környezet mentése…")
        top_layout.addWidget(self.load_env_btn)
        top_layout.addWidget(self.save_env_btn)

        root.addLayout(top_layout)

        splitter = QSplitter(Qt.Orientation.Vertical)
        root.addWidget(splitter, 1)

        # Világ szerkesztése
        world_tabs = QTabWidget()
        splitter.addWidget(world_tabs)

        self.simple_table = QTableWidget(0, 5)
        self.simple_table.setHorizontalHeaderLabels(
            ["Név", "Sebzés", "Életerő", "Típus", "Stílus"]
        )
        world_tabs.addTab(self.simple_table, "Sima kártyák")

        self.leader_table = QTableWidget(0, 5)
        self.leader_table.setHorizontalHeaderLabels(
            ["Név", "Sebzés", "Életerő", "Típus", "Stílus"]
        )
        world_tabs.addTab(self.leader_table, "Vezérkártyák")

        self.dungeon_table = QTableWidget(0, 5)
        self.dungeon_table.setHorizontalHeaderLabels(
            ["Név", "Típus", "Sima lapok", "Vezér", "Jutalom"]
        )
        world_tabs.addTab(self.dungeon_table, "Kazamaták")

        # Kezdő gyűjtemény
        starter_group = QGroupBox("Kezdő gyűjtemény (sima kártyák)")
        splitter.addWidget(starter_group)
        starter_layout = QVBoxLayout(starter_group)
        self.collection_list = QListWidget()
        self.collection_list.setSelectionMode(QListWidget.SelectionMode.MultiSelection)
        starter_layout.addWidget(self.collection_list)
        starter_info = QLabel(
            "Jelöld ki, hogy a világból mely sima kártyák kerüljenek a játékos "
            "kezdő gyűjteményébe."
        )
        starter_info.setWordWrap(True)
        starter_layout.addWidget(starter_info)

        # Alul: űrlapok az egyes entitások hozzáadásához
        forms_splitter = QSplitter(Qt.Orientation.Horizontal)
        root.addWidget(forms_splitter)

        forms_splitter.addWidget(self._build_simple_form())
        forms_splitter.addWidget(self._build_leader_form())
        forms_splitter.addWidget(self._build_dungeon_form())

        # Jelzések
        self.status_label = QLabel(
            "Nincs mentett játékkörnyezet. Hozz létre egyet vagy tölts be egyet."
        )
        root.addWidget(self.status_label)

        # Jelek
        self.load_env_btn.clicked.connect(self.on_load_env_clicked)
        self.save_env_btn.clicked.connect(self.on_save_env_clicked)
        self.collection_list.itemChanged.connect(self.on_collection_item_changed)

    def _build_simple_form(self) -> QWidget:
        w = QGroupBox("Új sima kártya")
        layout = QFormLayout(w)

        self.simple_name_edit = QLineEdit()
        self.simple_damage_spin = QSpinBox()
        self.simple_damage_spin.setRange(2, 100)
        self.simple_damage_spin.setValue(2)
        self.simple_health_spin = QSpinBox()
        self.simple_health_spin.setRange(1, 100)
        self.simple_health_spin.setValue(5)
        self.simple_element_combo = QComboBox()
        for e in ELEMENT_ORDER:
            self.simple_element_combo.addItem(e)
        self.simple_style_spin = QSpinBox()
        self.simple_style_spin.setRange(1, 4)
        self.simple_style_spin.setValue(1)

        layout.addRow("Név:", self.simple_name_edit)
        layout.addRow("Sebzés:", self.simple_damage_spin)
        layout.addRow("Életerő:", self.simple_health_spin)
        layout.addRow("Típus:", self.simple_element_combo)
        layout.addRow("Stílus (1-4):", self.simple_style_spin)

        btn = QPushButton("Hozzáadás")
        layout.addRow(btn)
        btn.clicked.connect(self.on_add_simple_card)

        return w

    def _build_leader_form(self) -> QWidget:
        w = QGroupBox("Új vezérkártya")
        layout = QFormLayout(w)

        self.leader_name_edit = QLineEdit()
        self.leader_base_combo = QComboBox()
        self.leader_mode_combo = QComboBox()
        self.leader_mode_combo.addItem("Sebzés duplázás", "sebzes")
        self.leader_mode_combo.addItem("Életerő duplázás", "eletero")
        self.leader_style_spin = QSpinBox()
        self.leader_style_spin.setRange(1, 2)
        self.leader_style_spin.setValue(1)

        layout.addRow("Név:", self.leader_name_edit)
        layout.addRow("Alap sima kártya:", self.leader_base_combo)
        layout.addRow("Mód:", self.leader_mode_combo)
        layout.addRow("Stílus (1-2):", self.leader_style_spin)

        btn = QPushButton("Hozzáadás")
        layout.addRow(btn)
        btn.clicked.connect(self.on_add_leader_card)

        return w

    def _build_dungeon_form(self) -> QWidget:
        w = QGroupBox("Új kazamata")
        layout = QVBoxLayout(w)

        form = QFormLayout()
        self.dun_name_edit = QLineEdit()
        self.dun_kind_combo = QComboBox()
        self.dun_kind_combo.addItem("Egyszerű találkozás", "egyszeru")
        self.dun_kind_combo.addItem("Kis kazamata", "kis")
        self.dun_kind_combo.addItem("Nagy kazamata", "nagy")

        self.dun_simple_list = QListWidget()
        self.dun_simple_list.setSelectionMode(QListWidget.SelectionMode.MultiSelection)

        self.dun_leader_combo = QComboBox()
        self.dun_reward_combo = QComboBox()
        self.dun_reward_combo.addItem("Sebzés bónusz (+1)", "sebzes")
        self.dun_reward_combo.addItem("Életerő bónusz (+2)", "eletero")

        form.addRow("Név:", self.dun_name_edit)
        form.addRow("Típus:", self.dun_kind_combo)
        layout.addLayout(form)
        layout.addWidget(
            QLabel("Sima kártyák (tartsd lenyomva a Ctrl-t több kijelöléshez):")
        )
        layout.addWidget(self.dun_simple_list)
        form2 = QFormLayout()
        form2.addRow("Vezérkártya:", self.dun_leader_combo)
        form2.addRow("Jutalom típusa:", self.dun_reward_combo)
        layout.addLayout(form2)

        btn = QPushButton("Kazamata hozzáadása")
        layout.addWidget(btn)

        # Jelzések
        btn.clicked.connect(self.on_add_dungeon)
        self.dun_kind_combo.currentIndexChanged.connect(self.on_dungeon_kind_changed)

        return w

    def _rebuild_all_views(self):
        # Sima kártyák táblája + kezdő gyűjtemény + dungeon form listája
        self.simple_table.setRowCount(0)
        self.collection_list.blockSignals(True)
        self.collection_list.clear()
        self.dun_simple_list.clear()

        for card in self.world.iter_simple_cards():
            self._append_simple_row(card)

            # Kezdő gyűjtemény lista
            item = QListWidgetItem(
                f"{card.name} - {card.damage}/{card.health} {card.element}"
            )
            item.setFlags(
                item.flags()
                | Qt.ItemFlag.ItemIsUserCheckable
                | Qt.ItemFlag.ItemIsSelectable
            )
            checked = (
                Qt.CheckState.Checked
                if card.name in self.starting_collection
                else Qt.CheckState.Unchecked
            )
            item.setCheckState(checked)
            item.setData(Qt.ItemDataRole.UserRole, card.name)
            self.collection_list.addItem(item)

            # Dungeon form - sima lap lista
            dun_item = QListWidgetItem(
                f"{card.name} - {card.damage}/{card.health} {card.element}"
            )
            dun_item.setData(Qt.ItemDataRole.UserRole, card.name)
            self.dun_simple_list.addItem(dun_item)

        self.collection_list.blockSignals(False)

        # Vezérkártya táblázat + dungeon form vezércombo
        self.leader_table.setRowCount(0)
        self.dun_leader_combo.clear()
        for leader in self.world.iter_leader_cards():
            self._append_leader_row(leader)
            self.dun_leader_combo.addItem(leader.name, leader.name)

        # Kazamaták táblázata
        self.dungeon_table.setRowCount(0)
        for dungeon in self.world.iter_dungeons():
            self._append_dungeon_row(dungeon)

        self._update_status_label()

        # Leader form - alap sima kártyák combo
        self.leader_base_combo.clear()
        for c in self.world.iter_simple_cards():
            self.leader_base_combo.addItem(c.name, c.name)

    def _append_simple_row(self, card: CardDefinition):
        row = self.simple_table.rowCount()
        self.simple_table.insertRow(row)
        self.simple_table.setItem(row, 0, QTableWidgetItem(card.name))
        self.simple_table.setItem(row, 1, QTableWidgetItem(str(card.damage)))
        self.simple_table.setItem(row, 2, QTableWidgetItem(str(card.health)))
        self.simple_table.setItem(row, 3, QTableWidgetItem(card.element))
        style = getattr(self.world, "simple_styles", {}).get(card.name, 1)
        self.simple_table.setItem(row, 4, QTableWidgetItem(str(style)))

    def _append_leader_row(self, card: CardDefinition):
        row = self.leader_table.rowCount()
        self.leader_table.insertRow(row)
        self.leader_table.setItem(row, 0, QTableWidgetItem(card.name))
        self.leader_table.setItem(row, 1, QTableWidgetItem(str(card.damage)))
        self.leader_table.setItem(row, 2, QTableWidgetItem(str(card.health)))
        self.leader_table.setItem(row, 3, QTableWidgetItem(card.element))
        style = getattr(self.world, "leader_styles", {}).get(card.name, 1)
        self.leader_table.setItem(row, 4, QTableWidgetItem(str(style)))

    def _append_dungeon_row(self, dungeon: Dungeon):
        row = self.dungeon_table.rowCount()
        self.dungeon_table.insertRow(row)
        self.dungeon_table.setItem(row, 0, QTableWidgetItem(dungeon.name))
        self.dungeon_table.setItem(row, 1, QTableWidgetItem(dungeon.kind))
        self.dungeon_table.setItem(
            row, 2, QTableWidgetItem(",".join(dungeon.simple_card_names))
        )
        self.dungeon_table.setItem(row, 3, QTableWidgetItem(dungeon.leader_name or "-"))
        self.dungeon_table.setItem(row, 4, QTableWidgetItem(dungeon.reward_type or "-"))

    def _update_status_label(self):
        name = self.environment.name if self.environment else self.env_name_edit.text()
        num_simple = len(list(self.world.iter_simple_cards()))
        num_leader = len(list(self.world.iter_leader_cards()))
        num_dun = len(list(self.world.iter_dungeons()))
        num_start = len(self.starting_collection)
        self.status_label.setText(
            f"Környezet: {name} - {num_simple} sima, {num_leader} vezér, "
            f"{num_dun} kazamata, {num_start} kezdő kártya a gyűjteményben."
        )

    def on_collection_item_changed(self, item: QListWidgetItem):
        name = item.data(Qt.ItemDataRole.UserRole)
        if item.checkState() == Qt.CheckState.Checked:
            card = self.world.get_simple_card(name)
            if card:
                self.starting_collection[name] = card
        else:
            self.starting_collection.pop(name, None)
        self._update_status_label()

    def on_add_simple_card(self):
        name = self.simple_name_edit.text().strip()
        if not name:
            show_error(self, "Hiba", "A kártya neve nem lehet üres.")
            return

        damage = int(self.simple_damage_spin.value())
        health = int(self.simple_health_spin.value())
        element = (
            self.simple_element_combo.currentData()
            or self.simple_element_combo.currentText()
        )
        style = int(self.simple_style_spin.value())

        ok = self.world.add_simple_card(name, damage, health, element, style)
        if not ok:
            show_error(
                self,
                "Hiba",
                "A kártya nem hozható létre. Ellenőrizd a megadott értékeket (név egyediség, tartományok).",
            )
            return

        card = self.world.get_simple_card(name)
        if card:
            self._append_simple_row(card)
        self._rebuild_all_views()
        self.simple_name_edit.clear()

    def on_add_leader_card(self):
        name = self.leader_name_edit.text().strip()
        if not name:
            show_error(self, "Hiba", "A vezérkártya neve nem lehet üres.")
            return

        base_name = self.leader_base_combo.currentData()
        if not base_name:
            show_error(self, "Hiba", "Először hozz létre legalább egy sima kártyát.")
            return

        mode = self.leader_mode_combo.currentData()
        style = int(self.leader_style_spin.value())

        ok = self.world.add_leader_card(name, base_name, mode, style)
        if not ok:
            show_error(
                self,
                "Hiba",
                "A vezérkártya nem hozható létre. Ellenőrizd a megadott értékeket.",
            )
            return

        leader = self.world.get_leader_card(name)
        if leader:
            self._append_leader_row(leader)
        self._rebuild_all_views()
        self.leader_name_edit.clear()

    def on_dungeon_kind_changed(self, index: int):
        kind = self.dun_kind_combo.currentData()
        if kind == "nagy":
            self.dun_reward_combo.setEnabled(False)
            self.dun_leader_combo.setEnabled(True)
        elif kind == "egyszeru":
            self.dun_reward_combo.setEnabled(True)
            self.dun_leader_combo.setEnabled(False)
        else:  # kis
            self.dun_reward_combo.setEnabled(True)
            self.dun_leader_combo.setEnabled(True)

    def on_add_dungeon(self):
        name = self.dun_name_edit.text().strip()
        if not name:
            show_error(self, "Hiba", "A kazamata neve nem lehet üres.")
            return

        kind = self.dun_kind_combo.currentData()
        simple_items = self.dun_simple_list.selectedItems()
        simple_names = [i.data(Qt.ItemDataRole.UserRole) for i in simple_items]

        required = {"egyszeru": 1, "kis": 3, "nagy": 5}.get(kind, 1)
        if len(simple_names) != required:
            show_error(
                self,
                "Hiba",
                f"{kind.capitalize()} kazamatához pontosan {required} sima kártyát kell kiválasztani.",
            )
            return

        leader_name: Optional[str] = None
        reward_type: Optional[str] = None

        if kind in ("kis", "nagy"):
            leader_name = self.dun_leader_combo.currentData()
            if not leader_name:
                show_error(
                    self,
                    "Hiba",
                    "Kis és nagy kazamatához ki kell választani egy vezérkártyát.",
                )
                return

        if kind in ("egyszeru", "kis"):
            reward_type = self.dun_reward_combo.currentData()
        else:
            reward_type = None

        dungeon = Dungeon(name, kind, simple_names, leader_name, reward_type)
        ok = self.world.add_dungeon(dungeon)
        if not ok:
            show_error(
                self, "Hiba", "Nem sikerült hozzáadni a kazamatát (névütközés?)."
            )
            return

        self._append_dungeon_row(dungeon)
        self._update_status_label()
        self.dun_name_edit.clear()

    # Környezet mentés / betöltés

    def on_save_env_clicked(self):
        name = self.env_name_edit.text().strip() or "Névtelen környezet"
        self.environment = Environment(name, self.world, self.starting_collection)

        path_str, _ = QFileDialog.getSaveFileName(
            self,
            "Környezet mentése",
            f"{name}.json",
            "Damareen környezet (*.json)",
        )
        if not path_str:
            return

        try:
            storage_module.save_environment_to_file(self.environment, path_str)
        except Exception as e:  # pragma: no cover - hibaüzenet
            show_error(self, "Hiba", f"A környezet mentése nem sikerült:\n{e}")
            return

        self._update_status_label()
        show_info(self, "Mentve", "A játékkörnyezet sikeresen elmentve.")

    def on_load_env_clicked(self):
        path_str, _ = QFileDialog.getOpenFileName(
            self,
            "Környezet betöltése",
            "",
            "Damareen környezet (*.json)",
        )
        if not path_str:
            return

        try:
            env = storage_module.load_environment_from_file(path_str)
        except Exception as e:  # pragma: no cover
            show_error(self, "Hiba", f"A környezet betöltése nem sikerült:\n{e}")
            return

        self.environment = env
        self.world = env.world
        self.starting_collection = dict(env.starting_collection)
        self.env_name_edit.setText(env.name)
        self._rebuild_all_views()
        show_info(self, "Betöltve", f"Környezet betöltve: {env.name}")

    # Külső használathoz

    def get_environment(self) -> Optional[Environment]:
        """
        A legfrissebb Environment példány lekérdezése.

        Ha még nem volt lementve, akkor az aktuális world + starting_collection
        alapján készítünk egy ideiglenes példányt.
        """

        if self.environment is None:
            name = self.env_name_edit.text().strip() or "Ideiglenes környezet"
            self.environment = Environment(name, self.world, self.starting_collection)
        return self.environment


# Játékos nézet


class PlayerWidget(QWidget):
    """
    Játékos szerepkör - pakliépítés, kazamata választás, harcok, játékmentés.
    """

    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)

        self.environment: Optional[Environment] = None
        self.state: Optional[State] = None

        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)

        # Felső sor - környezet + játék betöltése / mentése
        top = QHBoxLayout()
        self.env_label = QLabel("Nincs betöltött környezet.")
        top.addWidget(self.env_label, 1)

        self.load_env_btn = QPushButton("Környezet betöltése…")
        self.new_game_btn = QPushButton("Új játék…")
        self.load_game_btn = QPushButton("Játék betöltése…")
        self.save_game_btn = QPushButton("Játék mentése…")

        top.addWidget(self.load_env_btn)
        top.addWidget(self.new_game_btn)
        top.addWidget(self.load_game_btn)
        top.addWidget(self.save_game_btn)

        layout.addLayout(top)

        # Középső rész - pakliépítés + kazamaták
        middle_splitter = QSplitter(Qt.Orientation.Horizontal)
        layout.addWidget(middle_splitter, 1)

        # Gyűjtemény + pakli
        deck_group = QGroupBox("Gyűjtemény és pakli")
        middle_splitter.addWidget(deck_group)
        deck_layout = QVBoxLayout(deck_group)

        lists_layout = QHBoxLayout()
        deck_layout.addLayout(lists_layout)

        self.collection_list = QListWidget()
        self.collection_list.setSelectionMode(QListWidget.SelectionMode.MultiSelection)
        lists_layout.addWidget(self.collection_list)

        buttons_col = QVBoxLayout()
        lists_layout.addLayout(buttons_col)
        self.add_to_deck_btn = QPushButton("→ Hozzáadás a paklihoz")
        self.remove_from_deck_btn = QPushButton("← Eltávolítás a pakliból")
        self.move_up_btn = QPushButton("Feljebb")
        self.move_down_btn = QPushButton("Lejjebb")
        buttons_col.addWidget(self.add_to_deck_btn)
        buttons_col.addWidget(self.remove_from_deck_btn)
        buttons_col.addWidget(self.move_up_btn)
        buttons_col.addWidget(self.move_down_btn)
        buttons_col.addStretch(1)

        self.deck_list = QListWidget()
        self.deck_list.setSelectionMode(QListWidget.SelectionMode.SingleSelection)
        lists_layout.addWidget(self.deck_list)

        self.save_deck_btn = QPushButton("Pakli frissítése")
        deck_layout.addWidget(self.save_deck_btn)

        self.deck_info_label = QLabel("Nincs aktív játékos állapot.")
        deck_layout.addWidget(self.deck_info_label)

        # Kazamaták
        dungeon_group = QGroupBox("Kazamaták")
        middle_splitter.addWidget(dungeon_group)
        dun_layout = QVBoxLayout(dungeon_group)

        self.dungeon_table = QTableWidget(0, 3)
        self.dungeon_table.setHorizontalHeaderLabels(["Név", "Típus", "Nyeremény"])
        self.dungeon_table.setSelectionBehavior(
            QTableWidget.SelectionBehavior.SelectRows
        )
        self.dungeon_table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        self.dungeon_table.horizontalHeader().setStretchLastSection(True)
        dun_layout.addWidget(self.dungeon_table)

        self.start_battle_btn = QPushButton("Harc indítása")
        dun_layout.addWidget(self.start_battle_btn)

        self.dungeon_info_label = QLabel("")
        self.dungeon_info_label.setWordWrap(True)
        dun_layout.addWidget(self.dungeon_info_label)

        # Alsó rész - harcnapló
        battle_group = QGroupBox("Harc naplója")
        layout.addWidget(battle_group, 1)
        battle_layout = QVBoxLayout(battle_group)
        self.battle_log_edit = QTextEdit()
        self.battle_log_edit.setReadOnly(True)
        battle_layout.addWidget(self.battle_log_edit)

        self.status_label = QLabel("Nincs aktív játék.")
        layout.addWidget(self.status_label)

        # Jelek
        self.load_env_btn.clicked.connect(self.on_load_env_clicked)
        self.new_game_btn.clicked.connect(self.on_new_game_clicked)
        self.load_game_btn.clicked.connect(self.on_load_game_clicked)
        self.save_game_btn.clicked.connect(self.on_save_game_clicked)

        self.add_to_deck_btn.clicked.connect(self.on_add_to_deck)
        self.remove_from_deck_btn.clicked.connect(self.on_remove_from_deck)
        self.move_up_btn.clicked.connect(lambda: self.on_move_deck_item(-1))
        self.move_down_btn.clicked.connect(lambda: self.on_move_deck_item(1))
        self.save_deck_btn.clicked.connect(self.on_save_deck_clicked)

        self.start_battle_btn.clicked.connect(self.on_start_battle_clicked)

        self._update_buttons_enabled()

    def _update_buttons_enabled(self):
        has_env = self.environment is not None
        has_state = self.state is not None

        self.new_game_btn.setEnabled(has_env)
        self.save_game_btn.setEnabled(has_state)
        self.load_game_btn.setEnabled(True)

        self.add_to_deck_btn.setEnabled(has_state)
        self.remove_from_deck_btn.setEnabled(has_state)
        self.move_up_btn.setEnabled(has_state)
        self.move_down_btn.setEnabled(has_state)
        self.save_deck_btn.setEnabled(has_state)
        self.start_battle_btn.setEnabled(has_state and has_env)

    def _update_status_labels(self):
        if not self.state:
            self.status_label.setText("Nincs aktív játék.")
            self.deck_info_label.setText("")
            return

        player = self.state.player
        max_size = player.max_deck_size()
        deck_len = len(player.deck)
        self.deck_info_label.setText(
            f"Gyűjtemény: {len(player.collection)} kártya. "
            f"Pakli: {deck_len}/{max_size} lap. "
            f"Nehézség: {self.state.difficulty}."
        )
        self.status_label.setText(
            "Válassz kazamatát és indíts harcot, vagy állíts össze új paklit."
        )

        if self.environment:
            self.env_label.setText(f"Környezet: {self.environment.name} - aktív játék.")

        # Nagy kazamata infó
        if self.environment and self.state:
            if not can_start_big_dungeon(self.environment.world, self.state.player):
                self.dungeon_info_label.setText(
                    "Figyelem: jelenleg nem indítható nagy kazamata, mert a világ összes "
                    "sima kártyája megtalálható a gyűjteményben."
                )
            else:
                self.dungeon_info_label.setText(
                    "Nagy kazamata esetén a jutalom egy új sima kártya a világból."
                )

    def _rebuild_collection_and_deck_views(self):
        self.collection_list.clear()
        self.deck_list.clear()

        if not self.state:
            self._update_status_labels()
            return

        player = self.state.player

        # Gyűjtemény
        for card in player.collection.values():
            item = QListWidgetItem(
                f"{card.name} - {card.damage}/{card.health} {card.element}"
            )
            item.setData(Qt.ItemDataRole.UserRole, card.name)
            self.collection_list.addItem(item)

        # Pakli
        for name in player.deck:
            card = player.collection.get(name)
            if not card:
                continue
            item = QListWidgetItem(
                f"{card.name} - {card.damage}/{card.health} {card.element}"
            )
            item.setData(Qt.ItemDataRole.UserRole, card.name)
            self.deck_list.addItem(item)

        self._update_status_labels()

    def _rebuild_dungeon_table(self):
        self.dungeon_table.setRowCount(0)
        if not self.environment:
            return

        world = self.environment.world
        for dungeon in world.iter_dungeons():
            row = self.dungeon_table.rowCount()
            self.dungeon_table.insertRow(row)
            self.dungeon_table.setItem(row, 0, QTableWidgetItem(dungeon.name))
            self.dungeon_table.setItem(row, 1, QTableWidgetItem(dungeon.kind))

            if dungeon.kind == "nagy":
                reward = "Új sima kártya a világból"
            else:
                reward = (
                    "Sebzés +1" if dungeon.reward_type == "sebzes" else "Életerő +2"
                )
            self.dungeon_table.setItem(row, 2, QTableWidgetItem(reward))

        self.dungeon_table.resizeColumnsToContents()

    def _get_selected_dungeon(self) -> Optional[Dungeon]:
        if not self.environment:
            return None
        sel = self.dungeon_table.selectedItems()
        if not sel:
            return None
        row = sel[0].row()
        name_item = self.dungeon_table.item(row, 0)
        if not name_item:
            return None
        name = name_item.text()
        return self.environment.world.get_dungeon(name)

    def _current_deck_names_from_view(self) -> list[str]:
        names: list[str] = []
        for i in range(self.deck_list.count()):
            item = self.deck_list.item(i)
            names.append(item.data(Qt.ItemDataRole.UserRole))
        return names

    def on_load_env_clicked(self):
        path_str, _ = QFileDialog.getOpenFileName(
            self,
            "Környezet betöltése",
            "",
            "Damareen környezet (*.json)",
        )
        if not path_str:
            return

        try:
            env = storage_module.load_environment_from_file(path_str)
        except Exception as e:  # pragma: no cover
            show_error(self, "Hiba", f"A környezet betöltése nem sikerült:\n{e}")
            return

        self.environment = env
        self.env_label.setText(f"Környezet: {env.name} - nincs aktív játék.")
        self._rebuild_dungeon_table()
        self.state = None
        self.collection_list.clear()
        self.deck_list.clear()
        self.battle_log_edit.clear()
        self._update_buttons_enabled()
        self._update_status_labels()

    def on_new_game_clicked(self):
        if not self.environment:
            show_error(
                self, "Hiba", "Előbb tölts be vagy hozz létre egy játékkörnyezetet."
            )
            return

        difficulty = ask_difficulty(self)
        if difficulty is None:
            return

        self.state = self.environment.new_game(difficulty)
        self.battle_log_edit.clear()
        self._rebuild_collection_and_deck_views()
        self._update_buttons_enabled()

    def on_load_game_clicked(self):
        path_str, _ = QFileDialog.getOpenFileName(
            self,
            "Játék betöltése",
            "",
            "Damareen mentés (*.json)",
        )
        if not path_str:
            return

        try:
            with open(path_str, "r", encoding="utf-8") as f:
                data = json.load(f)
        except Exception as e:  # pragma: no cover
            show_error(self, "Hiba", f"A mentés betöltése nem sikerült:\n{e}")
            return

        try:
            env_data = data["environment"]
            state_data = data["state"]
            self.environment = storage_module.environment_from_dict(env_data)
            self.state = storage_module.state_from_dict(state_data)
        except Exception as e:  # pragma: no cover
            show_error(self, "Hiba", f"A mentés formátuma hibás:\n{e}")
            return

        self.env_label.setText(f"Környezet: {self.environment.name} - aktív játék.")
        self._rebuild_dungeon_table()
        self._rebuild_collection_and_deck_views()
        self.battle_log_edit.clear()
        self._update_buttons_enabled()

    def on_save_game_clicked(self):
        if not (self.environment and self.state):
            show_error(self, "Hiba", "Nincs aktív játék, amit menteni lehetne.")
            return

        path_str, _ = QFileDialog.getSaveFileName(
            self,
            "Játék mentése",
            "damareen_save.json",
            "Damareen mentés (*.json)",
        )
        if not path_str:
            return

        data = {
            "environment": storage_module.environment_to_dict(self.environment),
            "state": storage_module.state_to_dict(self.state),
        }

        try:
            with open(path_str, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception as e:  # pragma: no cover
            show_error(self, "Hiba", f"A játék mentése nem sikerült:\n{e}")
            return

        show_info(self, "Mentve", "A játékállapot sikeresen elmentve.")

    # Pakliépítés

    def on_add_to_deck(self):
        if not self.state:
            return
        for item in self.collection_list.selectedItems():
            name = item.data(Qt.ItemDataRole.UserRole)
            # ne legyen duplikátum
            for i in range(self.deck_list.count()):
                if self.deck_list.item(i).data(Qt.ItemDataRole.UserRole) == name:
                    break
            else:
                # új elem
                new_item = QListWidgetItem(item.text())
                new_item.setData(Qt.ItemDataRole.UserRole, name)
                self.deck_list.addItem(new_item)

    def on_remove_from_deck(self):
        row = self.deck_list.currentRow()
        if row >= 0:
            self.deck_list.takeItem(row)

    def on_move_deck_item(self, direction: int):
        row = self.deck_list.currentRow()
        if row < 0:
            return
        new_row = row + direction
        if new_row < 0 or new_row >= self.deck_list.count():
            return
        item = self.deck_list.takeItem(row)
        self.deck_list.insertItem(new_row, item)
        self.deck_list.setCurrentRow(new_row)

    def on_save_deck_clicked(self):
        if not self.state:
            return

        names = self._current_deck_names_from_view()
        ok = self.state.player.set_deck(names)
        if not ok:
            show_error(
                self,
                "Hiba",
                "A pakli nem érvényes. Legalább egy, a gyűjteményben szereplő kártyát kell tartalmazzon, "
                "és legfeljebb a gyűjtemény felét (felfelé kerekítve).",
            )
            return

        self._rebuild_collection_and_deck_views()
        show_info(self, "Pakli frissítve", "A pakli beállítása sikeres.")

    # Harc

    def on_start_battle_clicked(self):
        if not (self.environment and self.state):
            show_error(self, "Hiba", "Nincs aktív környezet vagy játék.")
            return

        if not self.state.player.has_deck():
            show_error(
                self, "Hiba", "Előbb állíts össze és ments el egy érvényes paklit."
            )
            return

        dungeon = self._get_selected_dungeon()
        if not dungeon:
            show_error(self, "Hiba", "Válassz ki egy kazamatát a listából.")
            return

        # Nagy kazamata indításának ellenőrzése
        if dungeon.kind == "nagy" and not can_start_big_dungeon(
            self.environment.world, self.state.player
        ):
            show_error(
                self,
                "Hiba",
                "Már minden sima világkártya szerepel a gyűjteményben, ezért nagy kazamata "
                "ellen nem indítható harc.",
            )
            return

        result = run_battle(
            self.environment.world,
            self.state.player,
            dungeon,
            difficulty=self.state.difficulty,
        )
        if not result:
            show_error(
                self, "Hiba", "A harc nem indítható (hibás pakli vagy kazamata)."
            )
            return

        # Harcnapló megjelenítése
        log_lines = list(result.log_lines)
        # Jutalom alkalmazása
        user_msg, last_log_line = apply_battle_rewards(
            self.environment.world, self.state, dungeon, result
        )
        log_lines.append(last_log_line)

        self.battle_log_edit.clear()
        self.battle_log_edit.setPlainText("\n".join(log_lines))

        # Gyűjtemény frissítése a jutalom alapján
        self._rebuild_collection_and_deck_views()
        self._update_buttons_enabled()

        show_info(
            self,
            "Harc vége",
            user_msg,
        )


# Főablak


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Damareen - Professzionális mód")

        self.tabs = QTabWidget()
        self.gm_widget = GameMasterWidget()
        self.player_widget = PlayerWidget()

        self.tabs.addTab(self.player_widget, "Játékos")
        self.tabs.addTab(self.gm_widget, "Játékmester")

        self.setCentralWidget(self.tabs)

        self._build_menus_and_toolbar()
        self.resize(800, 600)

    def _build_menus_and_toolbar(self):
        # Főmenü
        menubar = self.menuBar()
        file_menu = menubar.addMenu("&Fájl")

        exit_action = QAction("Kilépés", self)
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)

        help_menu = menubar.addMenu("&Súgó")
        about_action = QAction("Névjegy", self)
        help_menu.addAction(about_action)

        def on_about():
            QMessageBox.information(
                self,
                "Damareen - Névjegy",
                "Damareen - Lords of the Strings - 2025\n"
                "PySide6 alapú felhasználói felület.\n\n",
            )

        about_action.triggered.connect(on_about)


def run_tool_mode():
    app = QApplication([])
    window = MainWindow()
    window.show()
    app.exec()
