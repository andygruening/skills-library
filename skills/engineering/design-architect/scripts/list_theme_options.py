#!/usr/bin/env python3
"""List design-architect theme configurations."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
THEMES_ROOT = ROOT / "themes"


def read_theme(path: Path) -> dict[str, str]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as error:
        raise ValueError(f"{path} is not valid JSON: {error}") from error

    if not isinstance(data, dict):
        raise ValueError(f"{path} must contain a JSON object")
    return data


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "themes_dir",
        nargs="?",
        type=Path,
        default=THEMES_ROOT,
        help=f"Directory containing theme JSON files. Defaults to {THEMES_ROOT}.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    themes_root = args.themes_dir
    if not themes_root.is_dir():
        print(f"Themes directory not found: {themes_root}", file=sys.stderr)
        return 1

    rows: list[tuple[str, str]] = []
    for theme_path in sorted(themes_root.glob("*.json")):
        if theme_path.name == "theme.schema.json":
            continue
        try:
            theme = read_theme(theme_path)
        except ValueError as error:
            print(error, file=sys.stderr)
            return 1

        name = str(theme.get("name", "")).strip()
        description = str(theme.get("description", "")).strip()
        if not name or not description:
            print(f"{theme_path} must define name and description", file=sys.stderr)
            return 1
        rows.append((name, description))

    for name, description in rows:
        print(f"{name}: {description}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
