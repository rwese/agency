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
DEFAULT_OUTPUT_DIR = Path(__file__).parent.parent / "src" / "agency" / "models"


def load_schema(name: str) -> dict:
    """Load a JSON schema file."""
    path = SCHEMA_DIR / f"{name}.json"
    if not path.exists():
        raise FileNotFoundError(f"Schema not found: {path}")
    return json.loads(path.read_text())


def resolve_ref(ref: str, schemas: dict[str, dict]) -> dict | None:
    """Resolve a $ref to another schema.

    Args:
        ref: JSON reference string like "task.json" or "#/definitions/Task"
        schemas: Dict of schema name to schema dict

    Returns:
        Resolved schema dict or None if not found
    """
    # Handle local file references like "task.json"
    if ref.endswith(".json"):
        schema_name = ref[:-5]  # Remove .json extension
        return schemas.get(schema_name)

    if ref.startswith("#/definitions/"):
        def_name = ref[len("#/definitions/") :]
        return schemas.get(def_name)
    return None


def _to_pascal_case(name: str) -> str:
    """Convert snake_case to PascalCase."""
    return "".join(word.capitalize() for word in name.split("_"))


def schema_to_pydantic(
    schema: dict, name: str, schemas: dict[str, dict] | None = None
) -> tuple[str, list[str]]:
    """Convert a JSON schema to Pydantic model code.

    Args:
        schema: JSON schema dict
        name: Name for the generated class (will be PascalCase'd)
        schemas: Dict of all schemas for reference resolution (for allOf handling)

    Returns: (code, imports)
    """
    imports = set()
    imports.add("from __future__ import annotations")
    imports.add("from pydantic import BaseModel")

    lines = [
        '"""Generated from JSON Schema - do not edit directly."""',
        "",
    ]

    # Extract patterns for validators
    patterns = _extract_patterns(schema)
    pattern_lines = []
    if patterns:
        imports.add("import re")
        imports.add("from pydantic import field_validator")
        # Add module-level pattern constants
        for field_name, pattern in patterns:
            var_name = f"_PATTERN_{field_name.upper()}"
            pattern_lines.append(f"# Pattern from schema: {pattern}")
            pattern_lines.append(f"{var_name} = re.compile(r'{pattern}')")
            pattern_lines.append("")

    # Handle definitions in index schema
    if "definitions" in schema:
        for def_name, def_schema in schema["definitions"].items():
            model_code, model_imports, model_patterns = _schema_to_model(def_name, def_schema, schemas, _to_pascal_case(def_name))
            lines.append(model_code)
            lines.append("")
            imports.update(model_imports)
            pattern_lines.extend(model_patterns)
    else:
        pascal_name = _to_pascal_case(name)
        model_code, model_imports, model_patterns = _schema_to_model(name, schema, schemas, pascal_name)
        lines.append(model_code)
        imports.update(model_imports)
        pattern_lines.extend(model_patterns)

    # Insert pattern constants after imports but before class
    if pattern_lines:
        # Find the class line and insert before it
        class_idx = next((i for i, l in enumerate(lines) if l.startswith("class ")), 0)
        for j, pl in enumerate(reversed(pattern_lines)):
            lines.insert(class_idx, pl)

    # Add imports at the top
    import_lines = sorted(imports)
    result = import_lines + [""] + lines

    return "\n".join(result), list(imports)


