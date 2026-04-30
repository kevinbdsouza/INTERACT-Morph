from __future__ import annotations

import json
from pathlib import Path
from typing import Any

try:
    import yaml
except ModuleNotFoundError:  # pragma: no cover - environment dependent
    yaml = None


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def load_json(path: Path) -> Any:
    return json.loads(read_text(path))


def dump_json(path: Path, data: Any, indent: int = 2) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=indent, sort_keys=False) + "\n", encoding="utf-8")


def load_yaml(path: Path) -> Any:
    if yaml is None:
        raise ModuleNotFoundError("PyYAML is required for YAML support. Install with: pip install PyYAML")
    return yaml.safe_load(read_text(path))


def dump_yaml(path: Path, data: Any) -> None:
    if yaml is None:
        raise ModuleNotFoundError("PyYAML is required for YAML support. Install with: pip install PyYAML")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(yaml.safe_dump(data, sort_keys=False), encoding="utf-8")


def load_json_or_yaml(path: Path) -> Any:
    suffix = path.suffix.lower()
    if suffix == ".json":
        return load_json(path)
    if suffix in {".yaml", ".yml"}:
        return load_yaml(path)
    raise ValueError(f"Unsupported file type for {path}")
