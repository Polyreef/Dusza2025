import os

from core.models import World, Dungeon, Player
from core.battle import run_battle

# Egyetlen játékos van teszt módban; egyszerű globális tároló.
_player_holder = {"player": None}


def get_player():
    return _player_holder["player"]


def set_player(p):
    _player_holder["player"] = p


def run_test_mode(input_dir):
    """
    Teszt mód: az in.txt alapján futtatjuk a játékot.

    A nehézségi szint itt nem játszik szerepet.
    """

    world = World()
    set_player(None)

    in_path = os.path.join(input_dir, "in.txt")
    try:
        f = open(in_path, encoding="ascii")
    except OSError:
        print("Hiba: nem sikerült megnyitni az in.txt fájlt:", in_path)
        return -1

    with f:
        for raw_line in f:
            line = raw_line.strip()
            if not line:
                continue

            if handle_line(line, input_dir, world) == -1:
                print(f"Hiba ennél a sornál: {line}")


def handle_line(line, input_dir, world):
    parts = [p.strip() for p in line.split(";")]
    cmd = parts[0]

    player = get_player()

    if cmd == "uj kartya":
        # uj kartya;Nev;sebzes;eletero;tipus
        name = parts[1]
        damage = int(parts[2])
        health = int(parts[3])
        element = parts[4]
        if world.add_simple_card(name, damage, health, element) == -1:
            print("Hiba a sima kártya világhoz adásával.")
            return -1

    elif cmd == "uj vezer":
        # uj vezer;VezerNev;AlapKartyaNev;sebzes/eletero
        name = parts[1]
        base_name = parts[2]
        mode = parts[3]
        if world.add_leader_card(name, base_name, mode) == -1:
            print("Hiba a vezérkártya világhoz adásával.")
            return -1

    elif cmd == "uj kazamata":
        # többféle forma, a tipus határozza meg
        kind = parts[1]
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
            return -1

        dungeon = Dungeon(name, kind, simple_names, leader_name, reward_type)
        if world.add_dungeon(dungeon) == -1:
            print("Hiba a kazamata világhoz adásával.")
            return -1

    elif cmd == "uj jatekos":
        # új játékos, üres gyűjteménnyel
        player = Player()
        set_player(player)

    elif cmd == "felvetel gyujtemenybe":
        # felvetel gyujtemenybe;KartyaNev
        if player is None:
            print("Nincs játékos, de gyűjteménybe vétel történne.")
            return -1

        card_name = parts[1]
        if player.add_card_from_world(world, card_name) == -1:
            print("Hiba a ")

    elif cmd == "uj pakli":
        # uj pakli;Nev1,Nev2,...
        if player is None:
            print("Nincs játékos, de paklit szeretnénk.")
            return -1

        card_names = [n.strip() for n in parts[1].split(",") if n.strip()]
        player.set_deck(card_names)

    elif cmd == "harc":
        # harc;KazamataNev;out.harc01.txt
        if player is None:
            print("Nincs játékos, de harc indulna.")
            return -1

        dungeon_name = parts[1]
        out_filename = parts[2]
        dungeon = world.get_dungeon(dungeon_name)

        # Teszt módban a nehézségi szint mindig 0.
        result = run_battle(world, player, dungeon, difficulty=0)
        if result == -1:
            print("Hiba a harc levezényelésénél.")
            return -1

        # jutalom alkalmazása és utolsó sor
        final_line = apply_reward_and_get_final_line(world, player, dungeon, result)
        if final_line == -1:
            print("Hiba a harc végénél és/vagy jutalom feldolgozásánál.")
            return -1

        out_path = os.path.join(input_dir, out_filename)
        with open(out_path, "w", encoding="ascii", newline="\n") as out_f:
            for l in result.log_lines:
                out_f.write(l + "\n")

            out_f.write(final_line + "\n")

    elif cmd == "export vilag":
        out_filename = parts[1]
        out_path = os.path.join(input_dir, out_filename)
        if export_world(world, out_path) == -1:
            print("Hiba a világ exportálásánál.")
            return -1

    elif cmd == "export jatekos":
        if player is None:
            print("Nincs játékos, de 'export jatekos' parancs érkezett.")
            return -1

        out_filename = parts[1]
        out_path = os.path.join(input_dir, out_filename)
        export_player(player, out_path)

    else:
        print(f"Ismeretlen parancs: {cmd}")
        return -1


def apply_reward_and_get_final_line(world, player, dungeon, result):
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

        if reward_type == "sebzes":
            card.damage += 1
        elif reward_type == "eletero":
            card.health += 2
        else:
            print(f"Ismeretlen jutalom típus: {reward_type}")
            return -1

        return f"jatekos nyert;{reward_type};{card_name}"

    elif dungeon.kind == "nagy":
        # első olyan sima kártya a világból, ami még nincs a gyűjteményben
        new_name = None
        for c in world.iter_simple_cards():
            if c.name not in player.collection:
                player.add_card_from_world(world, c.name)
                new_name = c.name
                break

        if new_name is None:
            # teszt módban feltételezik, hogy ilyen nem fordul elő
            return "jatekos nyert"
        else:
            return f"jatekos nyert;{new_name}"

    else:
        print(f"Ismeretlen kazamata típus: {dungeon.kind}")
        return -1


def export_world(world, out_path):
    """
    Világ exportja.
    """

    with open(out_path, "w", encoding="ascii", newline="\n") as f:
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
                return -1

            f.write(line)


def export_player(player, out_path):
    """
    Játékos gyűjtemény + pakli exportja.
    """

    with open(out_path, "w", encoding="ascii", newline="\n") as f:
        for c in player.collection.values():
            f.write(
                "gyujtemeny;%s;%d;%d;%s\n" % (c.name, c.damage, c.health, c.element)
            )

        for name in player.deck:
            f.write("pakli;%s\n" % name)
