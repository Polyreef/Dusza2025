from __future__  import annotations
from dataclasses import dataclass, asdict
from pathlib     import Path
from typing      import List, Set

import json



CARD_TYPES    : List[str] = ["levego", "viz", "tuz", "fold"]
CARD_TYPES_HU : List[str] = ["levegő", "víz", "tűz", "föld"]

STRONG_PAIRS : Set[tuple[str, str]] = {
    ("levego", "fold"),
    ("levego", "viz"),
    ("tuz",    "fold"),
    ("tuz",    "viz")
}

WEAK_PAIRS   : Set[tuple[str, str]] = {
    ("levego", "tuz"),
    ("fold",   "viz")
}


def clamp(x: int, minimum: int, maximum: int) -> int:
    return max(minimum, min(maximum, x))


@dataclass
class Card:
    name   : str
    damage : int
    hp     : int
    type   : str
    leader : bool = False

    
    def __post_init__(self) -> None:
        self.name   = self.name[:16]
        self.damage = clamp(self.damage, 2, 100)
        self.hp     = clamp(self.hp, 1, 100)
        
        if self.type not in CARD_TYPES:
            self.type = "levego"


    def __str__(self) -> str:
        base = f"{self.name:<16}  {self.damage:>3}/{self.hp:<3}  {self.get_type_hu():<6}"
        return base + ("  (vezér)" if self.leader else "")


    def get_type_hu(self) -> str:
        return CARD_TYPES_HU[CARD_TYPES.index(self.type)]


    def make_leader(self, mod: str) -> bool:
        if self.leader:
            return False
        
        self.leader = True
        
        if mod == "sebzes":
            self.damage *= 2
        elif mod == "eletero":
            self.hp *= 2
        else:
            return False
        
        return True


    def save(self, path: str) -> None:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(asdict(self), f, indent=4, ensure_ascii=False)


def load_card(path: str) -> Card | None:
    file_path = Path(path)
    if not file_path.is_file():
        return None
    
    with open(file_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    
    try:
        return Card(**data)
    except TypeError:
        return None


def calculate_damage(attacker_type: str, defender_type: str, base_damage: int) -> int:
    if attacker_type == defender_type:
        return base_damage
    
    pair = (attacker_type, defender_type)
    
    if pair in STRONG_PAIRS:
        return base_damage * 2
    if pair in WEAK_PAIRS:
        return base_damage // 2
    
    return base_damage