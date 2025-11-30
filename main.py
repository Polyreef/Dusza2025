import os
import sys

from run_game import run_game_mode
from run_test import run_test_mode
from run_tool import run_tool_mode


def main():
    """
    Belépési pont.

    - <mappa>  -> teszt mód (in.txt a mappában)
    - --ui     -> játék mód (PySide)
    """

    if len(sys.argv) != 2:
        print("Használat:")
        print("  python main.py <mappa>    # teszt mód (in.txt a mappában)")
        print("  python main.py --ui       # játék mód (PySide)")
        print("  python main.py --tool     # basic mód (PySide)")
        sys.exit(1)

    arg = sys.argv[1]

    if arg == "--ui":
        run_game_mode()
    elif arg == "--tool":
        run_tool_mode()
    else:
        input_dir = arg
        if not os.path.isdir(input_dir):
            print(f"Hiba: a megadott mappa nem létezik: {input_dir}")
            sys.exit(1)

        run_test_mode(input_dir)


if __name__ == "__main__":
    main()
