#!/usr/bin/env python3
"""Generate TypeScript theme modules for the example app."""

from __future__ import annotations

import shutil
import subprocess
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
THEMES_DIR = ROOT / "themes"
GENERATOR = ROOT / "scripts" / "generate_components.py"
OUTPUT_DIR = ROOT / "example" / "src" / "generated" / "themes"


def theme_slugs() -> list[str]:
    return sorted(path.stem for path in THEMES_DIR.glob("*.json") if path.name != "theme.schema.json")


def main() -> int:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    generated_files: set[Path] = set()

    for slug in theme_slugs():
        with tempfile.TemporaryDirectory(prefix=f"design-architect-{slug}-") as temp_dir:
            subprocess.run(
                [
                    "python3",
                    str(GENERATOR),
                    temp_dir,
                    "--platform",
                    "typescript",
                    "--theme",
                    slug,
                ],
                check=True,
            )
            destination = OUTPUT_DIR / f"{slug}.gen.ts"
            shutil.copyfile(Path(temp_dir) / "styling.gen.ts", destination)
            generated_files.add(destination)

    for path in OUTPUT_DIR.glob("*.gen.ts"):
        if path not in generated_files:
            path.unlink()

    print(f"Generated {len(generated_files)} example theme modules in {OUTPUT_DIR}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
