import json

from .models import World, CardDefinition, Dungeon, Player, GameState
from .environment import GameEnvironment


# Segédfüggvények: CardDefinition, Dungeon


def _card_to_dict(card):
    return {
        "name": card.name,
        "damage": card.damage,
        "health": card.health,
        "element": card.element,
    }


def _card_from_dict(d):
    return CardDefinition(
        d["name"],
        d["damage"],
        d["health"],
        d["element"],
    )


def _dungeon_to_dict(dungeon):
    return {
        "name": dungeon.name,
        "kind": dungeon.kind,
        "simple_card_names": list(dungeon.simple_card_names),
        "leader_name": dungeon.leader_name,
        "reward_type": dungeon.reward_type,
    }


def _dungeon_from_dict(d):
    return Dungeon(
        d["name"],
        d["kind"],
        d["simple_card_names"],
        d.get("leader_name"),
        d.get("reward_type"),
    )


# World mentése / betöltése


def world_to_dict(world):
    simple_cards = [_card_to_dict(c) for c in world.iter_simple_cards()]
    leader_cards = [_card_to_dict(c) for c in world.iter_leader_cards()]
    dungeons = [_dungeon_to_dict(d) for d in world.iter_dungeons()]
    return {
        "simple_cards": simple_cards,
        "leader_cards": leader_cards,
        "dungeons": dungeons,
    }


def world_from_dict(data):
    world = World()
    for c in data.get("simple_cards", []):
        card = _card_from_dict(c)
        world.simple_cards[card.name] = card
    for c in data.get("leader_cards", []):
        card = _card_from_dict(c)
        world.leader_cards[card.name] = card
    for d in data.get("dungeons", []):
        dungeon = _dungeon_from_dict(d)
        world.dungeons[dungeon.name] = dungeon
    return world


# Player mentése / betöltése


def player_to_dict(player):
    collection = [_card_to_dict(c) for c in player.collection.values()]
    return {
        "collection": collection,
        "deck": list(player.deck),
    }


def player_from_dict(data):
    player = Player()
    for c in data.get("collection", []):
        card = _card_from_dict(c)
        player.collection[card.name] = card

    deck = data.get("deck", [])
    # itt nem ellenőrizzük újra a szabályt, a mentett állapotot bízunk
    player.deck = list(deck)
    return player


# GameEnvironment mentése / betöltése


def environment_to_dict(env):
    starting_collection = [_card_to_dict(c) for c in env.starting_collection.values()]
    return {
        "name": env.name,
        "world": world_to_dict(env.world),
        "starting_collection": starting_collection,
    }


def environment_from_dict(data):
    name = data["name"]
    world = world_from_dict(data["world"])
    starting_collection = {}
    for c in data.get("starting_collection", []):
        card = _card_from_dict(c)
        starting_collection[card.name] = card

    return GameEnvironment(name, world, starting_collection)


def save_environment_to_file(env, filepath):
    """
    Játékkörnyezet mentése JSON-ba.
    """

    data = environment_to_dict(env)
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def load_environment_from_file(filepath):
    """
    Játékkörnyezet betöltése JSON-ból.
    """

    with open(filepath, "r", encoding="utf-8") as f:
        data = json.load(f)

    return environment_from_dict(data)


# GameState mentése / betöltése


def gamestate_to_dict(state):
    return {
        "environment_name": state.environment_name,
        "difficulty": state.difficulty,
        "player": player_to_dict(state.player),
    }


def gamestate_from_dict(data):
    player = player_from_dict(data["player"])
    difficulty = data.get("difficulty", 0)
    env_name = data.get("environment_name")

    return GameState(player, difficulty, env_name)


def save_gamestate_to_file(state, filepath):
    """
    Játékállapot (GameState) mentése JSON-ba.
    """

    data = gamestate_to_dict(state)
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def load_gamestate_from_file(filepath):
    """
    Játékállapot betöltése JSON-ból.
    """

    with open(filepath, "r", encoding="utf-8") as f:
        data = json.load(f)

    return gamestate_from_dict(data)
