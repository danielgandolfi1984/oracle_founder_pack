#!/usr/bin/env python3
"""Validate plugin.json against the vendored Agent Plugins 1.0.0 schema.

The published schema uses a deliberately small JSON Schema vocabulary. This
dependency-free validator implements every assertion keyword present in the
vendored snapshot and fails if an unsupported assertion keyword is introduced.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_SCHEMA = ROOT / "schemas" / "agent-plugin-1.0.0.schema.json"
DEFAULT_MANIFEST = ROOT / "plugin.json"
ANNOTATION_KEYWORDS = {"$schema", "$id", "title", "description"}
ASSERTION_KEYWORDS = {
    "type",
    "properties",
    "required",
    "additionalProperties",
    "const",
    "minLength",
    "maxLength",
    "pattern",
    "items",
}


def json_type_matches(value: Any, expected: str) -> bool:
    return {
        "object": isinstance(value, dict),
        "array": isinstance(value, list),
        "string": isinstance(value, str),
        "number": isinstance(value, (int, float)) and not isinstance(value, bool),
        "integer": isinstance(value, int) and not isinstance(value, bool),
        "boolean": isinstance(value, bool),
        "null": value is None,
    }.get(expected, False)


def validate_instance(instance: Any, schema: dict[str, Any], path: str = "$") -> list[str]:
    errors: list[str] = []
    unknown_keywords = set(schema) - ANNOTATION_KEYWORDS - ASSERTION_KEYWORDS
    if unknown_keywords:
        return [f"{path}: schema uses unsupported keywords: {sorted(unknown_keywords)}"]

    expected_type = schema.get("type")
    if expected_type is not None:
        if not isinstance(expected_type, str) or not json_type_matches(instance, expected_type):
            return [f"{path}: expected {expected_type}, got {type(instance).__name__}"]

    if "const" in schema and instance != schema["const"]:
        errors.append(f"{path}: value must equal {schema['const']!r}")

    if isinstance(instance, str):
        if "minLength" in schema and len(instance) < schema["minLength"]:
            errors.append(f"{path}: string is shorter than {schema['minLength']}")
        if "maxLength" in schema and len(instance) > schema["maxLength"]:
            errors.append(f"{path}: string is longer than {schema['maxLength']}")
        if "pattern" in schema and re.search(schema["pattern"], instance) is None:
            errors.append(f"{path}: string does not match {schema['pattern']!r}")

    if isinstance(instance, list) and "items" in schema:
        item_schema = schema["items"]
        if not isinstance(item_schema, dict):
            errors.append(f"{path}: items schema must be an object")
        else:
            for index, item in enumerate(instance):
                errors.extend(validate_instance(item, item_schema, f"{path}[{index}]"))

    if isinstance(instance, dict):
        properties = schema.get("properties", {})
        if not isinstance(properties, dict):
            return [f"{path}: properties schema must be an object"]
        required = schema.get("required", [])
        if not isinstance(required, list) or not all(isinstance(item, str) for item in required):
            return [f"{path}: required schema must be a string array"]
        for name in required:
            if name not in instance:
                errors.append(f"{path}: missing required property {name!r}")
        additional = schema.get("additionalProperties", True)
        for name, value in instance.items():
            child_path = f"{path}.{name}"
            if name in properties:
                child_schema = properties[name]
                if not isinstance(child_schema, dict):
                    errors.append(f"{child_path}: property schema must be an object")
                else:
                    errors.extend(validate_instance(value, child_schema, child_path))
            elif additional is False:
                errors.append(f"{child_path}: additional property is not allowed")
            elif isinstance(additional, dict):
                errors.extend(validate_instance(value, additional, child_path))
            elif additional is not True:
                errors.append(f"{path}: additionalProperties must be boolean or object")

    return errors


def load_json_object(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"{path}: JSON root must be an object")
    return value


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("manifest", nargs="?", type=Path, default=DEFAULT_MANIFEST)
    parser.add_argument("--schema", type=Path, default=DEFAULT_SCHEMA)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    try:
        schema = load_json_object(args.schema)
        manifest = load_json_object(args.manifest)
    except (OSError, json.JSONDecodeError, ValueError) as exc:
        print(f"Agent Plugins schema validation failed: {exc}", file=sys.stderr)
        return 2
    errors = validate_instance(manifest, schema)
    if errors:
        for error in errors:
            print(error, file=sys.stderr)
        return 1
    print(f"Agent Plugins schema validation passed: {args.manifest}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
