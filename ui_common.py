from __future__ import annotations

import os


def clear_screen() -> None:
    os.system("cls" if os.name == "nt" else "clear")


def press_enter(prompt: str = "Továbblépéshez nyomj Entert...") -> None:
    input(prompt)


def input_int(prompt: str, min_value: int | None = None, max_value: int | None = None) -> int:
    while True:
        raw = input(prompt).strip()
        if not raw:
            print("Kérlek, adj meg egy számot!")
            continue
        if not raw.lstrip("-").isdigit():
            print("Kérlek, egész számot adj meg!")
            continue
        value = int(raw)
        if min_value is not None and value < min_value:
            print(f"A szám nem lehet kisebb, mint {min_value}.")
            continue
        if max_value is not None and value > max_value:
            print(f"A szám nem lehet nagyobb, mint {max_value}.")
            continue
        return value


def choose_from_list(items, title: str = "Válassz:", allow_empty: bool = False):
    """
    Általános listaválasztó.
    items: lista, elemei (id, label) vagy csak label-ek lehetnek.
    """
    if not items:
        print("Nincs elérhető elem.")
        return None

    print(title)
    for idx, it in enumerate(items, start=1):
        if isinstance(it, tuple):
            _, label = it
        else:
            label = it
        print(f"{idx}. {label}")

    while True:
        raw = input("Sorszám: ").strip()
        if allow_empty and raw == "":
            return None
        if not raw.isdigit():
            print("Adj meg egy érvényes sorszámot!")
            continue
        idx = int(raw)
        if not (1 <= idx <= len(items)):
            print("Érvénytelen sorszám.")
            continue
        return items[idx - 1]
