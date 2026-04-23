#!/usr/bin/env python3
"""
Generate Pydantic models from JSON schemas.

Usage:
    python scripts/generate_models.py [--check] [--output-dir src/agency/models]
"""

import argparse
import json
from pathlib import Path

SCHEMA_DIR = Path(__file__).parent.parent / "src" / "agency" / "schemas"
OUTPUT_DIR = Path(__file__).parent.parent / "src" / "agency" / "models"


def load_schema(name: str) -> dict:
    """Load a JSON schema file."""
    path = SCHEMA_DIR / f"{name}.json"
    if not path.exists():
        raise FileNotFoundError(f"Schema not found: {path}")
    return json.loads(path.read_text())


def schema_to_pydantic(schema: dict, class_name: str) -> tuple[str, list[str]]:
    """Convert a JSON schema to Pydantic model code.

    Returns: (code, imports)
    """
    imports = set()
    imports.add("from __future__ import annotations")
    imports.add("from pydantic import BaseModel")

    lines = [
        '"""Generated from JSON Schema - do not edit directly."""',
        "",
    ]

    # Handle definitions in index schema
    if "definitions" in schema:
        for def_name, def_schema in schema["definitions"].items():
            model_code, model_imports = _schema_to_model(def_name, def_schema)
            lines.append(model_code)
            lines.append("")
            imports.update(model_imports)
    else:
        model_code, model_imports = _schema_to_model(class_name, schema)
        lines.append(model_code)
        imports.update(model_imports)

    # Add imports at the top
    import_lines = sorted(imports)
    result = import_lines + [""] + lines

    return "\n".join(result), list(imports)


def _schema_to_model(name: str, schema: dict) -> tuple[str, list[str]]:
    """Convert a single schema to Pydantic model."""
    lines = []
    imports = []

    description = schema.get("description")

    # Skip index and private files
    if name.startswith("_") or name == "index":
        return "", imports

    # Build class
    class_name = _to_pascal_case(name)
    if description:
        lines.append(f'"""{description}"""')
    lines.append(f"class {class_name}(BaseModel):")

    required = schema.get("required", [])
    properties = schema.get("properties", {})

    if not properties:
        # No properties
        lines.append("    pass")
        return "\n".join(lines), imports

    for prop_name, prop_schema in properties.items():
        is_required = prop_name in required
        field_code, field_imports = _schema_to_field(prop_name, prop_schema, is_required)
        lines.append(f"    {field_code}")
        imports.extend(field_imports)

    return "\n".join(lines), imports


def _schema_to_field(name: str, schema: dict, required: bool = False) -> tuple[str, list[str]]:
    """Convert a property schema to a Pydantic field."""
    imports = []
    prop_type, type_imports = _schema_to_type(schema)
    imports.extend(type_imports)

    # Build default value
    has_default = False
    default = None

    if "default" in schema:
        default = schema["default"]
        has_default = True
    elif not required:
        has_default = True  # Optional fields get None

    # Clean up prop_type - remove duplicate | None
    prop_type = prop_type.replace(" | None | None", " | None")

    # Build field signature
    comment = ""
    if schema.get("description"):
        comment = f"  # {schema['description']}"

    if has_default:
        if default is not None:
            return f"{name}: {prop_type} = {repr(default)}{comment}", imports
        else:
            # Ensure we have | None for optional fields
            if " | None" not in prop_type and prop_type != "None":
                prop_type = f"{prop_type} | None"
            return f"{name}: {prop_type} = None{comment}", imports
    else:
        return f"{name}: {prop_type}{comment}", imports


