import json

from core.environment import Environment
from core.models import World, CardDefinition, Dungeon, Player, State


# Segédfüggvények: CardDefinition, Dungeon


def _card_to_dict(card: CardDefinition) -> dict:
    return {
        "name": card.name.strip(),
        "damage": card.damage,
        "health": card.health,
        "element": card.element.strip().lower(),
    }


def _card_from_dict(d: dict) -> CardDefinition:
    return CardDefinition(
        d["name"].strip(),
        d["damage"],
        d["health"],
        d["element"].strip().lower(),
    )


def _dungeon_to_dict(dungeon: Dungeon) -> dict:
    leader_name = (
        dungeon.leader_name.strip() if dungeon.leader_name is not None else None
    )
    reward_type = (
        dungeon.reward_type.strip().lower() if dungeon.reward_type is not None else None
    )
    return {
        "name": dungeon.name.strip(),
        "kind": dungeon.kind.strip().lower(),
        "simple_card_names": list(dungeon.simple_card_names),
        "leader_name": leader_name,
        "reward_type": reward_type,
    }


def _dungeon_from_dict(d: dict) -> Dungeon:
    leader_name = d.get("leader_name")
    if leader_name is not None:
        leader_name = leader_name.strip()

    reward_type = d.get("reward_type")
    if reward_type is not None:
        reward_type = reward_type.strip().lower()

    return Dungeon(
        d["name"].strip(),
        d["kind"].strip().lower(),
        d["simple_card_names"],
        leader_name,
        reward_type,
    )


# World mentése / betöltése


def world_to_dict(world: World) -> dict:
    simple_cards = [
        {**_card_to_dict(c), "style": world.simple_styles[c.name]}
        for c in world.iter_simple_cards()
    ]
    leader_cards = [
        {**_card_to_dict(c), "style": world.leader_styles[c.name]}
        for c in world.iter_leader_cards()
    ]

    dungeons = [_dungeon_to_dict(d) for d in world.iter_dungeons()]
    return {
        "simple_cards": simple_cards,
        "leader_cards": leader_cards,
        "dungeons": dungeons,
    }


def world_from_dict(data: dict) -> World:
    world = World()

    for c in data.get("simple_cards", []):
        card = _card_from_dict(c)
        world.simple_cards[card.name] = card

        style = c.get("style", 1)
        world.simple_styles[card.name] = style

    for c in data.get("leader_cards", []):
        card = _card_from_dict(c)
        world.leader_cards[card.name] = card

        style = c.get("style", 1)
        world.leader_styles[card.name] = style

    for d in data.get("dungeons", []):
        dungeon = _dungeon_from_dict(d)
        world.dungeons[dungeon.name] = dungeon

    return world


# Player mentése / betöltése


def player_to_dict(player: Player) -> dict:
    collection = [_card_to_dict(c) for c in player.collection.values()]
    return {
        "collection": collection,
        "deck": list(player.deck),
    }


def player_from_dict(data: dict) -> Player:
    player = Player()
    for c in data.get("collection", []):
        card = _card_from_dict(c)
        player.collection[card.name] = card

    deck = data.get("deck", [])
    # itt nem ellenőrizzük újra a szabályt, a mentett állapotot bízunk
    player.deck = list(deck)

    return player


# Environment mentése / betöltése


def environment_to_dict(env: Environment) -> dict:
    starting_collection = [_card_to_dict(c) for c in env.starting_collection.values()]
    return {
        "name": env.name,
        "world": world_to_dict(env.world),
        "starting_collection": starting_collection,
    }


def environment_from_dict(data: dict) -> Environment:
    name = data["name"]
    world = world_from_dict(data["world"])
    starting_collection = {}
    for c in data.get("starting_collection", []):
        card = _card_from_dict(c)
        starting_collection[card.name] = card

    return Environment(name, world, starting_collection)


def save_environment_to_file(env: Environment, filepath: str):
    """
    Játékkörnyezet mentése JSON-ba.
    """

    data = environment_to_dict(env)
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def load_environment_from_file(filepath: str) -> Environment:
    """
    Játékkörnyezet betöltése JSON-ból.
    """

    with open(filepath, "r", encoding="utf-8") as f:
        data = json.load(f)

    return environment_from_dict(data)


# State mentése / betöltése


def state_to_dict(state: State) -> dict:
    return {
        "environment_name": state.environment_name,
        "difficulty": state.difficulty,
        "player": player_to_dict(state.player),
    }


def state_from_dict(data: dict) -> State:
    player = player_from_dict(data["player"])
    difficulty = data.get("difficulty", 0)
    env_name = data.get("environment_name")

    return State(player, difficulty, env_name)


def save_state_to_file(state: State, filepath: str):
    """
    Játékállapot (State) mentése JSON-ba.
    """

    data = state_to_dict(state)
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def load_state_from_file(filepath: str) -> State:
    """
    Játékállapot betöltése JSON-ból.
    """

    with open(filepath, "r", encoding="utf-8") as f:
        data = json.load(f)

    return state_from_dict(data)
