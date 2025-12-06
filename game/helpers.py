from PySide6.QtWidgets import QMessageBox, QWidget

from core.battle import BattleResult
from core.models import Dungeon, Player, State, World


def ask_yes_no(parent: QWidget, title: str, text: str) -> bool:
    mb = QMessageBox(parent)
    mb.setWindowTitle(title)
    mb.setText(text)
    mb.setIcon(QMessageBox.Icon.Question)
    mb.setStandardButtons(
        QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
    )
    mb.setDefaultButton(QMessageBox.StandardButton.No)
    return mb.exec() == QMessageBox.StandardButton.Yes


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


def can_start_big_dungeon(world: World, player: Player) -> bool:
    for c in world.iter_simple_cards():
        if c.name not in player.collection:
            return True
    return False


def apply_battle_rewards(
    world: World, state: State, dungeon: Dungeon, result: BattleResult
) -> tuple[str, str]:
    player = state.player

    if result.outcome != "win":
        return ("A hős elbukott… most nincs jutalom.", "jatekos vesztett")

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
