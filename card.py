from pathlib import Path
from typing  import List, Set

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


class Card:
    def __init__(self, name: str, damage: int, hp: int, type: str, leader: bool) -> None:
        self.name   : str = name[:16]
        self.damage : int = clamp(damage, 2, 100)
        self.hp     : int = clamp(hp, 1, 100)
        self.type   : str = type if type in CARD_TYPES else "levego"

        self.leader : bool = leader
    

    def __str__(self) -> str:
        if self.leader:
            return f"{self.name:<16}  {self.damage:>3}/{self.hp:<3}  {self.get_type_hu():<6}  (vezér)"
        else:
            return f"{self.name:<16}  {self.damage:>3}/{self.hp:<3}  {self.get_type_hu():<6}"
    

    def save(self, path: str) -> None:
        d = {
            "name"   : self.name,
            "damage" : self.damage,
            "hp"     : self.hp,
            "type"   : self.type,
            "leader" : self.leader
        }

        with open(path, "w") as f:
            json.dump(d, f, indent=4)
    

    def get_type_hu(self) -> str:
        return CARD_TYPES_HU[CARD_TYPES.index(self.type)]
    

    def make_leader(self, mod: str) -> bool:
        if not self.leader:
            self.leader = True

            if mod == "sebzes"  : self.damage *= 2
            if mod == "eletero" : self.hp     *= 2

            return True
        else:
            return False


def load_card(path: str) -> Card | None:
    if not Path(path).is_file():
        return None
        
    with open(path, "r", encoding="utf-8") as f:
        d = json.load(f)

    return Card(d["name"], d["damage"], d["hp"], d["type"], d["leader"])


def clamp(x, minimum, maximum) -> int:
    if x < minimum:
        return minimum
    if x > maximum:
        return maximum
    return x


def calculate_damage(attacker_type: str, defender_type: str, base_damage: int) -> int:
    if attacker_type == defender_type:
        return base_damage
    
    pair: tuple[str, str] = (attacker_type, defender_type)

    if pair in STRONG_PAIRS:
        return base_damage * 2
    if pair in WEAK_PAIRS:
        return base_damage // 2
    
    return base_damage