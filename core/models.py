class CardDefinition:
    """
    Egy kártya típust ír le (név, sebzés, életerő, típus).

    Teszt módban ez közvetlenül megfelel az I. forduló világkártyáinak.
    """

    def __init__(self, name, damage, health, element):
        self.name = name
        self.damage = int(damage)
        self.health = int(health)
        self.element = element  # "fold", "levego", "viz", "tuz"

    def copy(self):
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
        self, name, kind, simple_card_names, leader_name=None, reward_type=None
    ):
        self.name = name
        self.kind = kind
        self.simple_card_names = list(simple_card_names)
        self.leader_name = leader_name
        self.reward_type = reward_type

    def card_sequence(self, world):
        """
        Visszaadja a kazamata kártyáit CardDefinition listaként, a világ alapján.
        """

        cards = []
        for name in self.simple_card_names:
            simple_card = world.get_simple_card(name)
            if simple_card == -1:
                print("Hiba a sima kártya lekérdezésénél.")
                return -1

            cards.append(simple_card)
        
        if self.leader_name:
            leader_card = world.get_leader_card(self.leader_name)
            if leader_card == -1:
                print("Hiba a vezérkártya lekérdezésénél.")
                return -1
            
            cards.append(leader_card)
        
        return cards


class World:
    """
    A világ: sima kártyák, vezérkártyák, kazamaták.

    A sima kártyák és vezérek nevei egyediek a világon belül.
    """

    def __init__(self):
        self.simple_cards = {}  # név -> CardDefinition
        self.leader_cards = {}  # név -> CardDefinition
        self.dungeons = {}  # név -> Dungeon
        # dict-ek beillesztési sorrendje megmarad (jó exporthoz/mentéshez)

    # Kártyák hozzáadása

    def add_simple_card(self, name, damage, health, element):
        if name in self.simple_cards or name in self.leader_cards:
            print(f"Már létezik ilyen nevű kártya: {name}")
            return -1

        self.simple_cards[name] = CardDefinition(name, damage, health, element)

    def add_leader_card(self, name, base_card_name, mode):
        """
        Vezérkártya hozzáadása.

        mode:
            - 'sebzes':  dupla sebzés
            - 'eletero': dupla életerő
        """

        if name in self.simple_cards or name in self.leader_cards:
            print(f"Már létezik ilyen nevű kártya: {name}")
            return -1

        base = self.get_simple_card(base_card_name)
        if base == -1:
            print("Hiba a sima kártya lekérdezésével.")
            return -1

        if mode == "sebzes":
            damage = base.damage * 2
            health = base.health
        elif mode == "eletero":
            damage = base.damage
            health = base.health * 2
        else:
            print(f"Ismeretlen vezér mod: {mode}")
            return -1

        self.leader_cards[name] = CardDefinition(name, damage, health, base.element)

    # Kazamata kezelés

    def add_dungeon(self, dungeon):
        if dungeon.name in self.dungeons:
            print(f"Már létezik ilyen nevű kazamata: {dungeon.name}")
            return -1

        self.dungeons[dungeon.name] = dungeon

    # Lekérdezések

    def get_simple_card(self, name):
        try:
            return self.simple_cards[name]
        except KeyError:
            print(f"Ismeretlen sima kártya: {name}")
            return -1

    def get_leader_card(self, name):
        try:
            return self.leader_cards[name]
        except KeyError:
            print(f"Ismeretlen vezér kártya: {name}")
            return -1

    def get_dungeon(self, name):
        try:
            return self.dungeons[name]
        except KeyError:
            print(f"Ismeretlen kazamata: {name}")
            return -1

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

    def add_card_from_world(self, world, card_name):
        """
        Sima kártyát ad a gyűjteményhez a világból, ha még nincs benne.

        True-t ad vissza, ha új kártya került be, False-t, ha már benne volt.
        """

        if card_name in self.collection:
            return False

        base = world.get_simple_card(card_name)
        if base == -1:
            print("Hiba a sima kártya lekérdezésével.")
            return -1
        
        self.collection[card_name] = base.copy()

        return True

    # Pakli kezelése

    def max_deck_size(self):
        """
        A pakli maximális mérete: a gyűjtemény fele felfelé kerekítve.
        """

        n = len(self.collection)
        return (n + 1) // 2

    def set_deck(self, card_names):
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
            return -1

        self.deck = unique

    def has_deck(self):
        return bool(self.deck)


class GameState:
    """
    Játékos állapot egy adott játékkörnyezetben, nehézségi szinttel.

    Ez az, amit menteni/betölteni kell:
      - player (gyűjtemény + aktuális pakli)
      - difficulty (0..10)
      - environment_name (honnan indult a játék)
    """

    def __init__(self, player, difficulty, environment_name=None):
        self.player = player
        self.difficulty = int(difficulty)

        if self.difficulty < 0:
            self.difficulty = 0
        if self.difficulty > 10:
            self.difficulty = 10

        self.environment_name = environment_name
