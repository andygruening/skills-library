#!/usr/bin/env python3
"""Validate every design-architect theme.json file."""

from __future__ import annotations

import importlib.util
import json
import re
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
THEMES_ROOT = ROOT / "themes"
GENERATOR_PATH = ROOT / "scripts" / "generate_components.py"
SCHEMA_PATH = THEMES_ROOT / "theme.schema.json"


def load_generator():
    spec = importlib.util.spec_from_file_location("generate_components", GENERATOR_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Cannot load {GENERATOR_PATH}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def main() -> int:
    generator = load_generator()
    schema = load_schema(SCHEMA_PATH)
    count = 0
    validate_spec(THEMES_ROOT / "SPEC.md")
    for theme_path in sorted(THEMES_ROOT.glob("*.json")):
        if theme_path.name == "theme.schema.json":
            continue
        validate_against_schema(theme_path, schema)
        generator.read_theme(theme_path.stem)
        count += 1

    print(f"Validated {count} theme configuration files and themes/SPEC.md.")
    return 0


def load_schema(path: Path) -> dict[str, object]:
    try:
        schema = json.loads(path.read_text())
    except json.JSONDecodeError as error:
        raise ValueError(f"{path} is not valid JSON: {error}") from error
    if not isinstance(schema, dict):
        raise ValueError(f"{path} must contain a JSON object.")
    return schema


def validate_against_schema(path: Path, schema: dict[str, object]) -> None:
    try:
        document = json.loads(path.read_text())
    except json.JSONDecodeError as error:
        raise ValueError(f"{path} is not valid JSON: {error}") from error

    errors = schema_errors(document, schema, schema)
    if errors:
        preview = "\n  ".join(errors[:8])
        raise ValueError(f"{path} does not match {SCHEMA_PATH.name}:\n  {preview}")


def schema_errors(value: object, schema: object, root_schema: dict[str, object], location: str = "$") -> list[str]:
    """Validate the JSON Schema features used by theme.schema.json without extra dependencies."""
    if isinstance(schema, bool):
        return [] if schema else [f"{location}: value is not permitted"]
    if not isinstance(schema, dict):
        return [f"{location}: invalid schema"]

    if "$ref" in schema:
        reference = schema["$ref"]
        if not isinstance(reference, str) or not reference.startswith("#/"):
            return [f"{location}: unsupported schema reference {reference!r}"]
        target: object = root_schema
        for part in reference.removeprefix("#/").split("/"):
            if not isinstance(target, dict) or part not in target:
                return [f"{location}: unresolved schema reference {reference!r}"]
            target = target[part]
        return schema_errors(value, target, root_schema, location)

    if "allOf" in schema:
        errors: list[str] = []
        for nested in schema["allOf"]:  # type: ignore[index]
            errors.extend(schema_errors(value, nested, root_schema, location))
        if errors:
            return errors

    if "oneOf" in schema:
        matches = sum(not schema_errors(value, nested, root_schema, location) for nested in schema["oneOf"])  # type: ignore[index]
        if matches != 1:
            return [f"{location}: must match exactly one supported theme format (matched {matches})"]

    expected_type = schema.get("type")
    if expected_type and not matches_type(value, expected_type):
        return [f"{location}: expected {expected_type}"]

    if "enum" in schema and value not in schema["enum"]:
        return [f"{location}: expected one of {schema['enum']}"]

    if isinstance(value, str):
        min_length = schema.get("minLength")
        if isinstance(min_length, int) and len(value) < min_length:
            return [f"{location}: must contain at least {min_length} character(s)"]
        pattern = schema.get("pattern")
        if isinstance(pattern, str) and re.search(pattern, value) is None:
            return [f"{location}: does not match required pattern"]

    if isinstance(value, list) and "items" in schema:
        errors: list[str] = []
        for index, item in enumerate(value):
            errors.extend(schema_errors(item, schema["items"], root_schema, f"{location}[{index}]"))
        if errors:
            return errors

    if isinstance(value, dict):
        errors = []
        required = schema.get("required", [])
        if isinstance(required, list):
            for key in required:
                if isinstance(key, str) and key not in value:
                    errors.append(f"{location}: missing required property {key!r}")

        properties = schema.get("properties", {})
        if not isinstance(properties, dict):
            properties = {}
        for key, child in value.items():
            child_location = f"{location}.{key}"
            if key in properties:
                errors.extend(schema_errors(child, properties[key], root_schema, child_location))
                continue
            additional = schema.get("additionalProperties", True)
            if additional is False:
                errors.append(f"{child_location}: unexpected property")
            elif isinstance(additional, dict):
                errors.extend(schema_errors(child, additional, root_schema, child_location))
        if errors:
            return errors

    return []


def matches_type(value: object, expected_type: object) -> bool:
    type_checks = {
        "object": lambda candidate: isinstance(candidate, dict),
        "array": lambda candidate: isinstance(candidate, list),
        "string": lambda candidate: isinstance(candidate, str),
        "integer": lambda candidate: isinstance(candidate, int) and not isinstance(candidate, bool),
        "number": lambda candidate: isinstance(candidate, (int, float)) and not isinstance(candidate, bool),
    }
    if isinstance(expected_type, list):
        return any(matches_type(value, item) for item in expected_type)
    return isinstance(expected_type, str) and expected_type in type_checks and type_checks[expected_type](value)


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
