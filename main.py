import sys

from game.run_game import run_ui_mode
from run_test import run_test_mode


def main() -> None:
    if len(sys.argv) < 2:
        print("Használat:")
        print("  python main.py <teszt_mappa>")
        print("  python main.py --ui")
        return

    arg = sys.argv[1]
    if arg == "--ui":
        run_ui_mode()
    else:
        run_test_mode(arg)


if __name__ == "__main__":
    main()