def _schema_to_model(
    name: str, schema: dict, schemas: dict[str, dict] | None = None, class_name: str = ""
) -> tuple[str, list[str], list[str]]:
    """Convert a single schema to Pydantic model.

    Args:
        name: Schema/file name or pre-computed class name
        schema: JSON schema dict
        schemas: Dict of all schemas for reference resolution
        class_name: Name of the containing class for validator naming

    Returns: (model_code, imports, pattern_lines)
    """
    lines = []
    imports = []
    pattern_lines = []

    description = schema.get("description")

    # Skip index and private files
    if name.startswith("_") or name == "index":
        return "", imports, pattern_lines

    # Build class - name is already in PascalCase if passed from main()
    # but we still need to handle names from definitions
    if not class_name:
        class_name = _to_pascal_case(name)
    if description:
        lines.append(f'"""{description}"""')
    lines.append(f"class {class_name}(BaseModel):")

    # Handle allOf composition - merge properties from all references
    required_fields = set()
    properties: dict = {}

    if "allOf" in schema and schemas:
        for sub_schema in schema["allOf"]:
            if "$ref" in sub_schema:
                # Resolve the reference
                resolved = resolve_ref(sub_schema["$ref"], schemas)
                if resolved:
                    # Merge properties
                    if "properties" in resolved:
                        properties.update(resolved["properties"])
                    # Merge required
                    if "required" in resolved:
                        required_fields.update(resolved["required"])
            elif "properties" in sub_schema:
                properties.update(sub_schema["properties"])
                if "required" in sub_schema:
                    required_fields.update(sub_schema["required"])
    elif "properties" in schema:
        properties = schema["properties"]
        required_fields = set(schema.get("required", []))

    required = list(required_fields)

    if not properties:
        # No properties
        lines.append("    pass")
        return "\n".join(lines), imports, pattern_lines

    # Extract patterns for field validators
    patterns = _extract_patterns(schema)
    pattern_vars = {}
    for i, (field_name, pattern) in enumerate(patterns):
        var_name = f"_PATTERN_{field_name.upper()}"
        pattern_vars[field_name] = var_name

    for prop_name, prop_schema in properties.items():
        is_required = prop_name in required
        field_code, field_imports = _schema_to_field(prop_name, prop_schema, is_required)
        lines.append(f"    {field_code}")
        imports.extend(field_imports)

    # Add validators for pattern fields
    for field_name, pattern in patterns:
        var_name = pattern_vars[field_name]
        lines.append("")
        lines.append(f"    @field_validator('{field_name}')")
        lines.append(f"    @classmethod")
        lines.append(f"    def validate_{field_name}(cls, v):")
        lines.append(f"        if v is not None and not {var_name}.match(str(v)):")
        lines.append(f"            raise ValueError(f\"{field_name} must match pattern '{pattern}', got: {{v}}\")")
        lines.append(f"        return v")

    # Add backwards compatibility methods
    lines.append("")
    lines.append("    def to_dict(self) -> dict:")
    lines.append('        """Convert to dictionary (backwards compatible)."""')
    lines.append("        return self.model_dump(mode=\"json\")")
    lines.append("")
    lines.append("    @classmethod")
    lines.append(f"    def from_dict(cls, data: dict) -> \"{class_name}\":")
    lines.append('        """Create from dictionary (backwards compatible)."""')
    lines.append("        return cls.model_validate(data)")

    return "\n".join(lines), imports, pattern_lines


def _schema_to_field(name: str, schema: dict, required: bool = False, class_name: str = "") -> tuple[str, list[str]]:
    """Convert a property schema to a Pydantic field.
    
    Args:
        name: Property name
        schema: Property schema
        required: Whether field is required
        class_name: Name of the containing class (for validator naming)
    """
    imports = []
    prop_type, type_imports = _schema_to_type(schema)
    imports.extend(type_imports)

    # Build field line
    if required:
        field_line = f"{name}: {prop_type}"
    else:
        field_line = f"{name}: {prop_type} | None = None"

    return field_line, imports


def _extract_patterns(schema: dict) -> list[tuple[str, str]]:
    """Extract pattern validators from schema properties.
    
    Returns list of (field_name, pattern) tuples.
    """
    patterns = []
    
    # Check properties directly
    if "properties" in schema:
        for prop_name, prop_schema in schema["properties"].items():
            if "pattern" in prop_schema:
                patterns.append((prop_name, prop_schema["pattern"]))
    
    # Check allOf
    if "allOf" in schema:
        for sub_schema in schema["allOf"]:
            if "properties" in sub_schema:
                for prop_name, prop_schema in sub_schema["properties"].items():
                    if "pattern" in prop_schema:
                        patterns.append((prop_name, prop_schema["pattern"]))
    
    return patterns


def _get_schema_type(schema: dict) -> str | list | None:
    """Get the type from a schema, handling nullable types."""
    schema_type = schema.get("type")
    # Handle nullable types like ["string", "null"]
    if isinstance(schema_type, list):
        # Filter out 'null' and return remaining type
        non_null = [t for t in schema_type if t != "null"]
        if non_null:
            return non_null[0]
        return "None"
    return schema_type


