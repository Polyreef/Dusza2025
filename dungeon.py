from pathlib import Path
from typing  import List

import json


DUNGEON_TYPES    : List[str] = ["egyszeru", "kis", "nagy"]
DUNGEON_TYPES_HU : List[str] = ["egyszerű", "kis", "nagy"]


class Dungeon:
    def __init__(self, type: str, name: str, cards: List[str], leader: str = "", reward: str = "") -> None:
        self.type   : str = type if type in DUNGEON_TYPES else "egyszeru"
        self.name   : str = name[:20]
        self.leader : str = leader
        self.reward : str = reward
        
        self.cards  : List[str] = []

        for card in cards:
            if card not in self.cards:
                self.cards.append(card)
    

    def __str__(self) -> str:
        cards: str = ", ".join(card for card in self.cards)
        
        leader: str = self.leader if self.leader != "" else "-"
        reward: str = self.reward if self.reward != "" else "-"

        return f"{self.name:<20}  {self.get_type_hu():<8}  {leader:<16}  {reward:<8}  {cards}"
    

    def save(self, path: str) -> None:
        d = {
            "type"   : self.type,
            "name"   : self.name,
            "cards"  : self.cards,
            "leader" : self.leader,
            "reward" : self.reward
        }

        with open(path, "w") as f:
            json.dump(d, f, indent=4)


    def get_type_hu(self) -> str:
        return DUNGEON_TYPES_HU[DUNGEON_TYPES.index(self.type)]


def load_dungeon(path: str) -> Dungeon | None:
    if not Path(path).is_file():
        return None
        
    with open(path, "r", encoding="utf-8") as f:
        d = json.load(f)
        
    return Dungeon(d["type"], d["name"], d["cards"], d["leader"], d["reward"])