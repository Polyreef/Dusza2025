from __future__  import annotations
from dataclasses import dataclass, field, asdict
from pathlib     import Path
from typing      import List

import json


@dataclass
class Player:
    name       : str
    
    collection : List[str] = field(default_factory=list)
    deck       : List[str] = field(default_factory=list)

    collection_order: List[str] = field(default_factory=list)


    def __str__(self) -> str:
        collection = ", ".join(self.collection)
        deck       = ", ".join(self.deck)
        
        return (
            f"{self.name}\n\n"
            
            f"Collection: {collection}\n"
            f"Deck:       {deck}"
        )


    def save(self, path: str) -> None:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(asdict(self), f, indent=4, ensure_ascii=False)


    def collection_add(self, card: str) -> bool:
        if card not in self.collection:
            self.collection.append(card)
            return True
        
        return False

    def deck_add(self, card: str) -> bool:
        if card in self.collection and card not in self.deck:
            self.deck.append(card)
            return True
        
        return False


def load_player(path: str) -> Player | None:
    file_path = Path(path)
    if not file_path.is_file():
        return None
    
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    
    try:
        player = Player(data["name"])
    except KeyError:
        return None

    for c in data.get("collection", []):
        player.collection_add(c)
    for c in data.get("deck", []):
        player.deck_add(c)

    return player