from __future__ import annotations

import os
from typing import Optional, Tuple, List

from world import World
from player import PlayerState
from combat import simulate_battle
from dungeon import Dungeon
from card import CardTemplate


def handle_line_testmode(
    line: str,
    world: World,
    player: Optional[PlayerState],
    base_dir: str
) -> PlayerState:
    """
    Egyetlen in.txt sor feldolgozása teszt módban.
    A player példányát frissítve adja vissza (ha nincs, létrehozza).
    """
    line = line.strip()
    if not line:
        return player or PlayerState()

    parts = [p.strip() for p in line.split(";")]
    cmd = parts[0]

    if cmd == "uj kartya":
        # uj kartya;Nev;sebzes;eletero;tipus
        name = parts[1]
        dmg = int(parts[2])
        hp = int(parts[3])
        typ = parts[4]
        world.add_card(name, dmg, hp, typ)

    elif cmd == "uj vezer":
        # uj vezer;VezerNev;AlapKartya;sebzes/eletero
        leader_name = parts[1]
        base_name = parts[2]
        mode = parts[3]
        world.add_leader_from_base(leader_name, base_name, mode)

    elif cmd == "uj kazamata":
        kind = parts[1]
        name = parts[2]
        if kind == "egyszeru":
            enemy_sima = [p.strip() for p in parts[3].split(",")] if parts[3] else []
            reward_type = parts[4]
            d = Dungeon(name=name, kind=kind, enemy_sima=enemy_sima, leader=None, reward_type=reward_type)
            world.add_dungeon(d)
        elif kind == "kis":
            enemy_sima = [p.strip() for p in parts[3].split(",")] if parts[3] else []
            leader = parts[4]
            reward_type = parts[5]
            d = Dungeon(name=name, kind=kind, enemy_sima=enemy_sima, leader=leader, reward_type=reward_type)
            world.add_dungeon(d)
        elif kind == "nagy":
            enemy_sima = [p.strip() for p in parts[3].split(",")] if parts[3] else []
            leader = parts[4]
            d = Dungeon(name=name, kind=kind, enemy_sima=enemy_sima, leader=leader, reward_type=None)
            world.add_dungeon(d)

    elif cmd == "uj jatekos":
        player = PlayerState()

    elif cmd == "felvetel gyujtemenybe":
        # felvetel gyujtemenybe;KartyaNev
        if player is None:
            player = PlayerState()
        cname = parts[1]
        tmpl = world.cards[cname]
        if cname not in player.collection:
            player.add_to_collection_from_template(tmpl)

    elif cmd == "uj pakli":
        # uj pakli;Nev1,Nev2,...
        if player is None:
            player = PlayerState()
        deck_names = [p.strip() for p in parts[1].split(",")] if len(parts) > 1 and parts[1] else []
        player.deck = deck_names

    elif cmd == "harc":
        # harc;KazamataNev;kimenetiFajl
        if player is None:
            player = PlayerState()
        dungeon_name = parts[1]
        out_filename = parts[2]
        dungeon = world.dungeons[dungeon_name]
        log_lines, _, _ = simulate_battle(world, player, dungeon, player.deck, difficulty=0)
        out_path = os.path.join(base_dir, out_filename)
        with open(out_path, "w", encoding="utf-8") as f:
            for l in log_lines:
                f.write(l + "\n")

    elif cmd == "export vilag":
        out_filename = parts[1]
        out_path = os.path.join(base_dir, out_filename)
        with open(out_path, "w", encoding="utf-8") as f:
            # sima lapok
            for name in world.card_order:
                c = world.cards[name]
                f.write(f"kartya;{c.name};{c.damage};{c.hp};{c.type}\n")
            # vezérek
            for name in world.leader_order:
                v = world.leaders[name]
                f.write(f"vezer;{v.name};{v.damage};{v.hp};{v.type}\n")
            # kazamaták
            for d in world.dungeons.values():
                if d.kind == "egyszeru":
                    sima_str = ",".join(d.enemy_sima)
                    f.write(f"kazamata;egyszeru;{d.name};{sima_str};{d.reward_type}\n")
                elif d.kind == "kis":
                    sima_str = ",".join(d.enemy_sima)
                    f.write(f"kazamata;kis;{d.name};{sima_str};{d.leader};{d.reward_type}\n")
                elif d.kind == "nagy":
                    sima_str = ",".join(d.enemy_sima)
                    f.write(f"kazamata;nagy;{d.name};{sima_str};{d.leader}\n")

    elif cmd == "export jatekos":
        out_filename = parts[1]
        out_path = os.path.join(base_dir, out_filename)
        if player is None:
            player = PlayerState()
        with open(out_path, "w", encoding="utf-8") as f:
            for name in player.collection_order:
                pc = player.collection[name]
                f.write(f"gyujtemeny;{pc.name};{pc.damage};{pc.hp};{pc.type}\n")
            for name in player.deck:
                f.write(f"pakli;{name}\n")

    return player or PlayerState()


def run_test_mode(base_dir: str) -> None:
    """
    Teszt mód futtatása – teljesen kompatibilis az I. forduló in.txt specifikációjával.
    A nehézségi szint NEM játszik szerepet, minden determinisztikus.
    """
    in_path = os.path.join(base_dir, "in.txt")
    if not os.path.isfile(in_path):
        print(f"Hiba: nem találom az in.txt fájlt ebben a mappában: {base_dir}")
        return

    world = World()
    player: Optional[PlayerState] = None

    with open(in_path, "r", encoding="utf-8") as f:
        for raw_line in f:
            raw_line = raw_line.strip()
            if not raw_line:
                continue
            player = handle_line_testmode(raw_line, world, player, base_dir)
