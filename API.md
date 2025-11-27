# Játéklogika API

A játéklogika kódja a `core` mappában található.

A függvények többsége 2 féle értéket ad vissza:
- **Értelmes érték**, amikor a függvény hiba nélkül lefut és vissza tudja adni, amit kell.
- **Hibaérték**, amikor a függvény hibába ütközik, egyből visszatér. Ez általában a `False` érték.

Ahol 2 féle értéket vissza tud adni, a függvény deklarációjában benne van, hogy mely típusúak ezek, pl.: `def function() -> Value | Literal[False]`  
Itt `Value` típusú az az érték, amit a hiba nélküli lefutás után ad vissza.  
`Literal[False]` típusú az az érték, amit hiba esetén ad vissza - ergo egy `False` érték.

## Init

Az `__init__.py` fájlban található az `ELEMENT_ORDER` tömb, mely a típusokat tárolja, sorrendben.  
Használata: `from core import ELEMENT_ORDER`.

## Battle

A `battle.py` fájlban található minden, ami a harccal kapcsolatos.  
Használata: `from core.battle import <valami>`.

### `def damage_multiplier(att_type, def_type) -> float`

Típus alapú szorzó.

`att_type: str` - A támadó kártya típusa.  
`def_type: str` - A támadott kártya típusa.

`-> float` - A sebzés szorzóját adja vissza, mely lehet `0.5`, `1`, `2`.

### `class BattleResult`

A harc eredményét tároló osztály.

`log_lines: list[str]` - A harc naplóját tároló lista.  
`outcome: Literal["win", "lose"]` - A harc eredménye, mely vagy `win` vagy `lose`.  
`last_player_attacker_name: str` - A játékos utolsó támadó kártyájának neve.

### `def run_battle(world, player, dungeon, difficulty=0, rng=None) -> BattleResult | Literal[False]`

A harc levezényléséért felelős függvény.

`world: World` - A világ.  
`player: Player` - A játékos.  
`dungeon: Dungeon` - A kazamata.  
`difficulty: int = 0` - A nehézségi szint. Teszt módban `0`.  
`rng: random.Random | None = None` - A random generátor.

`-> BattleResult` - A harc eredményét tároló osztályt adja vissza.

### `def apply_damage(att_card, def_card, difficulty, rng, is_enemy) -> float`

Kiszámítja a tényleges sebzést a típus és nehézségi szint alapján.

`att_card: CardDefinition` - A támadó kártyája.  
`def_card: CardDefinition` - A támadott kártyája.  
`difficulty: int` - A nehézségi szint, `0`-tól `10`-ig.  
`rng: random.Random` - A random generátor.  
`is_enemy: bool` - `True`, ha a kazamata üt; `False`, ha a játékos üt.

`-> float` - A tényleges sebzést adja vissza.

## Environment

Az `environment.py` fájlban található minden, ami a játékkörnyezettel kapcsolatos.  
Használata: `from core.environment import <valami>`.

### `class GameEnvironment`

A játékkörnyezetet tároló és kezelő osztály.

`name: str` - Neve.  
`world: World` - A világ.  
`starting_collection: dict` - A kezdő gyűjtemény.

#### 

## Models

## Storage