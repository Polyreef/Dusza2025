from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional, Tuple

from card import adjusted_damage, CardTemplate
from world import World
from dungeon import Dungeon
from player import PlayerState, PlayerCard
from difficulty import enemy_damage_with_difficulty, player_damage_with_difficulty


@dataclass
class ActiveCard:
    """
    Jelenleg pályán lévő kártya (aktuális életerővel).
    """
    name: str
    damage: int
    max_hp: int
    type: str
    current_hp: int

    @classmethod
    def from_template(cls, tmpl: CardTemplate) -> "ActiveCard":
        return cls(tmpl.name, tmpl.damage, tmpl.hp, tmpl.type, tmpl.hp)

    @classmethod
    def from_playercard(cls, pc: PlayerCard) -> "ActiveCard":
        return cls(pc.name, pc.damage, pc.hp, pc.type, pc.hp)


def simulate_battle(
    world: World,
    player: PlayerState,
    dungeon: Dungeon,
    deck: List[str],
    difficulty: int = 0,
) -> Tuple[List[str], str, Optional[Tuple]]:
    """
    Harc szimulációja.

    Visszatér:
      - log_sorok: List[str]
      - eredmény: "jatekos" vagy "kazamata"
      - extra:
          ha játékos nyert egyszerű/kis kazamatán:
             ("upgrade", "sebzes"/"eletero", card_name)
          ha játékos nyert nagy kazamatán:
             ("newcard", new_card_name or None)
          ha a kazamata nyer:
             None
    A játékos gyűjteményét módosítja a jutalom alapján.
    """
    log: List[str] = [f"harc kezdodik;{dungeon.name}"]

    # ellenfél lapjai
    enemy_templates: List[CardTemplate] = [world.get_template(n) for n in dungeon.enemy_sima]
    if dungeon.leader is not None:
        enemy_templates.append(world.get_template(dungeon.leader))

    if not deck:
        # üres pakli = azonnali vereség
        log.append("jatekos vesztett")
        return log, "kazamata", None

    player_queue = list(deck)
    enemy_index = 0
    player_index = 0
    enemy_active: Optional[ActiveCard] = None
    player_active: Optional[ActiveCard] = None

    round_no = 1
    result: Optional[str] = None
    last_attacking_player_card: Optional[str] = None

    while result is None:
        # --- kazamata akció ---
        if enemy_active is None:
            if enemy_index >= len(enemy_templates):
                result = "jatekos"
                break
            enemy_active = ActiveCard.from_template(enemy_templates[enemy_index])
            enemy_index += 1
            log.append(
                f"{round_no}.kor;kazamata;kijatszik;"
                f"{enemy_active.name};{enemy_active.damage};{enemy_active.max_hp};{enemy_active.type}"
            )
        else:
            if player_active is None:
                # nincs aktív játékos lap, de még esetleg van a pakliban – a saját fázisában játssza ki
                if player_index >= len(player_queue):
                    result = "kazamata"
                    break
                # most nem tud védekezni -> ebben a körben nem támad a kazamata, a következőben már lesz lap
            else:
                # kazamata támadja a játékos aktív lapját
                base = adjusted_damage(enemy_active.type, player_active.type, enemy_active.damage)
                dmg = enemy_damage_with_difficulty(base, difficulty)
                player_active.current_hp -= dmg
                if player_active.current_hp < 0:
                    player_active.current_hp = 0
                log.append(
                    f"{round_no}.kor;kazamata;tamad;"
                    f"{enemy_active.name};{dmg};{player_active.name};{player_active.current_hp}"
                )
                if player_active.current_hp == 0:
                    if player_index >= len(player_queue):
                        result = "kazamata"
                        break
                    else:
                        player_active = None

        if result is not None:
            break

        # --- játékos akció ---
        if player_active is None:
            if player_index >= len(player_queue):
                result = "kazamata"
                break
            name = player_queue[player_index]
            player_index += 1
            pc = player.collection[name]
            player_active = ActiveCard.from_playercard(pc)
            log.append(
                f"{round_no}.kor;jatekos;kijatszik;"
                f"{player_active.name};{player_active.damage};{player_active.max_hp};{player_active.type}"
            )
        else:
            if enemy_active is None:
                result = "jatekos"
                break
            base = adjusted_damage(player_active.type, enemy_active.type, player_active.damage)
            dmg = player_damage_with_difficulty(base, difficulty)
            enemy_active.current_hp -= dmg
            if enemy_active.current_hp < 0:
                enemy_active.current_hp = 0
            log.append(
                f"{round_no}.kor;jatekos;tamad;"
                f"{player_active.name};{dmg};{enemy_active.name};{enemy_active.current_hp}"
            )
            last_attacking_player_card = player_active.name
            if enemy_active.current_hp == 0:
                if enemy_index >= len(enemy_templates):
                    result = "jatekos"
                    break
                else:
                    enemy_active = None

        round_no += 1

    extra: Optional[Tuple] = None

    if result == "kazamata":
        log.append("jatekos vesztett")
    else:
        # jutalom
        if dungeon.kind in ("egyszeru", "kis"):
            if last_attacking_player_card is None:
                log.append("jatekos nyert")
            else:
                pc = player.collection[last_attacking_player_card]
                if dungeon.reward_type == "sebzes":
                    pc.damage += 1
                    log.append(f"jatekos nyert;sebzes;{pc.name}")
                    extra = ("upgrade", "sebzes", pc.name)
                elif dungeon.reward_type == "eletero":
                    pc.hp += 2
                    log.append(f"jatekos nyert;eletero;{pc.name}")
                    extra = ("upgrade", "eletero", pc.name)
                else:
                    log.append("jatekos nyert")
        else:
            # nagy kazamata -> új világbeli kártya, ami még nincs a gyűjteményben
            new_name: Optional[str] = None
            for cname in world.card_order:
                if cname not in player.collection:
                    new_name = cname
                    break
            if new_name is not None:
                tmpl = world.cards[new_name]
                player.collection[new_name] = PlayerCard(tmpl.name, tmpl.damage, tmpl.hp, tmpl.type)
                player.collection_order.append(new_name)
                log.append(f"jatekos nyert;{new_name}")
                extra = ("newcard", new_name)
            else:
                log.append("jatekos nyert")
                extra = ("newcard", None)

    return log, result or "kazamata", extra
