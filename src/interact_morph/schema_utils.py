from __future__ import annotations

import re
from pathlib import Path
from typing import Any

try:
    from jsonschema import Draft202012Validator
except ModuleNotFoundError:  # pragma: no cover - environment dependent
    Draft202012Validator = None

from .io_utils import load_json


def load_schema(schema_path: Path) -> dict[str, Any]:
    return load_json(schema_path)


def _is_type(value: Any, schema_type: str) -> bool:
    if schema_type == "object":
        return isinstance(value, dict)
    if schema_type == "array":
        return isinstance(value, list)
    if schema_type == "string":
        return isinstance(value, str)
    if schema_type == "number":
        return isinstance(value, (int, float)) and not isinstance(value, bool)
    if schema_type == "boolean":
        return isinstance(value, bool)
    if schema_type == "null":
        return value is None
    return True


def _resolve_ref(root: dict[str, Any], ref: str) -> dict[str, Any]:
    if not ref.startswith("#/"):
        return {}
    cur: Any = root
    for part in ref[2:].split("/"):
        if not isinstance(cur, dict) or part not in cur:
            return {}
        cur = cur[part]
    return cur if isinstance(cur, dict) else {}


def _merge_ref_schema(schema: dict[str, Any], root: dict[str, Any]) -> dict[str, Any]:
    if "$ref" not in schema:
        return schema
    target = _resolve_ref(root, schema["$ref"])
    merged = dict(target)
    for k, v in schema.items():
        if k != "$ref":
            merged[k] = v
    return merged


def _validate_minimal(instance: Any, schema: dict[str, Any], root: dict[str, Any], path: str = "") -> list[str]:
    schema = _merge_ref_schema(schema, root)
    errors: list[str] = []

    # anyOf
    any_of = schema.get("anyOf")
    if isinstance(any_of, list) and any_of:
        any_ok = False
        for sub in any_of:
            sub_errors = _validate_minimal(instance, sub, root, path)
            if not sub_errors:
                any_ok = True
                break
        if not any_ok:
            errors.append(f"{path or '<root>'}: failed anyOf constraints")

    # type checking
    schema_type = schema.get("type")
    if schema_type is not None:
        allowed = schema_type if isinstance(schema_type, list) else [schema_type]
        if not any(_is_type(instance, t) for t in allowed):
            errors.append(f"{path or '<root>'}: expected type {allowed}, got {type(instance).__name__}")
            return errors

    # enum
    if "enum" in schema and instance not in schema["enum"]:
        errors.append(f"{path or '<root>'}: value {instance!r} not in enum")

    # numeric constraints
    if isinstance(instance, (int, float)) and not isinstance(instance, bool):
        if "minimum" in schema and instance < schema["minimum"]:
            errors.append(f"{path or '<root>'}: {instance} < minimum {schema['minimum']}")
        if "maximum" in schema and instance > schema["maximum"]:
            errors.append(f"{path or '<root>'}: {instance} > maximum {schema['maximum']}")
        if "exclusiveMinimum" in schema and instance <= schema["exclusiveMinimum"]:
            errors.append(
                f"{path or '<root>'}: {instance} <= exclusiveMinimum {schema['exclusiveMinimum']}"
            )

    # string constraints
    if isinstance(instance, str):
        if "minLength" in schema and len(instance) < schema["minLength"]:
            errors.append(f"{path or '<root>'}: string shorter than minLength {schema['minLength']}")
        pattern = schema.get("pattern")
        if pattern and not re.search(pattern, instance):
            errors.append(f"{path or '<root>'}: string does not match pattern {pattern!r}")

    # object handling
    if isinstance(instance, dict):
        required = schema.get("required", [])
        for field in required:
            if field not in instance:
                errors.append(f"{path + '.' if path else ''}{field}: missing required field")

        properties = schema.get("properties", {})
        additional_props = schema.get("additionalProperties", True)

        if additional_props is False:
            extra = sorted(set(instance.keys()) - set(properties.keys()))
            for key in extra:
                errors.append(f"{path + '.' if path else ''}{key}: additional property not allowed")

        for key, val in instance.items():
            if key in properties:
                child_path = f"{path}.{key}" if path else key
                errors.extend(_validate_minimal(val, properties[key], root, child_path))

    # array handling
    if isinstance(instance, list):
        min_items = schema.get("minItems")
        if isinstance(min_items, int) and len(instance) < min_items:
            errors.append(f"{path or '<root>'}: array has {len(instance)} items, minItems is {min_items}")
        item_schema = schema.get("items")
        if isinstance(item_schema, dict):
            for idx, item in enumerate(instance):
                child_path = f"{path}[{idx}]" if path else f"[{idx}]"
                errors.extend(_validate_minimal(item, item_schema, root, child_path))

    return errors


def validate_with_schema(instance: dict[str, Any], schema_path: Path) -> list[str]:
    schema = load_schema(schema_path)

    if Draft202012Validator is not None:
        validator = Draft202012Validator(schema, format_checker=Draft202012Validator.FORMAT_CHECKER)
        errors = sorted(validator.iter_errors(instance), key=lambda e: e.path)
        messages: list[str] = []
        for err in errors:
            location = ".".join(str(piece) for piece in err.absolute_path)
            if location:
                messages.append(f"{location}: {err.message}")
            else:
                messages.append(err.message)
        return messages

    return _validate_minimal(instance=instance, schema=schema, root=schema)
