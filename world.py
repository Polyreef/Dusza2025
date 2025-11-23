from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List

from card import CardTemplate
from dungeon import Dungeon


@dataclass
class World:
    """
    A világhoz tartozó összes definíció: sima lapok, vezérek, kazamaták.
    """
    cards: Dict[str, CardTemplate] = field(default_factory=dict)
    card_order: List[str] = field(default_factory=list)
    leaders: Dict[str, CardTemplate] = field(default_factory=dict)
    leader_order: List[str] = field(default_factory=list)
    dungeons: Dict[str, Dungeon] = field(default_factory=dict)

    # --- világelemek létrehozása ---

    def add_card(self, name: str, damage: int, hp: int, typ: str) -> None:
        self.cards[name] = CardTemplate(name, damage, hp, typ)
        if name not in self.card_order:
            self.card_order.append(name)

    def add_leader_from_base(self, leader_name: str, base_name: str, mode: str) -> None:
        base = self.cards[base_name]
        if mode == "sebzes":
            damage = base.damage * 2
            hp = base.hp
        elif mode == "eletero":
            damage = base.damage
            hp = base.hp * 2
        else:
            raise ValueError("Ismeretlen vezér származtatási mód: " + mode)

        self.leaders[leader_name] = CardTemplate(leader_name, damage, hp, base.type)
        if leader_name not in self.leader_order:
            self.leader_order.append(leader_name)

    def add_dungeon(self, dungeon: Dungeon) -> None:
        self.dungeons[dungeon.name] = dungeon

    # --- segédfüggvények ---

    def get_template(self, name: str) -> CardTemplate:
        if name in self.cards:
            return self.cards[name]
        if name in self.leaders:
            return self.leaders[name]
        raise KeyError(f"Ismeretlen kártyanév a világban: {name}")
