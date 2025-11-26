import os

from typing import List

from core.battle import run_battle
from core.gamestate import GameState
from core.models import parse_element, parse_dungeon_type, parse_reward_type


def handle_world_command(current_game: GameState, command_parts: List[str]) -> None:
    """
    Világot módosító parancsok kezelése (uj kartya, uj vezer, uj kazamata).
    """

    command = command_parts[0]

    if command == "uj kartya":
        # uj kartya;Nev;sebzes;eletero;tipus
        card_name = command_parts[1]
        damage = int(command_parts[2])
        health = int(command_parts[3])
        element_text = parse_element(command_parts[4])
        current_game.world.add_simple_card(card_name, damage, health, element_text)

    elif command == "uj vezer":
        # uj vezer;UjNev;AlapKartyaNeve;sebzes/eletero
        new_leader_name = command_parts[1]
        base_card_name = command_parts[2]
        mode = command_parts[3]  # "sebzes" vagy "eletero"
        current_game.world.add_leader_from(new_leader_name, base_card_name, mode)

    elif command == "uj kazamata":
        dungeon_type = parse_dungeon_type(command_parts[1])
        dungeon_name = command_parts[2]

        if dungeon_type == "egyszeru":
            # uj kazamata;egyszeru;Nev;SimaKartya;sebzes/eletero
            simple_card_name = command_parts[3]
            reward_type = parse_reward_type(command_parts[4])
            current_game.world.add_dungeon(
                dungeon_name,
                dungeon_type,
                [simple_card_name],
                None,
                reward_type,
            )
        elif dungeon_type == "kis":
            # uj kazamata;kis;Nev;A,B,C;Vezer;sebzes/eletero
            simple_card_names = [
                name.strip() for name in command_parts[3].split(",") if name.strip()
            ]
            leader_name = command_parts[4]
            reward_type = parse_reward_type(command_parts[5])
            current_game.world.add_dungeon(
                dungeon_name,
                dungeon_type,
                simple_card_names,
                leader_name,
                reward_type,
            )
        else:
            # nagy: uj kazamata;nagy;Nev;A,B,C,D,E;Vezer
            simple_card_names = [
                name.strip() for name in command_parts[3].split(",") if name.strip()
            ]
            leader_name = command_parts[4]
            current_game.world.add_dungeon(
                dungeon_name,
                dungeon_type,
                simple_card_names,
                leader_name,
                None,
            )


def handle_player_command(current_game: GameState, command_parts: List[str]) -> None:
    """
    Játékos gyűjteményét vagy pakliját módosító parancsok.
    """

    command = command_parts[0]

    if command == "uj jatekos":
        current_game.player = current_game.player.__class__()  # új Player
    elif command == "felvetel gyujtemenybe":
        card_name = command_parts[1]
        current_game.add_collection_card_from_world(card_name)
    elif command == "uj pakli":
        if len(command_parts) < 2 or command_parts[1].strip() == "":
            current_game.player.deck = []
            return
        card_names = [
            name.strip() for name in command_parts[1].split(",") if name.strip()
        ]
        current_game.player.set_deck(card_names)


def handle_export_world(current_game: GameState, file_path: str) -> None:
    """
    Világ állapot exportálása az előírt text formátumban.
    """

    with open(file_path, "w", encoding="utf-8") as output_file:
        for name in current_game.world.simple_order:
            card = current_game.world.simple_cards[name]
            output_file.write(
                f"kartya;{card.name};{card.damage};{card.health};{card.element}\n"
            )

        output_file.write("\n")

        for name in current_game.world.leader_order:
            card = current_game.world.leaders[name]
            output_file.write(
                f"vezer;{card.name};{card.damage};{card.health};{card.element}\n"
            )

        output_file.write("\n")

        for name in current_game.world.dungeon_order:
            dungeon = current_game.world.dungeons[name]
            base_text = f"kazamata;{dungeon.dungeon_type};{dungeon.name};"

            if dungeon.dungeon_type == "egyszeru":
                base_text += f"{dungeon.simple_cards[0]};{dungeon.reward}"
            elif dungeon.dungeon_type == "kis":
                simple_text = ",".join(dungeon.simple_cards)
                base_text += f"{simple_text};{dungeon.leader_name};{dungeon.reward}"
            else:
                simple_text = ",".join(dungeon.simple_cards)
                base_text += f"{simple_text};{dungeon.leader_name}"

            output_file.write(base_text + "\n")


def handle_export_player(current_game: GameState, file_path: str) -> None:
    """
    Játékos állapot exportálása az előírt formátumban.
    """

    with open(file_path, "w", encoding="utf-8") as output_file:
        for name in current_game.player.collection_order:
            card = current_game.player.collection[name]
            output_file.write(
                f"gyujtemeny;{card.name};{card.damage};{card.health};{card.element}\n"
            )

        output_file.write("\n")

        for name in current_game.player.deck:
            output_file.write(f"pakli;{name}\n")


def handle_battle(current_game: GameState, dungeon_name: str, file_path: str) -> None:
    """
    Harc futtatása teszt módban, napló kiírása fájlba.
    """

    outcome = run_battle(current_game, dungeon_name, difficulty_level=0)
    with open(file_path, "w", encoding="utf-8") as output_file:
        for line in outcome.log_lines:
            output_file.write(line + "\n")


def run_test_mode(folder_path: str) -> None:
    """
    Teszt mód: az adott mappában lévő in.txt alapján futtatja a parancsokat.
    """

    current_game = GameState()
    input_path = os.path.join(folder_path, "in.txt")

    with open(input_path, "r", encoding="utf-8") as input_file:
        for raw_line in input_file:
            line = raw_line.strip()
            if not line:
                continue

            command_parts = [part.strip() for part in line.split(";")]
            command = command_parts[0]

            if command in ("uj kartya", "uj vezer", "uj kazamata"):
                handle_world_command(current_game, command_parts)
            elif command in ("uj jatekos", "felvetel gyujtemenybe", "uj pakli"):
                handle_player_command(current_game, command_parts)
            elif command == "export vilag":
                output_file_path = os.path.join(folder_path, command_parts[1])
                handle_export_world(current_game, output_file_path)
            elif command == "export jatekos":
                output_file_path = os.path.join(folder_path, command_parts[1])
                handle_export_player(current_game, output_file_path)
            elif command == "harc":
                dungeon_name = command_parts[1]
                output_file_path = os.path.join(folder_path, command_parts[2])
                handle_battle(current_game, dungeon_name, output_file_path)
            else:
                print(f"Ismeretlen parancs: {line}")
