import random


def clamp_nonnegative(value: int) -> int:
    return value if value >= 0 else 0


def enemy_damage_with_difficulty(base_damage: int, difficulty: int) -> int:
    if difficulty <= 0:
        return base_damage

    factor = 1.0 + random.random() * (difficulty / 10.0)
    return max(1, round(base_damage * factor))


def player_damage_with_difficulty(base_damage: int, difficulty: int) -> int:
    if difficulty <= 0:
        return base_damage

    factor = 1.0 - random.random() * (difficulty / 20.0)
    modified = round(base_damage * factor)
    return clamp_nonnegative(modified)