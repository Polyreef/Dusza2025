"""
Damareen játéklogika csomag.

- models: alap adatszerkezetek (kártyák, világ, kazamaták, játékos)
- battle: harcrendszer (nehézségi szint támogatással)
- environment: játékkörnyezet (világ + kezdő gyűjtemény) és új játék
- storage: mentés / betöltés JSON alapokon
- testmode: teszt mód implementáció

Hibánál MINDIG -1 értéket ad vissza, de nem minden funkciónál van hibalehetőség.
"""

# Típusok erősségeihez tömb.
ELEMENT_ORDER = ["levego", "fold", "tuz", "viz"]
