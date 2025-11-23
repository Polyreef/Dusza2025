from __future__ import annotations

import os
import sys

from test import run_test_mode
from ui_master import master_menu
from ui_player import player_menu
from ui_common import clear_screen, press_enter
from default_environment import create_default_world_and_player
from environment import save_environment


def ensure_default_environment() -> None:
    """
    Gondoskodik róla, hogy legyen egy alap játékkörnyezet fájl az I. fordulós világgal.
    Ha már létezik, nem írja felül.
    """
    filename = "default.env.json"
    if os.path.isfile(filename):
        return

    env_name, world, player = create_default_world_and_player()
    save_environment(filename, env_name, world, player)


def run_game_mode() -> None:
    """
    Játék mód futtatása: főmenü (Játékos / Játékmester).
    """
    ensure_default_environment()

    while True:
        clear_screen()
        print("=== Damareen – Játék mód ===\n")
        print("1 – Játékos mód")
        print("2 – Játékmester mód")
        print("3 – Kilépés")
        choice = input("Választásod: ").strip()

        if choice == "1":
            player_menu()
        elif choice == "2":
            master_menu()
        elif choice == "3":
            print("Kilépés a programból.")
            break
        else:
            print("Ismeretlen menüpont.")
            press_enter()


def main() -> None:
    args = sys.argv[1:]
    if len(args) == 1 and args[0] == "--ui":
        run_game_mode()
    elif len(args) == 1:
        # teszt mód: paraméter = mappa, ahol az in.txt található
        base_dir = args[0]
        run_test_mode(base_dir)
    else:
        print("Használat:")
        print("  python main.py <mappautvonal>   # teszt mód (in.txt ebben a mappában)")
        print("  python main.py --ui             # játék mód")


if __name__ == "__main__":
    main()
