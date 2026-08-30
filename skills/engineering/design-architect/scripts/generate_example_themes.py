#!/usr/bin/env python3
"""Generate TypeScript theme modules for the example app."""

from __future__ import annotations

import argparse
import difflib
import subprocess
import sys
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
THEMES_DIR = ROOT / "themes"
GENERATOR = ROOT / "scripts" / "generate_components.py"
OUTPUT_DIR = ROOT / "example" / "src" / "generated" / "themes"


def theme_slugs() -> list[str]:
    return sorted(path.stem for path in THEMES_DIR.glob("*.json") if path.name != "theme.schema.json")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--theme",
        action="append",
        choices=theme_slugs(),
        help="Theme slug to generate. Pass multiple times to generate a subset. Defaults to every theme.",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=OUTPUT_DIR,
        help=f"Directory for generated *.gen.ts files. Defaults to {OUTPUT_DIR}.",
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="Print diffs and fail if generated example theme modules are stale.",
    )
    return parser.parse_args()


def render_theme(slug: str) -> str:
    with tempfile.TemporaryDirectory(prefix=f"design-architect-{slug}-") as temp_dir:
        subprocess.run(
            [
                sys.executable,
                str(GENERATOR),
                temp_dir,
                "--platform",
                "typescript",
                "--theme",
                slug,
            ],
            check=True,
        )
        return (Path(temp_dir) / "styling.gen.ts").read_text()


def write_file(path: Path, content: str, check: bool) -> bool:
    normalized = content.rstrip() + "\n"
    if check:
        current = path.read_text() if path.exists() else ""
        if current != normalized:
            print(f"DIFF {path}")
            for line in difflib.unified_diff(
                current.splitlines(),
                normalized.splitlines(),
                fromfile=str(path),
                tofile=f"{path} (generated)",
                lineterm="",
            ):
                print(line)
            return False
        return True

    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(normalized)
    return True


def main() -> int:
    args = parse_args()
    output_dir = args.output_dir
    slugs = args.theme or theme_slugs()
    prune_stale = args.theme is None
    generated_files: set[Path] = set()
    ok = True

    for slug in slugs:
        destination = output_dir / f"{slug}.gen.ts"
        generated_files.add(destination)
        if not write_file(destination, render_theme(slug), args.check):
            ok = False

    if prune_stale and output_dir.exists():
        for path in output_dir.glob("*.gen.ts"):
            if path not in generated_files:
                if args.check:
                    print(f"STALE {path}")
                    ok = False
                else:
                    path.unlink()

    if args.check and not ok:
        return 1

    verb = "Checked" if args.check else "Generated"
    print(f"{verb} {len(generated_files)} example theme modules in {output_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
