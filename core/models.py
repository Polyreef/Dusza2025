from typing import Literal

from core import ELEMENT_ORDER


class CardDefinition:
    """
    Egy kártya típust ír le (név, sebzés, életerő, típus).

    Teszt módban ez közvetlenül megfelel az I. forduló világkártyáinak.
    """

    def __init__(self, name: str, damage: int, health: int, element: str):
        self.name = name.strip()
        self.damage = int(damage)
        self.health = int(health)
        self.element = element.strip().lower()  # "fold", "levego", "viz", "tuz"

        if len(self.name) == 0 or len(self.name) > 16:
            raise ValueError(f"Érvénytelen kártyanév (max 16 karakter): {self.name}")

        if self.damage < 2 or self.damage > 100:
            raise ValueError(f"Érvénytelen sebzés (2..100): {self.name}")

        if self.health < 1 or self.health > 100:
            raise ValueError(f"Érvénytelen életerő (1..100): {self.name}")

        if self.element not in ELEMENT_ORDER:
            raise ValueError(f"Érvénytelen típus: {self.element}")

    def copy(self) -> "CardDefinition":
        """Új, azonos értékű példányt ad vissza."""

        return CardDefinition(self.name, self.damage, self.health, self.element)


class Dungeon:
    """
    Kazamata definíciója.

    kind:
        - "egyszeru"
        - "kis"
        - "nagy"

    simple_card_names: a benne lévő sima kártyák nevei, sorrendben
    leader_name: vezérkártya neve (kis/nagy kazamatáknál)
    reward_type:
        - egyszeru/kis: "sebzes" vagy "eletero"
        - nagy: None
    """

    def __init__(
        self,
        name: str,
        kind: str,
        simple_card_names: list,
        leader_name: str | None = None,
        reward_type: str | None = None,
    ):
        self.name = name.strip()
        self.kind = kind.strip().lower()
        self.simple_card_names = list(simple_card_names)
        self.leader_name = (
            leader_name.strip() if leader_name is not None else leader_name
        )
        self.reward_type = (
            reward_type.strip().lower() if reward_type is not None else reward_type
        )

        if len(self.name) == 0 or len(self.name) > 20:
            raise ValueError(f"Érvénytelen kazamatanév (max 20 karakter): {self.name}")

    def card_sequence(self, world: "World") -> list | Literal[False]:
        """
        Visszaadja a kazamata kártyáit CardDefinition listaként, a világ alapján.
        """

        cards = []
        for name in self.simple_card_names:
            c = world.get_simple_card(name)
            if c == -1:
                return False

            cards.append(c)

        if self.leader_name:
            v = world.get_leader_card(self.leader_name)
            if v == -1:
                return False

            cards.append(v)

        return cards


