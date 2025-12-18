from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator, FormatChecker
from jsonschema.exceptions import ValidationError

from utils.io import load_json


def load_schema(schemas_dir: Path, name: str) -> dict:
    return load_json(schemas_dir / f"{name}.schema.json")


def _json_pointer(path_parts) -> str:
    # Produces something like: $.close.AAPL
    if not path_parts:
        return "$"
    return "$." + ".".join(str(p) for p in path_parts)


def validate_or_die(schemas_dir: Path, schema_name: str, obj: Any) -> None:
    schema_path = schemas_dir / f"{schema_name}.schema.json"
    schema = load_schema(schemas_dir, schema_name)

    validator = Draft202012Validator(schema, format_checker=FormatChecker())

    errors = sorted(validator.iter_errors(obj), key=lambda e: list(e.path))
    if not errors:
        return

    # Print up to 5 errors (usually enough to fix quickly)
    print(f"\n❌ Schema validation failed: {schema_name}", file=sys.stderr)
    print(f"   Schema: {schema_path}", file=sys.stderr)

    for idx, err in enumerate(errors[:5], start=1):
        loc = _json_pointer(list(err.path))
        print(f"   {idx}) At {loc}: {err.message}", file=sys.stderr)

        # Optional: show what schema rule failed (helpful for debugging)
        if err.validator:
            print(f"      Rule: {err.validator}", file=sys.stderr)

    if len(errors) > 5:
        print(f"   …and {len(errors) - 5} more error(s).", file=sys.stderr)

    raise SystemExit(1)