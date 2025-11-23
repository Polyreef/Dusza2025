from __future__ import annotations

import os
from math import ceil
from typing import Tuple

from world import World
from dungeon import Dungeon
from player import PlayerState
from card import CARD_TYPES
from environment import save_environment
from ui_common import clear_screen, press_enter, input_int, choose_from_list


def create_environment_interactive() -> Tuple[str, World, PlayerState]:
    """
    Új játékkörnyezet létrehozása a játékmesterrel.
    """
    clear_screen()
    print("=== Új játékkörnyezet létrehozása (Játékmester) ===\n")
    env_name = input("Játékkörnyezet neve: ").strip() or "Nevesítetlen környezet"
    world = World()
    player = PlayerState()

    # ----- normál kártyák -----
    clear_screen()
    print("Sima kártyák megadása.")
    num_cards = input_int("Hány sima kártyát szeretnél felvenni? ", 0)
    for i in range(num_cards):
        print(f"\n{i+1}. kártya:")
        name = input("  Név: ").strip()
        damage = input_int("  Sebzés: ", 0)
        hp = input_int("  Életerő: ", 1)
        while True:
            typ = input(f"  Típus ({', '.join(CARD_TYPES)}): ").strip()
            if typ in CARD_TYPES:
                break
            print("  Hibás típus, próbáld újra.")
        world.add_card(name, damage, hp, typ)

    # ----- vezérek -----
    clear_screen()
    print("Vezérkártyák megadása.")
    if not world.card_order:
        print("Nincsenek sima kártyák, ezért vezért sem tudunk létrehozni.")
        num_leaders = 0
    else:
        num_leaders = input_int("Hány vezérkártyát szeretnél felvenni? ", 0)
    for i in range(num_leaders):
        print(f"\n{i+1}. vezér:")
        name = input("  Vezér neve: ").strip()
        # alap kártya választása
        base_choice = choose_from_list(
            [(cn, cn) for cn in world.card_order],
            title="  Válassz alap kártyát a vezérhez:"
        )
        base_name = base_choice[0]
        # mód
        while True:
            mode = input("  Fejlesztés típusa ('sebzes' vagy 'eletero'): ").strip()
            if mode in ("sebzes", "eletero"):
                break
            print("  Csak 'sebzes' vagy 'eletero' lehet.")
        world.add_leader_from_base(name, base_name, mode)

    # ----- kazamaták -----
    clear_screen()
    print("Kazamaták megadása.")
    num_dungeons = input_int("Hány kazamatát szeretnél felvenni? ", 0)
    for i in range(num_dungeons):
        print(f"\n{i+1}. kazamata:")
        name = input("  Kazamata neve: ").strip()

        kind_choice = choose_from_list(
            [("egyszeru", "egyszerű"), ("kis", "kis"), ("nagy", "nagy")],
            title="  Típus:"
        )
        kind = kind_choice[0]

        # ellenfél sima kártyái
        enemy_sima = []
        if world.cards:
            print("  Add meg az ellenfél sima kártyáit (nevek vesszővel elválasztva, üres = nincs):")
            print("  Elérhető kártyák:", ", ".join(world.card_order))
            raw = input("  Kártyanevek: ").strip()
            if raw:
                for n in raw.split(","):
                    n = n.strip()
                    if n and n in world.cards:
                        enemy_sima.append(n)
        else:
            print("  Nincsenek sima kártyák, ez a kazamata üres lesz.")

        leader = None
        reward_type = None

        if kind == "egyszeru":
            # egyszerű kazamata, nincs vezér, de van jutalom
            while True:
                reward_type = input("  Jutalom típusa ('sebzes' vagy 'eletero'): ").strip()
                if reward_type in ("sebzes", "eletero"):
                    break
                print("  Csak 'sebzes' vagy 'eletero' lehet.")
        elif kind == "kis":
            # kis kazamata: vezér + jutalom
            if world.leader_order:
                leader_choice = choose_from_list(
                    [(ln, ln) for ln in world.leader_order],
                    title="  Vezérkártya kiválasztása:"
                )
                leader = leader_choice[0]
            else:
                print("  Nincsenek vezérkártyák, ide nem tudunk vezért rendelni.")
            while True:
                reward_type = input("  Jutalom típusa ('sebzes' vagy 'eletero'): ").strip()
                if reward_type in ("sebzes", "eletero"):
                    break
                print("  Csak 'sebzes' vagy 'eletero' lehet.")
        else:
            # nagy kazamata: vezér, jutalom mindig 'új sima lap'
            if world.leader_order:
                leader_choice = choose_from_list(
                    [(ln, ln) for ln in world.leader_order],
                    title="  Vezérkártya kiválasztása:"
                )
                leader = leader_choice[0]
            else:
                print("  Nincsenek vezérkártyák, ide nem tudunk vezért rendelni.")

        d = Dungeon(name=name, kind=kind, enemy_sima=enemy_sima, leader=leader, reward_type=reward_type)
        world.add_dungeon(d)

    # ----- kezdő gyűjtemény -----
    clear_screen()
    print("Kezdő gyűjtemény megadása játékosnak.")
    if not world.card_order:
        print("Figyelem: nincs egyetlen sima kártya sem a világban.")
    else:
        print("Elérhető sima kártyák:", ", ".join(world.card_order))
    raw = input("Add meg a gyűjteménybe kerülő lapok neveit vesszővel elválasztva: ").strip()
    if raw:
        for n in raw.split(","):
            n = n.strip()
            if n in world.cards:
                player.add_to_collection_from_template(world.cards[n])

    # ha semmit sem választott, beállíthatjuk alapnak az összeset
    if not player.collection_order:
        for name in world.card_order:
            player.add_to_collection_from_template(world.cards[name])

    return env_name, world, player


def master_menu() -> None:
    """
    Játékmester főmenü.
    """
    while True:
        clear_screen()
        print("=== Játékmester mód ===")
        print("1 – Új játékkörnyezet létrehozása")
        print("2 – Kilépés a főmenübe")
        choice = input("Választásod: ").strip()

        if choice == "1":
            env_name, world, player = create_environment_interactive()
            default_filename = env_name.replace(" ", "_").lower() + ".env.json"
            print(f"\nAlapértelmezett fájlnév: {default_filename}")
            filename = input("Fájlnév (Enter = alapértelmezett): ").strip() or default_filename
            path = os.path.abspath(filename)
            save_environment(path, env_name, world, player)
            print(f"Játékkörnyezet elmentve: {path}")
            press_enter()
        elif choice == "2":
            break
        else:
            print("Ismeretlen menüpont.")
            press_enter()
