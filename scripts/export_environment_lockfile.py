#!/usr/bin/env python3
from __future__ import annotations

import argparse
import ast
import re
import sys
from datetime import datetime, timezone
from importlib import metadata as importlib_metadata
from pathlib import Path
from typing import Any

try:
    import tomllib
except ModuleNotFoundError:  # pragma: no cover
    tomllib = None


PROJECT_ROOT = Path(__file__).resolve().parents[1]

_NAME_SPLIT_RE = re.compile(r"[<>=!~;\s]")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Export a pinned environment lockfile from pyproject dependencies "
            "and currently installed package versions (MVP-036)."
        )
    )
    parser.add_argument("--pyproject", type=Path, default=PROJECT_ROOT / "pyproject.toml")
    parser.add_argument("--output", type=Path, default=PROJECT_ROOT / "locks" / "environment.lock.txt")
    parser.add_argument(
        "--include-optional",
        action="append",
        default=[],
        help="Optional dependency group from pyproject (repeat for multiple groups).",
    )
    parser.add_argument(
        "--skip-project-deps",
        action="store_true",
        help="Only lock selected optional groups and skip project.dependencies.",
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Exit non-zero if any dependency from selected groups is not installed.",
    )
    return parser.parse_args()


def parse_package_name(requirement: Any) -> str | None:
    if not isinstance(requirement, str):
        return None
    text = requirement.strip()
    if not text:
        return None

    token = _NAME_SPLIT_RE.split(text, maxsplit=1)[0].strip()
    if not token:
        return None
    if "[" in token:
        token = token.split("[", 1)[0].strip()
    if not token:
        return None
    return token


def read_pyproject(path: Path) -> dict[str, Any]:
    if tomllib is not None:
        return tomllib.loads(path.read_text(encoding="utf-8"))
    return read_pyproject_fallback(path)


def _count_brackets(text: str) -> int:
    return text.count("[") - text.count("]")


def _parse_list_assignment(lines: list[str], start_index: int) -> tuple[list[str], int]:
    first_line = lines[start_index]
    if "=" not in first_line:
        raise ValueError(f"invalid assignment line: {first_line!r}")
    _, rhs = first_line.split("=", 1)
    expr_lines = [rhs.strip()]
    balance = _count_brackets(expr_lines[0])
    index = start_index

    while balance > 0:
        index += 1
        if index >= len(lines):
            raise ValueError("unterminated list literal in pyproject.toml")
        next_line = lines[index].strip()
        expr_lines.append(next_line)
        balance += _count_brackets(next_line)

    literal = "\n".join(expr_lines).strip()
    parsed = ast.literal_eval(literal)
    if not isinstance(parsed, list) or any(not isinstance(item, str) for item in parsed):
        raise ValueError(f"expected list[str] in assignment, got {type(parsed).__name__}")
    return parsed, index


def read_pyproject_fallback(path: Path) -> dict[str, Any]:
    lines = path.read_text(encoding="utf-8").splitlines()
    section = ""
    project_dependencies: list[str] = []
    optional_dependencies: dict[str, list[str]] = {}

    i = 0
    while i < len(lines):
        raw = lines[i]
        line = raw.strip()
        if not line or line.startswith("#"):
            i += 1
            continue

        if line.startswith("[") and line.endswith("]"):
            section = line[1:-1].strip()
            i += 1
            continue

        if section == "project":
            if line.startswith("dependencies"):
                parsed, i = _parse_list_assignment(lines, i)
                project_dependencies = parsed
        elif section == "project.optional-dependencies":
            if "=" in line and line[0].isalpha():
                group_name = line.split("=", 1)[0].strip()
                parsed, i = _parse_list_assignment(lines, i)
                optional_dependencies[group_name] = parsed

        i += 1

    return {
        "project": {
            "dependencies": project_dependencies,
            "optional-dependencies": optional_dependencies,
        }
    }


def select_dependencies(pyproject_payload: dict[str, Any], include_optional: list[str], skip_project_deps: bool) -> list[str]:
    project = pyproject_payload.get("project")
    if not isinstance(project, dict):
        raise ValueError("pyproject.toml missing [project] table")

    requirements: list[str] = []
    if not skip_project_deps:
        deps = project.get("dependencies", [])
        if isinstance(deps, list):
            requirements.extend([d for d in deps if isinstance(d, str)])

    optional = project.get("optional-dependencies", {})
    if not isinstance(optional, dict):
        optional = {}

    for group in include_optional:
        group_reqs = optional.get(group)
        if not isinstance(group_reqs, list):
            raise ValueError(f"optional dependency group not found or invalid: {group!r}")
        requirements.extend([d for d in group_reqs if isinstance(d, str)])

    names = [parse_package_name(req) for req in requirements]
    deduped = sorted({name for name in names if name}, key=lambda x: x.lower())
    return deduped


def resolve_versions(package_names: list[str]) -> tuple[list[str], list[str]]:
    resolved: list[str] = []
    missing: list[str] = []
    for name in package_names:
        try:
            version = importlib_metadata.version(name)
        except importlib_metadata.PackageNotFoundError:
            missing.append(name)
            continue
        resolved.append(f"{name}=={version}")
    resolved.sort(key=lambda line: line.lower())
    missing.sort(key=lambda name: name.lower())
    return resolved, missing


def main() -> int:
    args = parse_args()

    pyproject_payload = read_pyproject(args.pyproject)
    selected_names = select_dependencies(
        pyproject_payload=pyproject_payload,
        include_optional=list(args.include_optional),
        skip_project_deps=bool(args.skip_project_deps),
    )

    resolved, missing = resolve_versions(selected_names)

    lines = [
        "# INTERACT-Capsules environment lockfile (MVP-036)",
        f"# generated_at_utc={datetime.now(timezone.utc).isoformat()}",
        f"# python_version={sys.version.split()[0]}",
        f"# pyproject={args.pyproject}",
        f"# included_optional_groups={','.join(args.include_optional) if args.include_optional else '(none)'}",
        "",
    ]

    if resolved:
        lines.extend(resolved)
    else:
        lines.append("# No resolvable installed dependencies in selected groups.")

    if missing:
        lines.append("")
        lines.append("# Missing packages (not installed in current environment):")
        lines.extend([f"# - {name}" for name in missing])

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text("\n".join(lines) + "\n", encoding="utf-8")

    print(f"Wrote environment lockfile -> {args.output}")
    print(f"Resolved packages: {len(resolved)}")
    print(f"Missing packages: {len(missing)}")

    if args.strict and missing:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
