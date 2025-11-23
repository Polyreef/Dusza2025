from __future__  import annotations
from dataclasses import dataclass, field, asdict
from pathlib     import Path
from typing      import Dict, List

import json

from card    import Card, load_card
from dungeon import Dungeon, load_dungeon


@dataclass
class World:
    name: str
    
    cards    : Dict[str, Card]    = field(default_factory=dict)
    leaders  : Dict[str, Card]    = field(default_factory=dict)
    dungeons : Dict[str, Dungeon] = field(default_factory=dict)
    
    card_order   : List[str] = field(default_factory=list)
    leader_order : List[str] = field(default_factory=list)


    def __str__(self) -> str:
        cards    = ", ".join(self.cards.keys())
        leaders  = ", ".join(self.leaders.keys())
        dungeons = ", ".join(self.dungeons.keys())
        
        card_order   = ", ".join(self.card_order)
        leader_order = ", ".join(self.leader_order)

        return (
            f"{self.name}\n\n"
            
            f"Cards:    {cards}\n"
            f"Leaders:  {leaders}\n"
            f"Dungeons: {dungeons}\n\n"
            
            f"Card order:   {card_order}\n"
            f"Leader order: {leader_order}"
        )


    def save(self, path: str) -> None:
        d = {
            "name": self.name,
            
            "cards": list(self.cards.keys()),
            "leaders": list(self.leaders.keys()),
            "dungeons": list(self.dungeons.keys()),
            
            "card_order": self.card_order,
            "leader_order": self.leader_order
        }

        with open(path, "w", encoding="utf-8") as f:
            json.dump(d, f, indent=4, ensure_ascii=False)

        for c in self.cards.values():
            c.save(f"{c.name}.json")
        for l in self.leaders.values():
            l.save(f"{l.name}.json")
        for d in self.dungeons.values():
            d.save(f"{d.name}.json")


    def get_card(self, name: str) -> Card | None:
        return self.cards.get(name)

    def get_leader(self, name: str) -> Card | None:
        return self.leaders.get(name)

    def get_dungeon(self, name: str) -> Dungeon | None:
        return self.dungeons.get(name)


    def add_card(self, card: Card) -> bool:
        if card.leader:
            return False
        
        if card.name in self.cards or card.name in self.card_order:
            return False
        
        self.cards[card.name] = card
        self.card_order.append(card.name)
        
        return True

    def add_leader(self, leader: Card) -> bool:
        if not leader.leader:
            return False
        
        if leader.name in self.leaders or leader.name in self.leader_order:
            return False
        
        self.leaders[leader.name] = leader
        self.leader_order.append(leader.name)
        
        return True

    def add_dungeon(self, dungeon: Dungeon) -> bool:
        if dungeon.name in self.dungeons:
            return False
        
        self.dungeons[dungeon.name] = dungeon
        
        return True


    def export(self, path: str) -> None:
        lines = []

        for card in self.cards.values():
            lines.append(f"kartya;{card.name};{card.damage};{card.hp};{card.type}")

        lines.append("")

        for leader in self.leaders.values():
            lines.append(f"vezer;{leader.name};{leader.damage};{leader.hp};{leader.type}")

        lines.append("")

        for dungeon in self.dungeons.values():
            cards = ",".join(dungeon.cards)
            if dungeon.type == "egyszeru":
                lines.append(f"kazamata;{dungeon.type};{dungeon.name};{cards};{dungeon.reward}")
            elif dungeon.type == "kis":
                lines.append(f"kazamata;{dungeon.type};{dungeon.name};{cards};{dungeon.leader};{dungeon.reward}")
            elif dungeon.type == "nagy":
                lines.append(f"kazamata;{dungeon.type};{dungeon.name};{cards};{dungeon.leader}")

        with open(path, "w", encoding="utf-8") as f:
            f.write("\n".join(lines))


def load_world(path: str) -> World | None:
    file_path = Path(path)
    if not file_path.is_file():
        return None

    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)

    world = World(data["name"])

    for c in data["cards"]:
        card = load_card(f"{c}.json")
        if not card or not world.add_card(card):
            return None

    for l in data["leaders"]:
        leader = load_card(f"{l}.json")
        if not leader:
            return None
        
        if not leader.leader:
            leader.leader = True
        
        if not world.add_leader(leader):
            return None

    for d in data["dungeons"]:
        dungeon = load_dungeon(f"{d}.json")
        if not dungeon or not world.add_dungeon(dungeon):
            return None

    for c in data["card_order"]:
        if c in world.cards:
            if c not in world.card_order:
                world.card_order.append(c)
            else:
                return None
        else:
            return None

    for l in data["leader_order"]:
        if l in world.leaders:
            if l not in world.leader_order:
                world.leader_order.append(l)
            else:
                return None
        else:
            return None

    return world