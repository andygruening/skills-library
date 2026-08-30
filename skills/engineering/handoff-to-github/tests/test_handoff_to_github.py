#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
import sys
import unittest
from pathlib import Path


SCRIPT_PATH = Path(__file__).resolve().parents[1] / "scripts" / "handoff_to_github.py"


def load_handoff_module():
    spec = importlib.util.spec_from_file_location("handoff_to_github", SCRIPT_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Cannot load {SCRIPT_PATH}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


handoff = load_handoff_module()


class ParseHeadingTasksTest(unittest.TestCase):
    def parse(self, markdown: str):
        return handoff.parse_heading_tasks(
            markdown,
            custom_heading_regex=None,
            max_title_length=120,
        )

    def test_ignores_task_named_document_title(self) -> None:
        markdown = "# Task Templates\n\nReusable task formats live here.\n\n## Notes\n\nNo issues."

        self.assertEqual(self.parse(markdown), [])

    def test_ignores_child_heading_under_non_task_container(self) -> None:
        markdown = "# Non-tasks\n\n## Background\n\nThis is supporting context."

        self.assertEqual(self.parse(markdown), [])

    def test_ignores_child_heading_under_known_issues_section(self) -> None:
        markdown = "# Known issues and risks\n\n## Mitigate outage\n\nOperational notes."

        self.assertEqual(self.parse(markdown), [])

    def test_ignores_unpunctuated_task_number_heading_with_title(self) -> None:
        markdown = "## Task 1 Build export flow\n\nWire the endpoint."

        self.assertEqual(self.parse(markdown), [])

    def test_ignores_unpunctuated_issue_number_heading_with_title(self) -> None:
        markdown = "## Issue #99 Build export flow\n\nWire the endpoint."

        self.assertEqual(self.parse(markdown), [])

    def test_parses_explicit_task_heading(self) -> None:
        tasks = self.parse("## Task 1: Build export flow\n\nWire the endpoint.")

        self.assertEqual(len(tasks), 1)
        self.assertEqual(tasks[0].title, "Build export flow")
        self.assertIn("Wire the endpoint.", tasks[0].body)

    def test_parses_task_number_heading_without_title(self) -> None:
        tasks = self.parse("## Task 1\n\nWire the endpoint.")

        self.assertEqual(len(tasks), 1)
        self.assertEqual(tasks[0].title, "Task 1")

    def test_parses_child_heading_under_task_container(self) -> None:
        tasks = self.parse("## Tasks\n\n### Build export flow\n\nWire the endpoint.")

        self.assertEqual(len(tasks), 1)
        self.assertEqual(tasks[0].title, "Build export flow")

    def test_parses_numbered_heading(self) -> None:
        tasks = self.parse("## 1. Build export flow\n\nWire the endpoint.")

        self.assertEqual(len(tasks), 1)
        self.assertEqual(tasks[0].title, "Build export flow")


if __name__ == "__main__":
    unittest.main()
