from pathlib import Path
from typing  import List

import json


class Player:
    def __init__(self, name) -> None:
        self.name: str = name

        self.collection : List[str] = []
        self.deck       : List[str] = []
    

    def __str__(self) -> str:
        string = f"{self.name}\n"
        string += "\n"
        string += f"Collection: {", ".join(card for card in self.collection)}\n"
        string += f"Deck      : {", ".join(card for card in self.deck)}"
        return string
    

    def save(self, path: str) -> None:
        d = {
            "name"       : self.name,
            "collection" : self.collection,
            "deck"       : self.deck
        }

        with open(path, "w") as f:
            json.dump(d, f, indent=4)
    

    def collection_add(self, card: str) -> bool:
        if card not in self.collection:
            self.collection.append(card)
            return True
        else:
            return False
    

    def deck_add(self, card: str) -> bool:
        if card not in self.deck and card in self.collection:
            self.deck.append(card)
            return True
        else:
            return False


def load_player(path: str) -> Player | None:
    if not Path(path).is_file():
        return None
        
    with open(path, "r", encoding="utf-8") as f:
        d = json.load(f)
        
    player = Player(d["name"])

    for card in d["collection"]:
        if not player.collection_add(card):
            return None
        
    for card in d["deck"]:
        if not player.deck_add(card):
            return None

    return player