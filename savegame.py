from __future__ import annotations

import json
from dataclasses import asdict
from typing import Dict, Any, Tuple

from player import PlayerState, PlayerCard


def save_game(path: str, env_file: str, difficulty: int, player: PlayerState) -> None:
    """
    Játékállás mentése JSON-be:
      - melyik játékkörnyezet fájlból indult
      - nehézségi szint
      - játékos gyűjteménye + paklija
    """
    data: Dict[str, Any] = {
        "env_file": env_file,
        "difficulty": int(difficulty),
        "player": {
            "collection": [
                asdict(player.collection[name]) for name in player.collection_order
            ],
            "collection_order": player.collection_order,
            "deck": player.deck,
        },
    }

    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def load_game(path: str) -> Tuple[str, int, PlayerState]:
    """
    Mentett játék betöltése.

    Visszaadja:
      (env_file, difficulty, player)
    """
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)

    env_file: str = data["env_file"]
    difficulty: int = int(data.get("difficulty", 0))

    p = PlayerState()
    p.collection_order = list(data["player"].get("collection_order", []))
    for pc in data["player"]["collection"]:
        card = PlayerCard(pc["name"], int(pc["damage"]), int(pc["hp"]), pc["type"])
        p.collection[card.name] = card
    p.deck = list(data["player"].get("deck", []))

    return env_file, difficulty, p