def _schema_to_type(schema: dict) -> tuple[str, list[str]]:
    """Convert a schema type to Python type annotation."""
    imports = []

    # Handle enum
    if "enum" in schema:
        enum_values = ", ".join(repr(v) for v in schema["enum"])
        return f"Literal[{enum_values}]", ["from typing import Literal"]

    # Handle array
    schema_type = _get_schema_type(schema)
    if schema_type == "array":
        items_schema = schema.get("items", {})
        item_type, item_imports = _schema_to_type(items_schema)
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


def main():
    parser = argparse.ArgumentParser(description="Generate Pydantic models from JSON schemas")
    parser.add_argument("--check", action="store_true", help="Check if models are up to date (exit 1 if not)")
    parser.add_argument("--output-dir", default=str(DEFAULT_OUTPUT_DIR), help="Output directory for models")
    args = parser.parse_args()

    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    # Load all schemas first (for reference resolution)
    all_schemas: dict[str, dict] = {}
    for schema_file in SCHEMA_DIR.glob("*.json"):
        if not schema_file.stem.startswith("_"):
            all_schemas[schema_file.stem] = json.loads(schema_file.read_text())

    # Load index schema for definitions
    index_path = SCHEMA_DIR / "_index.json"
    if index_path.exists():
        all_schemas["index"] = json.loads(index_path.read_text())

    # Generate models from all schemas
    schema_files = sorted(SCHEMA_DIR.glob("*.json"))
    schema_files = [f for f in schema_files if not f.stem.startswith("_")]

    print(f"Generating models from {len(schema_files)} schemas...")

    generated = []
    all_imports = set()

    for schema_file in schema_files:
        schema = json.loads(schema_file.read_text())
        schema_name = schema_file.stem  # Original name (snake_case)

        # Skip index file
        if schema_file.stem == "index":
            continue

        # Handle definitions in index schema
        if "definitions" in schema:
            for def_name, def_schema in schema["definitions"].items():
                class_name = _to_pascal_case(def_name)
                code, imports = schema_to_pydantic(
                    {"definitions": {def_name: def_schema}}, def_name, all_schemas
                )
                output_file = output_dir / f"{def_name}.py"
                generated.append((output_file, code, class_name))
                all_imports.update(imports)
        else:
            code, imports = schema_to_pydantic(schema, schema_name, all_schemas)
            output_file = output_dir / f"{schema_file.stem}.py"
            class_name = _to_pascal_case(schema_name)
            generated.append((output_file, code, class_name))
            all_imports.update(imports)

    # Check mode - compare generated content with existing files
    if args.check:
        changes_needed = False
        for output_file, code, class_name in generated:
            if output_file.exists():
                existing = output_file.read_text().strip()
                new = code.strip()
                if existing != new:
                    changes_needed = True
                    print(f"  CHANGED: {output_file.name}")
                else:
                    print(f"  OK: {output_file.name}")
            else:
                changes_needed = True
                print(f"  NEW: {output_file.name}")

        if changes_needed:
            print("\nModels are out of date. Run without --check to regenerate.")
            return 1
        else:
            print("\nAll models are up to date.")
            return 0

    # Write models
    for output_file, code, class_name in generated:
        if code.strip():
            output_file.write_text(code + "\n")
            print(f"  Generated: {output_file.relative_to(output_dir.parent.parent)}")

    # Write __init__.py with explicit imports (using _to_pascal_case for consistency)
    init_lines = [
        '"""Generated Pydantic models from JSON schemas."""',
        "",
    ]
    for output_file, _, class_name in generated:
        module = output_file.stem
        # Use _to_pascal_case to match actual class names
        init_lines.append(f"from .{module} import {class_name}")

    # Add re-exports for convenience
    init_lines.append("")
    init_lines.append("__all__ = [")
    for _, _, class_name in generated:
        init_lines.append(f'    "{class_name}",')
    init_lines.append("]")

    (output_dir / "__init__.py").write_text("\n".join(init_lines) + "\n")

    print(f"\nGenerated {len(generated)} model files in {output_dir}")
    return 0


if __name__ == "__main__":
    exit(main())
