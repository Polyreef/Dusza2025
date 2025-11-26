import random

from dataclasses import dataclass
from typing import List, Optional

from .gamestate import GameState
from .models import Card, Dungeon, Player


@dataclass
class BattleCard:
    """
    Egy harcban résztvevő (ideiglenes) lap.
    A gyűjteményben lévő Card objektumot NEM módosítjuk, itt csak a harc közbeni állapotot tároljuk.
    """

    name: str
    base_damage: int
    base_health: int
    element: str
    current_health: int
    owner_side: str  # "kazamata" vagy "jatekos"

    @staticmethod
    def from_card(card: Card, owner_side: str) -> "BattleCard":
        return BattleCard(
            name=card.name,
            base_damage=card.damage,
            base_health=card.health,
            element=card.element,
            current_health=card.health,
            owner_side=owner_side,
        )


@dataclass
class BattleOutcome:
    player_won: bool
    reward_type: Optional[str]  # None nagy kazamatánál
    reward_card: Optional[Card]  # fejlődő vagy új lap
    log_lines: List[str]


# Elem erősségek


def type_multiplier(attacker_element: str, defender_element: str) -> float:
    """
    Elem-erősségi rendszer:

    föld   -> erős levegő és tűz ellen, gyenge víz ellen
    levegő -> erős föld és víz ellen, gyenge tűz ellen
    víz    -> erős levegő és tűz ellen, gyenge föld ellen
    tűz    -> erős víz és föld ellen, gyenge levegő ellen
    """

    strong_map = {
        "fold": {"levego", "tuz"},
        "levego": {"fold", "viz"},
        "viz": {"levego", "tuz"},
        "tuz": {"viz", "fold"},
    }

    weak_map = {
        "fold": {"viz"},
        "levego": {"tuz"},
        "viz": {"fold"},
        "tuz": {"levego"},
    }

    if defender_element in strong_map.get(attacker_element, set()):
        return 2.0
    if defender_element in weak_map.get(attacker_element, set()):
        return 0.5
    return 1.0


# Sebzés számítása nehézséggel


def effective_damage(
    base_damage: int,
    owner_side: str,
    difficulty_level: int,
    random_generator: random.Random,
) -> int:
    """
    Nehézségi szint miatti módosítás.
    Teszt módban difficulty_level = 0, így nem változik semmi.
    """

    if difficulty_level <= 0:
        return base_damage

    if owner_side == "kazamata":
        # kazamataSebzesUj = round( base * (1 + rnd() * n/10) )
        factor = 1.0 + random_generator.random() * (difficulty_level / 10.0)
    else:
        # jatekosSebzesUj = round( base * (1 - rnd() * n/20) )
        factor = 1.0 - random_generator.random() * (difficulty_level / 20.0)

    damage = round(base_damage * factor)
    return max(0, damage)


def perform_attack(
    attacker_card: BattleCard,
    defender_card: BattleCard,
    difficulty_level: int,
    random_generator: random.Random,
) -> int:
    """
    Egy támadás lejátszása, visszaadja a tényleges sebzést.
    """

    damage = effective_damage(
        attacker_card.base_damage,
        attacker_card.owner_side,
        difficulty_level,
        random_generator,
    )
    multiplier = type_multiplier(attacker_card.element, defender_card.element)
    if multiplier == 2.0:
        damage *= 2
    elif multiplier == 0.5:
        damage = damage // 2  # lefelé kerekítés

    defender_card.current_health -= damage
    if defender_card.current_health < 0:
        defender_card.current_health = 0
    return damage


# Sorok felépítése


def build_enemy_line(world, dungeon: Dungeon) -> List[BattleCard]:
    """
    Kazamata oldalának felépítése a világ kártyáiból.
    """

    result: List[BattleCard] = []
    for name in dungeon.simple_cards:
        base_card = world.simple_cards[name]
        result.append(BattleCard.from_card(base_card, owner_side="kazamata"))

    if dungeon.leader_name:
        base_card = world.leaders[dungeon.leader_name]
        result.append(BattleCard.from_card(base_card, owner_side="kazamata"))

    return result


def build_player_line(player: Player) -> List[BattleCard]:
    """
    Játékos oldalának felépítése a pakliból.
    """

    result: List[BattleCard] = []
    for name in player.deck:
        base_card = player.collection[name]
        result.append(BattleCard.from_card(base_card, owner_side="jatekos"))
    return result


# Fő harc függvény


