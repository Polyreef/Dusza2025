# Damareen

A gyűjtögetős fantasy kártyajáték, amelyben **stratégia**, **szerencse** és **képzelet** fonódik össze. A selyemutak játszóasztalaitól a modern digitális arénákig ez a műfaj mindig is a **hősök** és **történetek** kovácsa volt. Most **RAJTAD** (🫵) a sor, hogy saját paklid lapjaira írd a történelmet: **hősöket teremts**, **kazamatákon küzdj végig**, és **szörnyek vezéreivel mérkőzz meg**.

Vajon a gondosan kidolgozott stratégiád diadalt arat, vagy a kazamaták mélye örökre elnyel?

**Készítsd elő a paklidat, mert a kártyák sorsot hordoznak!**

---

## Telepítés

A játék futtatásához **PyGame**-re van szükség.

Telepítsd a Python-t, majd a PyGame és pygame_gui csomagot.

`pip install pygame pygame_gui`

## Használat

A programnak 2 különböző módja van:

- **Teszt mód:** Ebben a módban a játék belső logikája kerül tesztelésre egy `in.txt` fájl alapján.

- **Játék mód:** Ebben a módban lehet magát a játékot használni.

### Teszt mód

Teszt módban futtatáshoz a programot a teszteset mappájával, mint paraméterrel indítjuk el.

Példa parancs: `python main.py test_cases/01`

A futás eredénye ugyanabba a mappába kerül kiíratásra a tesztesetben meghatározott fájlokba.

### Játék mód

Játék módban futtatáshoz a programot a `--ui` paraméterrel indítjuk el.

Példa parancs: `python main.py --ui`

---

#### Lord of the Strings - 2025