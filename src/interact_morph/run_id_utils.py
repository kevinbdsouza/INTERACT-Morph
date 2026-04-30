from __future__ import annotations

import hashlib
import re


CANONICAL_RUN_ID_PATTERN = re.compile(r"^[A-Z]_[A-Z0-9]+(?:_[A-Z0-9]+)*$")
NON_ALNUM_RE = re.compile(r"[^A-Za-z0-9]+")
MULTI_UNDERSCORE_RE = re.compile(r"_+")


def normalize_token(value: str) -> str:
    text = NON_ALNUM_RE.sub("_", value.strip().upper())
    text = MULTI_UNDERSCORE_RE.sub("_", text)
    return text.strip("_")


def extract_source_run_id(metadata: dict[str, object], run_dir_name: str) -> str:
    for key in ("source_run_id", "run_id"):
        value = metadata.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip()
    return run_dir_name


def canonicalize_run_id(family: str, source_run_id: str, run_dir_name: str) -> str:
    family_token = normalize_token(family)[:1] or "A"
    base = normalize_token(source_run_id or run_dir_name)
    if not base:
        base = "RUN"

    family_prefix = f"{family_token}_"
    if base == family_token:
        base = "RUN"
    elif base.startswith(family_prefix):
        stripped = base[len(family_prefix) :]
        base = stripped if stripped else "RUN"

    return f"{family_token}_{base}"


def ensure_unique_run_id(
    candidate: str,
    used_ids: set[str],
    disambiguator: str,
) -> tuple[str, bool]:
    if candidate not in used_ids:
        used_ids.add(candidate)
        return candidate, False

    suffix = hashlib.sha1(disambiguator.encode("utf-8")).hexdigest()[:8].upper()
    unique_candidate = f"{candidate}_{suffix}"
    counter = 2
    while unique_candidate in used_ids:
        unique_candidate = f"{candidate}_{suffix}_{counter}"
        counter += 1

    used_ids.add(unique_candidate)
    return unique_candidate, True


def is_canonical_run_id(run_id: str, family: str | None = None) -> bool:
    if not CANONICAL_RUN_ID_PATTERN.fullmatch(run_id):
        return False
    if family is None:
        return True
    family_token = normalize_token(family)[:1]
    return bool(family_token) and run_id.startswith(f"{family_token}_")