def run_battle(
    game: GameState,
    dungeon_name: str,
    difficulty_level: Optional[int] = None,
    random_generator: Optional[random.Random] = None,
) -> BattleOutcome:
    """
    Egy teljes harc lejátszása. A napló sorait és az eredményt adja vissza.

    difficulty_level:
        - ha None: a game.difficulty értéket használjuk
        - ha szám: azt használjuk (0 teszt módban, 0..10 játék módban).
    """

    if random_generator is None:
        random_generator = random.Random()

    if difficulty_level is None:
        difficulty_level = game.difficulty

    world = game.world
    player = game.player
    dungeon = world.dungeons[dungeon_name]

    enemy_line = build_enemy_line(world, dungeon)
    player_line = build_player_line(player)

    log_lines: List[str] = [f"harc kezdodik;{dungeon.name}"]

    # Ha bármelyik oldalnak nincs lapja, a játékos veszít.
    if not enemy_line or not player_line:
        return BattleOutcome(False, None, None, log_lines)

    enemy_index = 0
    player_index = 0
    enemy_current: Optional[BattleCard] = None
    player_current: Optional[BattleCard] = None

    round_number = 1
    last_attacking_player_card_name: Optional[str] = None

    while True:
        # Kazamata akció
        if enemy_current is None:
            if enemy_index >= len(enemy_line):
                # Nincs több kazamata lap -> játékos nyert
                break
            enemy_current = enemy_line[enemy_index]
            enemy_index += 1
            log_lines.append(
                f"{round_number}.kor;kazamata;kijatszik;"
                f"{enemy_current.name};{enemy_current.base_damage};"
                f"{enemy_current.base_health};{enemy_current.element}"
            )
        else:
            if player_current is None and player_index < len(player_line):
                # Nincs még kint játékos lap, de lesz - majd a saját körében kijátssza.
                pass
            elif player_current is None and player_index >= len(player_line):
                # Nincs több játékos lap -> játékos vesztett.
                break
            else:
                damage = perform_attack(
                    enemy_current,
                    player_current,
                    difficulty_level,
                    random_generator,
                )
                log_lines.append(
                    f"{round_number}.kor;kazamata;tamad;"
                    f"{enemy_current.name};{damage};"
                    f"{player_current.name};{player_current.current_health}"
                )
                if player_current.current_health == 0:
                    player_current = None
                    if player_index >= len(player_line):
                        # Utolsó játékos lap is meghalt
                        break

        # Játékos akció
        enemy_alive_exists = enemy_current is not None or enemy_index < len(enemy_line)
        if not enemy_alive_exists:
            # Nincs több kazamata lap -> játékos nyert
            break

        if player_current is None:
            if player_index >= len(player_line):
                # Nincs több játékos lap -> játékos vesztett.
                break

            player_current = player_line[player_index]
            player_index += 1
            log_lines.append(
                f"{round_number}.kor;jatekos;kijatszik;"
                f"{player_current.name};{player_current.base_damage};"
                f"{player_current.base_health};{player_current.element}"
            )
        else:
            damage = perform_attack(
                player_current,
                enemy_current,
                difficulty_level,
                random_generator,
            )
            log_lines.append(
                f"{round_number}.kor;jatekos;tamad;"
                f"{player_current.name};{damage};"
                f"{enemy_current.name};{enemy_current.current_health}"
            )
            last_attacking_player_card_name = player_current.name
            if enemy_current.current_health == 0:
                enemy_current = None
                if enemy_index >= len(enemy_line):
                    # Utolsó kazamata lap is meghalt
                    break

        round_number += 1

    # Eredmény és jutalom
    player_has_cards = (player_current is not None) or (player_index < len(player_line))
    enemy_has_cards = (enemy_current is not None) or (enemy_index < len(enemy_line))

    player_won = player_has_cards and not enemy_has_cards
    reward_type: Optional[str] = None
    reward_card: Optional[Card] = None

    if player_won:
        # Egyszerű / kis kazamata: utolsó támadó játékos lap fejlődik.
        if dungeon.dungeon_type in ("egyszeru", "kis"):
            reward_type = dungeon.reward
            if last_attacking_player_card_name is not None and reward_type is not None:
                original = player.collection.get(last_attacking_player_card_name)
                if original is not None:
                    if reward_type == "sebzes":
                        original.damage += 1
                    elif reward_type == "eletero":
                        original.health += 2
                    reward_card = original

            if reward_type == "sebzes" and reward_card is not None:
                log_lines.append(f"jatekos nyert;sebzes;{reward_card.name}")
            elif reward_type == "eletero" and reward_card is not None:
                log_lines.append(f"jatekos nyert;eletero;{reward_card.name}")
            else:
                # Biztonsági fallback, ha valamiért nincs reward_card
                log_lines.append("jatekos nyert")
        else:
            # Nagy kazamata - új sima kártya jár, ha van még.
            new_card = game.world.first_missing_simple_card_for_player(game.player)
            if new_card is not None:
                game.player.add_to_collection(new_card)
                reward_card = new_card
                log_lines.append(f"jatekos nyert;{new_card.name}")
            else:
                log_lines.append("jatekos nyert")
    else:
        log_lines.append("jatekos vesztett")

    return BattleOutcome(player_won, reward_type, reward_card, log_lines)
