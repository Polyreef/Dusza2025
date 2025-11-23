from __future__  import annotations
from dataclasses import dataclass, field, asdict
from pathlib     import Path
from typing      import List

import json


DUNGEON_TYPES    : List[str] = ["egyszeru", "kis", "nagy"]
DUNGEON_TYPES_HU : List[str] = ["egyszerű", "kis", "nagy"]


@dataclass
class Dungeon:
    type   : str
    name   : str
    cards  : List[str] = field(default_factory=list)
    leader : str = ""
    reward : str = ""

    
    def __post_init__(self) -> None:
        if self.type not in DUNGEON_TYPES:
            self.type = "egyszeru"
        
        self.name  = self.name[:20]
        self.cards = list(dict.fromkeys(self.cards))


    def __str__(self) -> str:
        cards = ", ".join(self.cards)
        
        leader = self.leader if self.leader else "-"
        reward = self.reward if self.reward else "-"
        
        return f"{self.name:<20}  {self.get_type_hu():<8}  {leader:<16}  {reward:<8}  {cards}"


    def save(self, path: str) -> None:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(asdict(self), f, indent=4, ensure_ascii=False)


    def get_type_hu(self) -> str:
        return DUNGEON_TYPES_HU[DUNGEON_TYPES.index(self.type)]


def load_dungeon(path: str) -> Dungeon | None:
    file_path = Path(path)
    if not file_path.is_file():
        return None
    
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    
    try:
        return Dungeon(**data)
    except TypeError:
        return None