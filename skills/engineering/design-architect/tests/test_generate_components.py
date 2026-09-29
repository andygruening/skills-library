#!/usr/bin/env python3
from __future__ import annotations

import copy
import importlib.util
import json
import sys
import unittest
from pathlib import Path


SKILL_ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = SKILL_ROOT / "scripts" / "generate_components.py"


def load_generator_module():
    spec = importlib.util.spec_from_file_location("generate_components", SCRIPT_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Cannot load {SCRIPT_PATH}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


generator = load_generator_module()


class ThemeValidationTest(unittest.TestCase):
    def load_theme(self, name: str) -> dict[str, object]:
        return json.loads((SKILL_ROOT / "themes" / f"{name}.json").read_text())

    def test_rich_theme_must_satisfy_schema_required_fields(self) -> None:
        theme = copy.deepcopy(self.load_theme("oms"))
        del theme["borders"]["focusRingWidth"]

        with self.assertRaisesRegex(ValueError, "focusRingWidth"):
            generator.validate_rich_theme_json(
                theme,
                SKILL_ROOT / "themes" / "oms.json",
                expected_slug="oms",
            )

    def test_checked_in_themes_validate(self) -> None:
        for theme_name in ("light", "dark", "oms"):
            with self.subTest(theme=theme_name):
                generator.read_theme(theme_name)


if __name__ == "__main__":
    unittest.main()
