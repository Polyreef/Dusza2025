import os

from typing import Literal

from core.battle import run_battle
from core.models import World, Dungeon, Player

# Egyetlen játékos van teszt módban; egyszerű globális tároló.
_player_holder = {"player": None}


def get_player():
    return _player_holder["player"]


def set_player(p):
    _player_holder["player"] = p


def run_test_mode(input_dir) -> Literal[True] | Literal[False]:
    """
    Teszt mód: az in.txt alapján futtatjuk a játékot.

    A nehézségi szint itt nem játszik szerepet.
    """

    world = World()
    set_player(None)

    in_path = os.path.join(input_dir, "in.txt")
    try:
        f = open(in_path, encoding="utf-8")
    except OSError:
        print("Hiba: nem sikerült megnyitni az in.txt fájlt:", in_path)
        return False

    with f:
        for raw_line in f:
            line = raw_line.strip()
            if not line:
                continue

            if not handle_line(line, input_dir, world):
                print(f"Sor: {line}")

    return True


def handle_line(line, input_dir, world) -> Literal[True] | Literal[False]:
    parts = [p.strip() for p in line.split(";")]
    cmd = parts[0].lower()

    player = get_player()

    if cmd == "uj kartya":
        # uj kartya;Nev;sebzes;eletero;tipus
        name = parts[1]
        damage = int(parts[2])
        health = int(parts[3])
        element = parts[4]

        if not world.add_simple_card(name, damage, health, element):
            return False

    elif cmd == "uj vezer":
        # uj vezer;VezerNev;AlapKartyaNev;sebzes/eletero
        name = parts[1]
        base_name = parts[2]
        mode = parts[3]

        if not world.add_leader_card(name, base_name, mode):
            return False

    elif cmd == "uj kazamata":
        # többféle forma, a tipus határozza meg
        kind = parts[1].lower()
        name = parts[2]
        simple_names = [n.strip() for n in parts[3].split(",") if n.strip()]
        leader_name = None
        reward_type = None

        if kind == "egyszeru":
            # uj kazamata;egyszeru;Nev;Sadan;eletero
            reward_type = parts[4]
        elif kind == "kis":
            # uj kazamata;kis;Nev;Aragorn,Eowyn,ObiWan;Darth ObiWan;eletero
            leader_name = parts[4]
            reward_type = parts[5]
        elif kind == "nagy":
            # uj kazamata;nagy;Nev;Aragorn,...;Darth ObiWan
            leader_name = parts[4]
        else:
            print(f"Ismeretlen kazamata típus: {kind}")
            return False

        try:
            dungeon = Dungeon(name, kind, simple_names, leader_name, reward_type)
        except ValueError as e:
            print(str(e))
            return False

        if not world.add_dungeon(dungeon):
            return False

    elif cmd == "uj jatekos":
        # új játékos, üres gyűjteménnyel
        player = Player()
        set_player(player)

    elif cmd == "felvetel gyujtemenybe":
        # felvetel gyujtemenybe;KartyaNev
        if not player:
            print("Nincs játékos, de gyűjteménybe vétel történne.")
            return False

        card_name = parts[1]
        player.add_card_from_world(world, card_name)

    elif cmd == "uj pakli":
        # uj pakli;Nev1,Nev2,...
        if not player:
            print("Nincs játékos, de paklit szeretnénk.")
            return False

        card_names = [n.strip() for n in parts[1].split(",") if n.strip()]
        if not player.set_deck(card_names):
            return False

    elif cmd == "harc":
        # harc;KazamataNev;out.harc01.txt
        if not player:
            print("Nincs játékos, de harc indulna.")
            return False

        dungeon_name = parts[1]
        out_filename = parts[2]
        dungeon = world.get_dungeon(dungeon_name)
        if not dungeon:
            return False

        # Teszt módban a nehézségi szint mindig 0.
        result = run_battle(world, player, dungeon, difficulty=0)
        if not result:
            return False

        # jutalom alkalmazása és utolsó sor
        final_line = apply_reward_and_get_final_line(world, player, dungeon, result)
        if not final_line:
            return False

        out_path = os.path.join(input_dir, out_filename)
        with open(out_path, "w", encoding="utf-8", newline="\n") as out_f:
            for l in result.log_lines:
                out_f.write(l + "\n")

            out_f.write(final_line + "\n")

    elif cmd == "export vilag":
        out_filename = parts[1]
        out_path = os.path.join(input_dir, out_filename)
        if not export_world(world, out_path):
            return False

    elif cmd == "export jatekos":
        if not player:
            print("Nincs játékos, de 'export jatekos' parancs érkezett.")
            return False

        out_filename = parts[1]
        out_path = os.path.join(input_dir, out_filename)
        export_player(player, out_path)

    else:
        print(f"Ismeretlen parancs: {cmd}")
        return False

    return True


def apply_reward_and_get_final_line(
    world, player, dungeon, result
) -> str | Literal[False]:
    """
    Harc végeredménye + jutalom feldolgozása, utolsó sor előállítása.
    """

    if result.outcome == "lose":
        return "jatekos vesztett"

    # játékos nyert
    if dungeon.kind in ("egyszeru", "kis"):
        reward_type = dungeon.reward_type  # "sebzes" vagy "eletero"
        card_name = result.last_player_attacker_name
        card = player.collection[card_name]

        if reward_type == "sebzes" and card.damage <= 99:
            card.damage += 1
        elif reward_type == "eletero" and card.health <= 98:
            card.health += 2
        else:
            print(f"Ismeretlen jutalom típus: {reward_type}")
            return False

        return f"jatekos nyert;{reward_type};{card_name}"

    elif dungeon.kind == "nagy":
        # első olyan sima kártya a világból, ami még nincs a gyűjteményben
        new_name = None
        for c in world.iter_simple_cards():
            if c.name not in player.collection:
                if not player.add_card_from_world(world, c.name):
                    return False

                new_name = c.name
                break

        if not new_name:
            # teszt módban feltételezik, hogy ilyen nem fordul elő
            return "jatekos nyert"
        else:
            return f"jatekos nyert;{new_name}"

    else:
        print(f"Ismeretlen kazamata típus: {dungeon.kind}")
        return False


def export_world(world, out_path) -> Literal[True] | Literal[False]:
    """
    Világ exportja.
    """

    with open(out_path, "w", encoding="utf-8", newline="\n") as f:
        for c in world.iter_simple_cards():
            f.write(f"kartya;{c.name};{c.damage};{c.health};{c.element}\n")

        for v in world.iter_leader_cards():
            f.write(f"vezer;{v.name};{v.damage};{v.health};{v.element}\n")

        for d in world.iter_dungeons():
            # kazamata;tipus;Nev;lista;vezer;[jutalom]
            base = f"kazamata;{d.kind};{d.name};" + ",".join(d.simple_card_names)
            if d.kind == "egyszeru":
                line = base + f";{d.reward_type}\n"
            elif d.kind == "kis":
                line = base + f";{d.leader_name};{d.reward_type}\n"
            elif d.kind == "nagy":
                line = base + f";{d.leader_name}\n"
            else:
                print(f"Ismeretlen kazamata típus: {d.kind}")
                return False

            f.write(line)

    return True


def export_player(player, out_path):
    """
    Játékos gyűjtemény + pakli exportja.
    """

    with open(out_path, "w", encoding="utf-8", newline="\n") as f:
        for c in player.collection.values():
            f.write(f"gyujtemeny;{c.name};{c.damage};{c.health};{c.element}\n")

        for name in player.deck:
            f.write(f"pakli;{name}\n")
