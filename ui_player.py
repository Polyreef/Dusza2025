from __future__ import annotations

import glob
import os
from math import ceil
from typing import Optional, Tuple

from world import World
from player import PlayerState
from environment import load_environment
from savegame import save_game, load_game
from combat import simulate_battle
from ui_common import clear_screen, press_enter, input_int, choose_from_list


def list_env_files() -> list:
    return sorted(glob.glob("*.env.json"))


def list_save_files() -> list:
    return sorted(glob.glob("*.save.json"))


def print_world_and_player(world: World, player: PlayerState, difficulty: int, env_name: str) -> None:
    print(f"=== Játékkörnyezet: {env_name} ===")
    print(f"Nehézségi szint: {difficulty}\n")

    print("=== Világ – sima kártyák ===")
    for name in world.card_order:
        c = world.cards[name]
        print(f"{c.name}: sebzes={c.damage}, eletero={c.hp}, tipus={c.type}")

    print("\n=== Világ – vezérek ===")
    if not world.leader_order:
        print("Nincsenek vezérkártyák.")
    else:
        for name in world.leader_order:
            v = world.leaders[name]
            print(f"{v.name}: sebzes={v.damage}, eletero={v.hp}, tipus={v.type}")

    print("\n=== Kazamaták ===")
    if not world.dungeons:
        print("Nincsenek kazamaták.")
    else:
        for d in world.dungeons.values():
            enemy_cards = d.enemy_sima + ([d.leader] if d.leader else [])
            if d.kind in ("egyszeru", "kis"):
                reward = d.reward_type
            else:
                reward = "új sima lap a világból"
            print(f"- {d.name} ({d.kind}) – ellenfelek: {', '.join(enemy_cards) if enemy_cards else 'nincs'}, nyeremény: {reward}")

    print("\n=== Játékos gyűjteménye ===")
    if not player.collection_order:
        print("A gyűjtemény üres.")
    else:
        for name in player.collection_order:
            pc = player.collection[name]
            print(f"{pc.name}: sebzes={pc.damage}, eletero={pc.hp}, tipus={pc.type}")

    print("\n=== Aktuális pakli ===")
    if not player.deck:
        print("Nincs összeállított pakli.")
    else:
        print(", ".join(player.deck))


def configure_deck(player: PlayerState) -> None:
    clear_screen()
    print("--- Pakli összeállítása ---\n")
    if not player.collection_order:
        print("Nincs egyetlen lap sem a gyűjteményedben.")
        press_enter()
        return

    print("Gyűjteményben elérhető lapok:")
    print(", ".join(player.collection_order))
    max_deck = ceil(len(player.collection_order) / 2)
    print(f"A pakli legfeljebb {max_deck} lapból állhat.\n")

    while True:
        raw = input("Add meg a pakliba kerülő lapok neveit vesszővel elválasztva (Enter = megszakítás): ").strip()
        if not raw:
            print("Pakli változatlanul marad.")
            press_enter()
            return
        names = [n.strip() for n in raw.split(",") if n.strip()]
        if not names:
            print("Nem adtál meg egyetlen lapot sem.")
            continue
        unknown = [n for n in names if n not in player.collection]
        if unknown:
            print("Ismeretlen lapok:", ", ".join(unknown))
            continue
        if len(set(names)) != len(names):
            print("A pakliban egy lap csak egyszer szerepelhet.")
            continue
        if len(names) > max_deck:
            print(f"Túl sok lap: legfeljebb {max_deck} lehet.")
            continue
        player.deck = names
        print("Pakli frissítve:", ", ".join(player.deck))
        press_enter()
        return


def choose_dungeon(world: World, player: PlayerState) -> Optional[str]:
    """
    Kazamata választása, nagy kazamatára csak akkor enged, ha van még nyerhető sima lap.
    Visszatér a kazamata nevével vagy None-nal.
    """
    if not world.dungeons:
        print("Nincs egyetlen kazamata sem a világban.")
        press_enter()
        return None

    items = []
    for d in world.dungeons.values():
        enemy_cards = d.enemy_sima + ([d.leader] if d.leader else [])
        if d.kind in ("egyszeru", "kis"):
            reward = d.reward_type
        else:
            reward = "új sima lap a világból"
        label = f"{d.name} ({d.kind}) – ellenfelek: {', '.join(enemy_cards) if enemy_cards else 'nincs'}, nyeremény: {reward}"
        items.append((d.name, label))

    while True:
        clear_screen()
        choice = choose_from_list(items, title="Válassz kazamatát (Enter = vissza):", allow_empty=True)
        if choice is None:
            return None
        dungeon_name = choice[0]
        d = world.dungeons[dungeon_name]
        if d.kind == "nagy":
            has_new = any(cname not in player.collection for cname in world.card_order)
            if not has_new:
                print("Már minden világbeli sima lap a gyűjteményedben van, ide nem léphetsz be.")
                press_enter()
                continue
        return dungeon_name


