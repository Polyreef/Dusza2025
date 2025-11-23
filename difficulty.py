from __future__ import annotations

import random
from math import ceil


def clamp_nonnegative(value: int) -> int:
    return value if value >= 0 else 0


def enemy_damage_with_difficulty(base_damage: int, difficulty: int) -> int:
    """
    Kazamata sebzése a feladatban megadott képlet alapján:
      új = round( alap * (1 + rnd() * n/10) )
    Ha n = 0, akkor nincs módosítás.
    """
    if difficulty <= 0:
        return base_damage

    factor = 1.0 + random.random() * (difficulty / 10.0)
    return max(1, round(base_damage * factor))


def player_damage_with_difficulty(base_damage: int, difficulty: int) -> int:
    """
    Játékos sebzése:
      új = round( alap * (1 - rnd() * n/20) )
    Ha n = 0, nincs módosítás.
    """
    if difficulty <= 0:
        return base_damage

    factor = 1.0 - random.random() * (difficulty / 20.0)
    # extrém esetben akár 0-ra is eshet, de ne legyen negatív
    modified = round(base_damage * factor)
    return clamp_nonnegative(modified)
