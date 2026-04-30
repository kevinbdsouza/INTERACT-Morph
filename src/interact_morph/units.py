from __future__ import annotations

import math
from typing import Any


POSITIVE_SUFFIXES = (
    "_mm",
    "_kg_m3",
    "_pa_s",
    "_n_m",
    "_um",
)


NONNEGATIVE_SUFFIXES = (
    "_ms",
    "_fps",
    "_c",
)


def _is_number(value: Any) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool)


def _check_scalar(key: str, value: Any) -> list[str]:
    issues: list[str] = []
    if not _is_number(value):
        return issues
    if not math.isfinite(float(value)):
        return [f"{key}: non-finite numeric value"]

    if key.endswith(POSITIVE_SUFFIXES) and float(value) <= 0:
        issues.append(f"{key}: must be > 0")
    if key.endswith(NONNEGATIVE_SUFFIXES) and float(value) < 0:
        issues.append(f"{key}: must be >= 0")
    return issues


def find_unit_issues(obj: Any, prefix: str = "") -> list[str]:
    issues: list[str] = []

    if isinstance(obj, dict):
        for k, v in obj.items():
            key = f"{prefix}.{k}" if prefix else k
            issues.extend(_check_scalar(k, v))
            issues.extend(find_unit_issues(v, key))
    elif isinstance(obj, list):
        for idx, item in enumerate(obj):
            key = f"{prefix}[{idx}]"
            issues.extend(find_unit_issues(item, key))

    return issues
