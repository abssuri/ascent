"""Command-line entry point for ascent.

Invoked both by ``python -m ascent`` and by the ``ascent`` console script
declared in pyproject.toml.
"""

import argparse

from ascent import __version__


def main() -> None:
    parser = argparse.ArgumentParser(prog="ascent")
    parser.add_argument("--version", action="version", version=__version__)
    parser.parse_args()


if __name__ == "__main__":
    main()
