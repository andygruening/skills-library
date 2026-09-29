#!/usr/bin/env python3
"""Validate every design-architect theme.json file."""

from __future__ import annotations

import argparse
import importlib.util
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
THEMES_ROOT = ROOT / "themes"
GENERATOR_PATH = ROOT / "scripts" / "generate_components.py"


def load_generator():
    spec = importlib.util.spec_from_file_location("generate_components", GENERATOR_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Cannot load {GENERATOR_PATH}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "themes_dir",
        nargs="?",
        type=Path,
        default=THEMES_ROOT,
        help=f"Directory containing theme JSON files and SPEC.md. Defaults to {THEMES_ROOT}.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    themes_root = args.themes_dir
    if not themes_root.is_dir():
        print(f"error: {themes_root} is missing.", file=sys.stderr)
        return 2

    generator = load_generator()
    generator.THEMES_ROOT = themes_root
    count = 0
    try:
        validate_spec(themes_root / "SPEC.md")
        for theme_path in sorted(themes_root.glob("*.json")):
            if theme_path.name == "theme.schema.json":
                continue
            generator.read_theme(theme_path.stem)
            count += 1
    except ValueError as error:
        print(f"error: {error}", file=sys.stderr)
        return 2

    print(f"Validated {count} theme configuration files and {themes_root / 'SPEC.md'}.")
    return 0


def validate_spec(path: Path) -> None:
    if not path.is_file():
        raise ValueError(f"{path} is missing.")

    lines = path.read_text().splitlines()
    if not lines or lines[0].strip() != "---":
        raise ValueError(f"{path} is missing YAML frontmatter.")

    fields: dict[str, str] = {}
    for line in lines[1:]:
        if line.strip() == "---":
            break
        if ":" not in line:
            continue
        key, value = line.split(":", 1)
        fields[key.strip()] = value.strip().strip("\"'")

    missing = [field for field in ("name", "description") if not fields.get(field)]
    if missing:
        raise ValueError(f"{path} frontmatter is missing: {', '.join(missing)}.")


if __name__ == "__main__":
    raise SystemExit(main())
