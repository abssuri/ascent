"""Command-line entry point for ascent.

Invoked both by ``python -m ascent`` and by the ``ascent`` console script
declared in pyproject.toml.
"""

import argparse

from ascent import __version__


def main() -> None:
    parser = argparse.ArgumentParser(prog="ascent")
    parser.add_argument("--version", action="version", version=__version__)
    parser.add_argument("--seed", type=int, default=0, help="seed for the run")
    args = parser.parse_args()

    # Imported here, not at module top, so `--version` never loads textual.
    from ascent.ui.app import AscentApp

    AscentApp(seed=args.seed).run()


if __name__ == "__main__":
    main()
