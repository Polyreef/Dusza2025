from __future__ import annotations

from dataclasses import dataclass
from typing import Set, FrozenSet

# A kártyák típusa – a feladatkiírás szerinti négy elem
CARD_TYPES = ["fold", "levego", "viz", "tuz"]

# Erős / gyenge kapcsolatok a feladat szerinti diagram alapján.
# erős: szomszédos csúcsok, gyenge: ellentétes csúcsok
STRONG_PAIRS: Set[FrozenSet[str]] = {
    frozenset(("levego", "fold")),
    frozenset(("levego", "viz")),
    frozenset(("tuz", "fold")),
    frozenset(("tuz", "viz")),
}

WEAK_PAIRS: Set[FrozenSet[str]] = {
    frozenset(("levego", "tuz")),
    frozenset(("fold", "viz")),
}


@dataclass
class CardTemplate:
    """
    Világbeli (alap) kártya vagy vezér definíciója.
    Ezek nem változnak játék közben, csak a játékos saját példányai.
    """
    name: str
    damage: int
    hp: int
    type: str  # fold, levego, viz, tuz


def adjusted_damage(att_type: str, def_type: str, base_damage: int) -> int:
    """
    Típus alapú sebzésmódosítás (erős/gyenge ugyanúgy, mint az I. fordulóban).
    Teszt módban és játék módban is ez az "alap" sebzés, erre jön rá a nehézségi szint
    szerinti szórás (csak játék módban).
    """
    if att_type == def_type:
        return base_damage

    pair = frozenset((att_type, def_type))

    if pair in STRONG_PAIRS:
        return base_damage * 2
    if pair in WEAK_PAIRS:
        return base_damage // 2

    return base_damage
