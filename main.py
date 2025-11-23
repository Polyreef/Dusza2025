import sys

from test import run_automated_tests


def main() -> None:
    if len(sys.argv) == 1:
        print(f"Használat: python {sys.argv[0]} [--ui | <test_dir_path>]")
        sys.exit(1)

    if sys.argv[1] == "--ui":
        pass
    else:
        run_automated_tests(sys.argv[1])


if __name__ == "__main__":
    main()