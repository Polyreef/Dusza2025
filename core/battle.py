import random

from core import ELEMENT_ORDER


def damage_multiplier(att_type, def_type):
    """
    Típus-alapú szorzó: 2, 1 vagy 0.5.

    ELEMENT_ORDER = ["levego", "fold", "tuz", "viz"]
    - szomszédos: "erős" -> 2x
    - átellenes: "gyenge" -> 0.5x
    - azonos: 1x
    """

    if att_type == def_type:
        return 1
    try:
        i_att = ELEMENT_ORDER.index(att_type)
        i_def = ELEMENT_ORDER.index(def_type)
    except ValueError as e:
        # ismeretlen típus esetén inkább ne módosítsuk
        print(f"Hiba: {e}")
        return 1

    diff = (i_att - i_def) % len(ELEMENT_ORDER)
    if diff == 2:
        return 0.5  # gyenge
    else:
        # minden más különböző típus szomszédos -> erős
        return 2


class BattleResult:
    """
    Harc eredménye.

    - log_lines: a harc naplója
    - outcome: "win" vagy "lose"
    - last_player_attacker_name: a játékos utolsó támadó lapja neve
    """

    def __init__(self, log_lines, outcome, last_player_attacker_name):
        self.log_lines = log_lines
        self.outcome = outcome
        self.last_player_attacker_name = last_player_attacker_name


def run_battle(world, player, dungeon, difficulty=0, rng=None):
    """
    Levezényli a harcot. Visszaad egy BattleResult-ot.

    difficulty: 0..10
        - 0 esetén a sebzések úgy működnek, mint az I. fordulóban.
        - >0 esetén a játékos / kazamata sebzését minden ütésnél
          véletlenszerűen módosítjuk a megadott képletek szerint.

    rng: opcionális random.Random példány, teszteléshez kontrollált.
    """

    if not player.has_deck():
        print("Hiba: Nincs összeállított pakli")
        return

    if rng is None:
        rng = random.Random()

    difficulty = int(difficulty)
    if difficulty < 0:
        difficulty = 0
    if difficulty > 10:
        difficulty = 10

    # Pakli: a játékos gyűjteményéből, az aktuális értékekkel
    player_cards = [player.collection[name] for name in player.deck]
    # Kazamata kártyái a világból
    enemy_cards = dungeon.card_sequence(world)

    # Állapot
    p_index = 0
    e_index = 0
    p_active = None
    e_active = None
    p_hp = 0
    e_hp = 0

    log_lines = []
    log_lines.append(f"harc kezdodik;{dungeon.name}")

    round_no = 1
    last_player_attacker_name = None
    outcome = None

    while True:
        # Kazamata köre
        if e_active is None:
            if e_index >= len(enemy_cards):
                # már nincs több kazamata lap -> játékos nyert
                outcome = "win"
                break

            e_active = enemy_cards[e_index]
            e_index += 1
            e_hp = e_active.health
            log_lines.append(
                f"{round_no}.kor;kazamata;kijatszik;{e_active.name};{e_active.damage};{e_hp};{e_active.element}"
            )
        else:
            # Támad, de csak akkor, ha a játékosnak van (már) aktív lapja
            if p_active is None:
                # ha nincs aktív lap és nincs több a pakliban, akkor a játékos veszített
                if p_index >= len(player_cards):
                    outcome = "lose"
                    break
                # egyébként (pl. a harc legelső körében) ilyenkor nem támad
            else:
                dmg = apply_damage(e_active, p_active, difficulty, rng, is_enemy=True)
                p_hp = max(0, p_hp - dmg)
                log_lines.append(
                    f"{round_no}.kor;kazamata;tamad;{e_active.name};{dmg};{p_active.name};{p_hp}"
                )
                if p_hp <= 0:
                    p_active = None  # a lap elesett

        if outcome is not None:
            break

        # Játékos köre
        if p_active is None:
            if p_index >= len(player_cards):
                outcome = "lose"
                break

            p_active = player_cards[p_index]
            p_index += 1
            p_hp = p_active.health
            log_lines.append(
                f"{round_no}.kor;jatekos;kijatszik;{p_active.name};{p_active.damage};{p_hp};{p_active.element}"
            )
        else:
            if e_active is None:
                # ha nincs aktív kazamata lap
                if e_index >= len(enemy_cards):
                    outcome = "win"
                    last_player_attacker_name = p_active.name
                    break
                # különben a következő kör elején játszik majd ki új lapot a kazamata
            else:
                dmg = apply_damage(p_active, e_active, difficulty, rng, is_enemy=False)
                e_hp = max(0, e_hp - dmg)
                log_lines.append(
                    f"{round_no}.kor;jatekos;tamad;{p_active.name};{dmg};{e_active.name};{e_hp}"
                )
                last_player_attacker_name = p_active.name
                if e_hp <= 0:
                    e_active = None
                    if e_index >= len(enemy_cards):
                        outcome = "win"
                        break

        if outcome is not None:
            break

        round_no += 1

    return BattleResult(log_lines, outcome, last_player_attacker_name)


def apply_damage(att_card, def_card, difficulty, rng, is_enemy):
    """
    Kiszámítja a tényleges sebzést (típus + nehézségi szint figyelembevételével).

    difficulty: 0..10
    is_enemy: True, ha a kazamata üt; False, ha a játékos üt.

    Képletek:
        KazamataSebzes_uj = round(KazamataSebzes * (1 + rnd() * n/10))
        JatekosSebzes_uj  = round( JatekosSebzes * (1 - rnd() * n/20))
    """

    # Típus-szorzó alkalmazása
    mult = damage_multiplier(att_card.element, def_card.element)
    base_damage = att_card.damage
    if mult == 2:
        base_damage *= 2
    elif mult == 0.5:
        base_damage = base_damage // 2

    # Ha nincs nehézség (0), azonnal visszaadjuk
    if difficulty <= 0:
        return base_damage

    # Véletlen módosítás
    rnd = rng.random()  # [0, 1)
    if is_enemy:
        # kazamata
        factor = 1 + rnd * (difficulty / 10.0)
        new_damage = round(base_damage * factor)
    else:
        # játékos
        factor = 1 - rnd * (difficulty / 20.0)
        new_damage = round(base_damage * factor)

    # Biztonsági korlát: minimum 0 sebzés
    if new_damage < 0:
        new_damage = 0

    return new_damage
