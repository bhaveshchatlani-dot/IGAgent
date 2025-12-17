from pathlib import Path
from jsonschema import validate

from utils.io import load_json


def load_schema(schemas_dir: Path, name: str) -> dict:
    return load_json(schemas_dir / f"{name}.schema.json")


def validate_or_die(schemas_dir: Path, schema_name: str, obj: dict) -> None:
    schema = load_schema(schemas_dir, schema_name)
    validate(instance=obj, schema=schema)