def _schema_to_type(schema: dict) -> tuple[str, list[str]]:
    """Convert a schema to a Python type annotation.

    Returns: (type_string, imports_needed)
    """
    imports = []
    schema_type = schema.get("type")

    # Handle type arrays (JSON Schema union types like ["string", "null"])
    if isinstance(schema_type, list):
        type_parts = []
        for t in schema_type:
            if isinstance(t, str):
                part, part_imports = _schema_to_type({"type": t})
                type_parts.append(part)
                imports.extend(part_imports)
            else:
                type_parts.append(str(t))
        # Filter out 'None' and convert to Pydantic Optional
        non_null = [p for p in type_parts if p != "None"]
        if "None" in type_parts:
            if len(non_null) == 0:
                return "None", imports
            if len(non_null) == 1:
                return f"{non_null[0]} | None", imports
            return " | ".join(non_null) + " | None", imports
        return " | ".join(type_parts), imports

    # Handle enum first
    if "enum" in schema:
        enum_values = schema["enum"]
        return f"Literal[{', '.join(repr(v) for v in enum_values)}]", ["from typing import Literal"]

    # Handle refs
    if "$ref" in schema:
        ref = schema["$ref"]
        ref_name = ref.replace(".json", "").split("/")[-1]
        return _to_pascal_case(ref_name), imports

    # Handle oneOf/anyOf
    if "oneOf" in schema:
        types = []
        for s in schema["oneOf"]:
            t, t_imports = _schema_to_type(s)
            types.append(t)
            imports.extend(t_imports)
        return " | ".join(types), imports
    if "anyOf" in schema:
        types = []
        for s in schema["anyOf"]:
            t, t_imports = _schema_to_type(s)
            types.append(t)
            imports.extend(t_imports)
        return " | ".join(types), imports

    # Handle array
    if schema_type == "array":
        items = schema.get("items", {})
        if "$ref" in items:
            item_type, item_imports = _schema_to_type(items)
        elif items.get("type"):
            item_type, item_imports = _schema_to_type(items)
        else:
            item_type = "Any"
            item_imports = ["from typing import Any"]
        imports.extend(item_imports)
        return f"list[{item_type}]", imports

    # Handle object
    if schema_type == "object":
        if "properties" in schema:
            return "dict", imports
        if "additionalProperties":
            return "dict", imports
        return "dict", imports

    # Handle primitives
    type_map = {
        "string": "str",
        "integer": "int",
        "number": "float",
        "boolean": "bool",
        "null": "None",
    }

    if schema_type in type_map:
        return type_map[schema_type], imports

    return "Any", ["from typing import Any"]


def _to_pascal_case(name: str) -> str:
    """Convert snake_case to PascalCase."""
    return "".join(word.capitalize() for word in name.split("_"))


def main():
    parser = argparse.ArgumentParser(description="Generate Pydantic models from JSON schemas")
    parser.add_argument("--check", action="store_true", help="Check if models are up to date (exit 1 if not)")
    parser.add_argument("--output-dir", default=str(OUTPUT_DIR), help="Output directory for models")
    _ = parser.parse_args()

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    # Generate models from all schemas
    schema_files = sorted(SCHEMA_DIR.glob("*.json"))
    schema_files = [f for f in schema_files if not f.stem.startswith("_")]

    print(f"Generating models from {len(schema_files)} schemas...")

    generated = []
    all_imports = set()

    for schema_file in schema_files:
        schema = json.loads(schema_file.read_text())
        class_name = _to_pascal_case(schema_file.stem)

        # Skip index file
        if schema_file.stem == "index":
            continue

        # Handle definitions in index schema
        if "definitions" in schema:
            for def_name, def_schema in schema["definitions"].items():
                class_name = _to_pascal_case(def_name)
                code, imports = schema_to_pydantic({"definitions": {def_name: def_schema}}, class_name)
                output_file = OUTPUT_DIR / f"{def_name}.py"
                generated.append((output_file, code))
                all_imports.update(imports)
        else:
            code, imports = schema_to_pydantic(schema, class_name)
            output_file = OUTPUT_DIR / f"{schema_file.stem}.py"
            generated.append((output_file, code))
            all_imports.update(imports)

    # Write models
    for output_file, code in generated:
        if code.strip():
            output_file.write_text(code + "\n")
            print(f"  Generated: {output_file.relative_to(OUTPUT_DIR.parent.parent)}")

    # Write __init__.py with explicit imports (ruff-safe)
    init_lines = [
        '"""Generated Pydantic models from JSON schemas."""',
        "",
    ]
    for output_file, _ in generated:
        module = output_file.stem
        init_lines.append(f"from .{module} import {module.capitalize()}")

    # Add re-exports for convenience
    init_lines.append("")
    init_lines.append("__all__ = [")
    for output_file, _ in generated:
        module = output_file.stem
        init_lines.append(f'    "{module.capitalize()}",')
    init_lines.append("]")

    (OUTPUT_DIR / "__init__.py").write_text("\n".join(init_lines) + "\n")

    print(f"\nGenerated {len(generated)} model files in {OUTPUT_DIR}")


if __name__ == "__main__":
    main()