def run_battle(world: World, player: PlayerState, difficulty: int, env_name: str) -> None:
    if not player.deck:
        print("Előbb állítsd össze a paklidat!")
        press_enter()
        return

    dungeon_name = choose_dungeon(world, player)
    if dungeon_name is None:
        return
    d = world.dungeons[dungeon_name]

    clear_screen()
    print(f"--- Harc indul: {d.name} ---\n")
    log_lines, result, extra = simulate_battle(world, player, d, player.deck, difficulty=difficulty)
    for line in log_lines:
        print(line)
    print()

    if result == "jatekos":
        print("Győztél!")
        if extra:
            kind = extra[0]
            if kind == "upgrade":
                _, rtype, cname = extra
                if rtype == "sebzes":
                    print(f"{cname} +1 sebzést kapott.")
                else:
                    print(f"{cname} +2 életerőt kapott.")
            elif kind == "newcard":
                _, cname = extra
                if cname:
                    print(f"Új lapot szereztél: {cname}")
                else:
                    print("Már nem volt új világbeli lap, így extra jutalmat nem kaptál.")
    else:
        print("Sajnos vesztettél.")
    press_enter()


def start_new_game_from_env() -> None:
    """
    Új játék indítása egy kiválasztott játékkörnyezetből.
    """
    env_files = list_env_files()
    clear_screen()
    if not env_files:
        print("Nem található egyetlen játékkörnyezet (*.env.json) sem az aktuális mappában.")
        press_enter()
        return

    choice = choose_from_list(
        [(f, os.path.basename(f)) for f in env_files],
        title="Válassz játékkörnyezetet:"
    )
    env_file = choice[0]

    env_name, world, base_player = load_environment(env_file)

    clear_screen()
    print(f"Kiválasztott környezet: {env_name}")
    difficulty = input_int("Add meg a nehézségi szintet (0–10): ", 0, 10)

    # új játékos állapot: másolat a kezdő gyűjteményről, üres paklival
    player = PlayerState()
    for name in base_player.collection_order:
        player.collection[name] = base_player.collection[name]
        player.collection_order.append(name)
    player.deck = []

    game_loop(world, player, difficulty, env_name, env_file)


def continue_game_from_save() -> None:
    """
    Meglévő mentett játék folytatása.
    """
    save_files = list_save_files()
    clear_screen()
    if not save_files:
        print("Nem található egyetlen mentett játék (*.save.json) sem.")
        press_enter()
        return

    choice = choose_from_list(
        [(f, os.path.basename(f)) for f in save_files],
        title="Válassz mentett játékot:"
    )
    save_file = choice[0]
    env_file, difficulty, player = load_game(save_file)

    # környezet betöltése
    if not os.path.isfile(env_file):
        print("A mentéshez tartozó játékkörnyezet fájl nem található:")
        print(env_file)
        press_enter()
        return

    env_name, world, _ = load_environment(env_file)

    game_loop(world, player, difficulty, env_name, env_file)


def game_loop(world: World, player: PlayerState, difficulty: int, env_name: str, env_file: str) -> None:
    """
    Folyamatban lévő játék menüje (világ + játékos + nehézség).
    """
    while True:
        clear_screen()
        print("=== Játékos mód – Játék ===")
        print("1 – Világ és játékos állapotának megjelenítése")
        print("2 – Pakli összeállítása / módosítása")
        print("3 – Harc indítása egy kazamatában")
        print("4 – Játék mentése")
        print("5 – Vissza a főmenübe")
        choice = input("Választásod: ").strip()

        if choice == "1":
            clear_screen()
            print_world_and_player(world, player, difficulty, env_name)
            print()
            press_enter()
        elif choice == "2":
            configure_deck(player)
        elif choice == "3":
            run_battle(world, player, difficulty, env_name)
        elif choice == "4":
            default_name = env_name.replace(" ", "_").lower() + ".save.json"
            print(f"Alapértelmezett mentésfájlnév: {default_name}")
            filename = input("Mentésfájl neve (Enter = alapértelmezett): ").strip() or default_name
            path = os.path.abspath(filename)
            save_game(path, env_file=env_file, difficulty=difficulty, player=player)
            print(f"Játék elmentve: {path}")
            press_enter()
        elif choice == "5":
            break
        else:
            print("Ismeretlen menüpont.")
            press_enter()


def player_menu() -> None:
    """
    Játékos főmenü.
    """
    while True:
        clear_screen()
        print("=== Játékos mód ===")
        print("1 – Új játék indítása játékkörnyezetből")
        print("2 – Játék folytatása mentésből")
        print("3 – Vissza a főmenübe")
        choice = input("Választásod: ").strip()

        if choice == "1":
            start_new_game_from_env()
        elif choice == "2":
            continue_game_from_save()
        elif choice == "3":
            break
        else:
            print("Ismeretlen menüpont.")
            press_enter()
