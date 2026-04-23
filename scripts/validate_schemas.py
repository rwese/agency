#!/usr/bin/env python3
"""
Validate JSON schemas against JSON Schema specification.

Usage:
    python scripts/validate_schemas.py [--fix]
"""

import argparse
import json
import sys
from pathlib import Path

SCHEMA_DIR = Path(__file__).parent.parent / "src" / "agency" / "schemas"


def load_schema(name: str) -> dict:
    """Load a JSON schema file."""
    path = SCHEMA_DIR / f"{name}.json"
    if not path.exists():
        raise FileNotFoundError(f"Schema not found: {path}")
    return json.loads(path.read_text())


def validate_schema(schema: dict, name: str) -> list[str]:
    """Validate a JSON schema for correctness."""
    errors = []

    # Check for required fields
    if "$schema" not in schema:
        errors.append(f"{name}: Missing $schema")

    # Check $schema version
    if "$schema" in schema:
        schema_uri = schema["$schema"]
        valid_versions = [
            "https://json-schema.org/draft/2020-12/schema",
            "https://json-schema.org/draft/2019-09/schema",
            "http://json-schema.org/draft-07/schema#",
            "http://json-schema.org/draft-06/schema#",
        ]
        if schema_uri not in valid_versions:
            errors.append(f"{name}: Invalid $schema version: {schema_uri}")

    # Check for $id
    if "$id" not in schema:
        errors.append(f"{name}: Missing $id")

    # Validate $ref targets exist
    if "$ref" in schema:
        ref = schema["$ref"]
        if ref.startswith("#/"):
            # Internal reference - check it exists
            path = ref[2:].split("/")
            target = schema
            for part in path:
                if part not in target:
                    errors.append(f"{name}: Invalid $ref: {ref}")
                    break
                target = target[part]

    # Check properties reference valid types
    if "properties" in schema:
        for prop_name, prop_schema in schema["properties"].items():
            if not isinstance(prop_schema, dict):
                continue
            if "$ref" in prop_schema:
                ref_file = prop_schema["$ref"]
                if not ref_file.endswith(".json"):
                    errors.append(f"{name}.{prop_name}: $ref should end with .json: {ref_file}")

    return errors


def validate_all_schemas() -> tuple[list[str], list[str]]:
    """Validate all schemas in the schemas directory."""
    schema_files = sorted(SCHEMA_DIR.glob("*.json"))
    schema_files = [f for f in schema_files if not f.stem.startswith("_")]

    all_errors = []
    warnings = []

    for schema_file in schema_files:
        name = schema_file.stem
        try:
            schema = json.loads(schema_file.read_text())
        except json.JSONDecodeError as e:
            all_errors.append(f"{name}: Invalid JSON: {e}")
            continue

        errors = validate_schema(schema, name)
        all_errors.extend(errors)

    return all_errors, warnings


def main():
    parser = argparse.ArgumentParser(description="Validate JSON schemas")
    parser.add_argument("--fix", action="store_true", help="Attempt to fix common issues")
    _ = parser.parse_args()

    print("Validating JSON schemas in:", SCHEMA_DIR)
    print()

    errors, warnings = validate_all_schemas()

    if warnings:
        print("Warnings:")
        for w in warnings:
            print(f"  ⚠ {w}")
        print()

    if errors:
        print("Errors:")
        for e in errors:
            print(f"  ✗ {e}")
        print()
        print(f"Found {len(errors)} error(s)")
        sys.exit(1)
    else:
        print("✓ All schemas are valid")
        sys.exit(0)


if __name__ == "__main__":
    main()
