"""Entry point for ``python -m trennungsgeld`` providing the quickstart CLI."""
from __future__ import annotations

from .simple_cli import run_simple_cli


def main() -> None:  # pragma: no cover - thin wrapper
    run_simple_cli()


if __name__ == "__main__":  # pragma: no cover - module execution guard
    main()
