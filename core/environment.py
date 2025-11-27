from core.models import Player, GameState, World


class GameEnvironment:
    """
    Játékkörnyezet: világ + kezdő játékos gyűjtemény.

      - Játékmester hozza létre a világot (sima kártyák, vezérek, kazamaták),
      - valamint egy kezdő gyűjteményt.
      - Ezeket együtt kell tudni menteni / betölteni (storage modul).

    Az environment neve tetszőleges.
    """

    def __init__(self, name: str, world: World, starting_collection: dict):
        """
        starting_collection: név -> CardDefinition (Player.collection formátumban)
        """

        self.name = name
        self.world = world
        self.starting_collection = starting_collection  # dict

    @staticmethod
    def from_world_and_player(name: str, world: World, player: Player):
        """
        Segédfüggvény: már létező világ + játékos gyűjtemény alapján
        épít egy játékkörnyezetet.
        """

        # másolat, hogy ne legyen közvetlen összekapcsolva
        starting_collection = {}
        for card in player.collection.values():
            starting_collection[card.name] = card.copy()

        return GameEnvironment(name, world, starting_collection)

    def new_game(self, difficulty) -> GameState:
        """
        Új játék indítása az adott környezet alapján.

        - létrejön egy új Player
        - a starting_collection másolatát kapja meg
        - még NINCS paklija, azt később kell beállítani
        - visszaad egy GameState-et
        """

        new_player = Player()
        for card in self.starting_collection.values():
            new_player.collection[card.name] = card.copy()

        # pakli üresen hagyva
        return GameState(new_player, difficulty, environment_name=self.name)
