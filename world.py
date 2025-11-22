from pathlib import Path
from typing  import Dict, List

import json

from card    import Card, load_card
from dungeon import Dungeon, load_dungeon


class World:
    def __init__(self, name: str) -> None:
        self.name = name[:20]

        self.cards    : Dict[str, Card]    = {}
        self.leaders  : Dict[str, Card]    = {}
        self.dungeons : Dict[str, Dungeon] = {}

        self.card_order   : List[str] = []
        self.leader_order : List[str] = []
    

    def __str__(self) -> str:
        string = f"{self.name}\n"
        string += "\n"
        string += f"Cards:    {", ".join(card for card in self.cards.keys())}\n"
        string += f"Leaders:  {", ".join(leader for leader in self.leaders.keys())}\n"
        string += f"Dungeons: {", ".join(dungeon for dungeon in self.dungeons.keys())}\n"
        string += "\n"
        string += f"Card order:   {", ".join(card for card in self.card_order)}\n"
        string += f"Leader order: {", ".join(card for card in self.card_order)}"
        return string
    

    def save(self, path: str) -> None:
        d = {
            "name"         : self.name,
            "cards"        : [card.name for card in self.cards.values()],
            "leaders"      : [leader.name for leader in self.leaders.values()],
            "dungeons"     : [dungeon.name for dungeon in self.dungeons.values()],
            "card_order"   : [card for card in self.card_order],
            "leader_order" : [leader for leader in self.leader_order]
        }

        with open(path, "w") as f:
            json.dump(d, f, indent=4)
        
        for card in self.cards.values():
            card.save(f"{card.name}.json")
        
        for leader in self.leaders.values():
            leader.save(f"{leader.name}.json")
        
        for dungeon in self.dungeons.values():
            dungeon.save(f"{dungeon.name}.json")
    

    def get_card(self, name: str) -> Card | None:
        if name in self.cards:
            return self.cards[name]
        
        return None
    

    def get_leader(self, name: str) -> Card | None:
        if name in self.leaders:
            return self.leaders[name]
        
        return None
    

    def get_dungeon(self, name: str) -> Dungeon | None:
        if name in self.dungeons:
            return self.dungeons[name]
        
        return None
    

    def add_card(self, card: Card) -> bool:
        if card.name not in self.card_order and not card.leader:
            self.cards[card.name] = card
            self.card_order.append(card.name)
            return True
        else:
            return False
    

    def add_leader(self, leader: Card) -> bool:
        if leader.name not in self.leader_order and leader.leader:
            self.leaders[leader.name] = leader
            self.leader_order.append(leader.name)
            return True
        else:
            return False
    

    def add_dungeon(self, dungeon: Dungeon) -> bool:
        if dungeon.name not in self.dungeons:
            self.dungeons[dungeon.name] = dungeon
            return True
        else:
            return False
    

    def export(self, path: str) -> None:
        lines = []

        for card in self.cards.values():
            lines.append(f"kartya;{card.name};{card.damage};{card.hp};{card.type}")
        
        lines.append("")

        for leader in self.leaders.values():
            lines.append(f"vezer;{leader.name};{leader.damage};{leader.hp};{leader.type}")
        
        lines.append("")

        for dungeon in self.dungeons.values():
            cards = ",".join(card for card in dungeon.cards)
            
            if dungeon.type == "egyszeru":
                lines.append(f"kazamata;{dungeon.type};{dungeon.name};{cards};{dungeon.reward}")
            
            elif dungeon.type == "kis":
                lines.append(f"kazamata;{dungeon.type};{dungeon.name};{cards};{dungeon.leader};{dungeon.reward}")
            
            elif dungeon.type == "nagy":
                lines.append(f"kazamata;{dungeon.type};{dungeon.name};{cards};{dungeon.leader}")

        with open(path, "w", encoding="utf-8") as f:
            f.write("\n".join(lines))


def load_world(path: str) -> bool:
    if not Path(path).is_file():
        return False
     
    with open(path, "r", encoding="utf-8") as f:
        d = json.load(f)
        
    world = World(d["name"])

    for card in d["cards"]:
        card_ = load_card(f"{card}.json")
        if not card_:
            return False
            
        if not world.add_card(card_):
            return False
        
    for leader in d["leaders"]:
        leader_ = load_card(f"{leader}.json")
        if not leader_:
            return False
            
        if not world.add_leader(leader_):
            return False
        
    for dungeon in d["dungeons"]:
        dungeon_ = load_dungeon(f"{dungeon}.json")
        if not dungeon_:
            return False
            
        if not world.add_dungeon(dungeon_):
            return False

    for card in d["card_order"]:
        if card not in world.card_order:
            world.card_order.append(card)
        else:
            return False
        
    for leader in d["leader_order"]:
        if leader not in world.leader_order:
            world.leader_order.append(leader)
        else:
            return False

    return True