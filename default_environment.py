from __future__ import annotations

from world import World
from player import PlayerState
from dungeon import Dungeon


def create_default_world_and_player() -> tuple[str, World, PlayerState]:
    """
    Az I. fordulóban megadott világ és gyűjtemény létrehozása környezetként.
    Az env_name egy beszédes név a környezethez.
    """
    env_name = "I. fordulós alap világ"
    w = World()

    # sima kártyák – az előző verziódban használt lista
    w.add_card("Arin", 2, 5, "fold")
    w.add_card("Liora", 2, 4, "levego")
    w.add_card("Nerun", 3, 3, "tuz")
    w.add_card("Selia", 2, 6, "viz")
    w.add_card("Torak", 3, 4, "fold")
    w.add_card("Emera", 2, 5, "levego")
    w.add_card("Vorn", 2, 7, "viz")
    w.add_card("Kael", 3, 5, "tuz")
    w.add_card("Myra", 2, 6, "fold")
    w.add_card("Thalen", 3, 5, "levego")
    w.add_card("Isara", 2, 6, "viz")

    # vezérek
    w.add_leader_from_base("Lord Torak", "Torak", "sebzes")
    w.add_leader_from_base("Priestess Selia", "Selia", "eletero")

    # kazamaták
    w.add_dungeon(Dungeon(
        name="Barlangi Portya",
        kind="egyszeru",
        enemy_sima=["Nerun"],
        leader=None,
        reward_type="sebzes",
    ))
    w.add_dungeon(Dungeon(
        name="Osi Szentely",
        kind="kis",
        enemy_sima=["Arin", "Emera", "Selia"],
        leader="Lord Torak",
        reward_type="eletero",
    ))
    w.add_dungeon(Dungeon(
        name="A melyseg kiralynoje",
        kind="nagy",
        enemy_sima=["Liora", "Arin", "Selia", "Nerun", "Torak"],
        leader="Priestess Selia",
        reward_type=None,
    ))

    # játékos gyűjtemény
    p = PlayerState()
    for name in ["Arin", "Liora", "Selia", "Nerun", "Torak", "Emera", "Kael", "Myra", "Thalen", "Isara"]:
        tmpl = w.cards[name]
        p.add_to_collection_from_template(tmpl)

    return env_name, w, p