class World:
    """
    A világ: sima kártyák, vezérkártyák, kazamaták.

    A sima kártyák és vezérek nevei egyediek a világon belül.
    """

    def __init__(self):
        self.simple_cards = {}  # név -> CardDefinition
        self.simple_styles = {}  # név -> 1 - 4
        self.leader_cards = {}  # név -> CardDefinition
        self.leader_styles = {}  # név -> 1 - 2
        self.dungeons = {}  # név -> Dungeon
        # dict-ek beillesztési sorrendje megmarad (jó exporthoz/mentéshez)

    # Kártyák hozzáadása

    def add_simple_card(
        self, name: str, damage: int, health: int, element: str, style: int = 1
    ) -> Literal[True] | Literal[False]:
        name = name.strip()
        element = element.strip().lower()

        if name in self.simple_cards or name in self.leader_cards:
            print(f"Már létezik ilyen nevű kártya: {name}")
            return False

        if style < 1 or style > 4:
            print(f"Érvénytelen kártya stílus: {style}")
            return False

        try:
            self.simple_cards[name] = CardDefinition(name, damage, health, element)
        except ValueError as e:
            print(str(e))
            return False

        self.simple_styles[name] = style

        return True

    def add_leader_card(
        self, name: str, base_card_name: str, mode: str, style: int = 1
    ) -> Literal[True] | Literal[False]:
        """
        Vezérkártya hozzáadása.

        mode:
            - 'sebzes':  dupla sebzés
            - 'eletero': dupla életerő
        """

        name = name.strip()
        mode = mode.lower()

        if name in self.simple_cards or name in self.leader_cards:
            print(f"Már létezik ilyen nevű kártya: {name}")
            return False

        if style < 1 or style > 2:
            print(f"Érvénytelen vezérkártya stílus: {style}")
            return False

        base = self.get_simple_card(base_card_name)
        if not base:
            return False

        if mode == "sebzes":
            damage = base.damage * 2
            health = base.health
        elif mode == "eletero":
            damage = base.damage
            health = base.health * 2
        else:
            print(f"Ismeretlen vezér mod: {mode}")
            return False

        try:
            self.leader_cards[name] = CardDefinition(name, damage, health, base.element)
        except ValueError as e:
            print(str(e))
            return False

        self.leader_styles[name] = style

        return True

    # Kazamata kezelés

    def add_dungeon(self, dungeon: Dungeon) -> Literal[True] | Literal[False]:
        dungeon.name = dungeon.name.strip()
        if dungeon.name in self.dungeons:
            print(f"Már létezik ilyen nevű kazamata: {dungeon.name}")
            return False

        self.dungeons[dungeon.name] = dungeon

        return True

    # Lekérdezések

    def get_simple_card(self, name: str) -> CardDefinition | Literal[False]:
        try:
            return self.simple_cards[name]
        except KeyError:
            print(f"Ismeretlen sima kártya: {name}")
            return False

    def get_leader_card(self, name: str) -> CardDefinition | Literal[False]:
        try:
            return self.leader_cards[name]
        except KeyError:
            print(f"Ismeretlen vezér kártya: {name}")
            return False

    def get_dungeon(self, name: str) -> Dungeon | Literal[False]:
        try:
            return self.dungeons[name]
        except KeyError:
            print(f"Ismeretlen kazamata: {name}")
            return False

    # Iterátorok (export / mentés megkönnyítésére)

    def iter_simple_cards(self):
        return self.simple_cards.values()

    def iter_leader_cards(self):
        return self.leader_cards.values()

    def iter_dungeons(self):
        return self.dungeons.values()


class Player:
    """
    Játékos: gyűjtemény + aktuális pakli.

    - collection: név -> CardDefinition (ezek módosulhatnak a nyeremények hatására)
    - deck: kártyanevek listája, sorrendben
    """

    def __init__(self):
        self.collection = {}
        self.deck = []

    # Gyűjtemény kezelése

    def add_card_from_world(
        self, world: World, card_name: str
    ) -> Literal[True] | Literal[False]:
        """
        Sima kártyát ad a gyűjteményhez a világból, ha még nincs benne.

        True-t ad vissza, ha új kártya került be, False-t, ha már benne volt.
        """

        if card_name in self.collection:
            return False

        base = world.get_simple_card(card_name)
        if not base:
            return False

        self.collection[card_name] = base.copy()

        return True

    # Pakli kezelése

    def max_deck_size(self) -> int:
        """
        A pakli maximális mérete: a gyűjtemény fele felfelé kerekítve.
        """

        n = len(self.collection)
        return (n + 1) // 2

    def set_deck(self, card_names: list) -> Literal[True] | Literal[False]:
        """
        Pakli beállítása.

        Csak a gyűjteményben lévő és egyedi neveket vesszük figyelembe,
        és maximum a gyűjtemény felét (felfelé kerekítve).
        """

        unique = []
        seen = set()
        for name in card_names:
            if name not in self.collection:
                print(f"Kártya nincs a gyűjteményben: {name}")
                # egyszerű hibatűrés: kihagyjuk
                continue

            if name in seen:
                print(f"Kártya már van a gyűjteményben: {name}")
                continue

            seen.add(name)
            unique.append(name)
            if len(unique) >= self.max_deck_size():
                break

        if not unique:
            print("A pakli üres vagy nem tartalmaz érvényes lapot.")
            return False

        self.deck = unique

        return True

    def has_deck(self) -> bool:
        return bool(self.deck)


class State:
    """
    Játékos állapot egy adott játékkörnyezetben, nehézségi szinttel.

    Ez az, amit menteni/betölteni kell:
      - player (gyűjtemény + aktuális pakli)
      - difficulty (0..10)
      - environment_name (honnan indult a játék)
    """

    def __init__(
        self, player: Player, difficulty: int, environment_name: str | None = None
    ):
        self.player = player
        self.difficulty = int(difficulty)

        if self.difficulty < 0:
            self.difficulty = 0
        if self.difficulty > 10:
            self.difficulty = 10

        self.environment_name = environment_name
