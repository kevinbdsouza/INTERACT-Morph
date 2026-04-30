#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import random
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = PROJECT_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from interact_morph.io_utils import dump_json, load_json_or_yaml


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Create reproducible dataset splits (MVP-008).")
    parser.add_argument("--dataset-root", required=True, type=Path, help="e.g., data/canonical/family_a")
    parser.add_argument("--config", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    return parser.parse_args()


def load_index(index_path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with index_path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            rows.append(json.loads(line))
    return rows


def assign_groups_to_splits(
    groups: list[str],
    train_fraction: float,
    val_fraction: float,
    seed: int,
) -> dict[str, set[str]]:
    rng = random.Random(seed)
    shuffled = groups[:]
    rng.shuffle(shuffled)

    n = len(shuffled)
    n_train = int(round(n * train_fraction))
    n_val = int(round(n * val_fraction))
    if n_train + n_val > n:
        n_val = max(0, n - n_train)
    n_test = n - n_train - n_val

    train_groups = set(shuffled[:n_train])
    val_groups = set(shuffled[n_train : n_train + n_val])
    test_groups = set(shuffled[n_train + n_val : n_train + n_val + n_test])

    return {
        "train": train_groups,
        "val": val_groups,
        "test": test_groups,
    }


def main() -> int:
    args = parse_args()

    config = load_json_or_yaml(args.config)
    index_path = args.dataset_root / "manifests" / "runs_index.jsonl"
    dataset_manifest_path = args.dataset_root / "manifests" / "dataset_manifest.json"
    rows = load_index(index_path)

    family_filter = config.get("filters", {}).get("family")
    require_video = config.get("filters", {}).get("require_video", False)
    require_annotation = config.get("filters", {}).get("require_annotation_complete", False)

    train_fraction = float(config["train_fraction"])
    val_fraction = float(config["val_fraction"])
    if train_fraction <= 0 or val_fraction < 0:
        raise ValueError("train_fraction must be > 0 and val_fraction must be >= 0")
    if train_fraction + val_fraction > 1.0:
        raise ValueError("train_fraction + val_fraction must be <= 1.0")
    if "test_fraction" in config:
        expected = 1.0 - train_fraction - val_fraction
        test_fraction = float(config["test_fraction"])
        if abs(test_fraction - expected) > 1e-9:
            raise ValueError(
                f"test_fraction ({test_fraction}) does not match 1-train-val ({expected})"
            )

    filtered: list[dict[str, Any]] = []
    for row in rows:
        if family_filter and row.get("family") != family_filter:
            continue
        if require_video and not row.get("video_file"):
            continue
        if require_annotation and not row.get("quality_flags", {}).get("annotation_complete", False):
            continue
        filtered.append(row)

    group_field = config.get("policy", {}).get("group_by_field", "fluid_combination_id")
    missing_group_field = [row.get("run_id") for row in filtered if not row.get(group_field)]
    if missing_group_field:
        raise ValueError(
            f"group_by_field={group_field!r} missing for {len(missing_group_field)} runs; "
            "fix metadata before split generation"
        )
    held_out_groups = set(config.get("held_out", {}).get("fluid_combination_ids", []))

    all_groups = sorted({row[group_field] for row in filtered})
    non_held_out_groups = [g for g in all_groups if g not in held_out_groups]

    split_groups = assign_groups_to_splits(
        groups=non_held_out_groups,
        train_fraction=train_fraction,
        val_fraction=val_fraction,
        seed=int(config["seed"]),
    )
    split_groups["test"].update(held_out_groups)

    split_runs = {"train": [], "val": [], "test": []}
    for row in filtered:
        group = row[group_field]
        if group in split_groups["train"]:
            split_runs["train"].append(row["run_id"])
        elif group in split_groups["val"]:
            split_runs["val"].append(row["run_id"])
        else:
            split_runs["test"].append(row["run_id"])

    payload = {
        "split_name": config.get("split_name", "unnamed_split"),
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "seed": config.get("seed", 0),
        "dataset_root": str(args.dataset_root),
        "dataset_manifest_path": str(dataset_manifest_path),
        "group_by": group_field,
        "counts": {k: len(v) for k, v in split_runs.items()},
        "groups": {k: sorted(list(v)) for k, v in split_groups.items()},
        "runs": split_runs,
    }
    if dataset_manifest_path.exists():
        payload["dataset_manifest_sha256"] = hashlib.sha256(
            dataset_manifest_path.read_text(encoding="utf-8").encode("utf-8")
        ).hexdigest()

    fingerprint_raw = "\n".join(sorted(split_runs["train"] + split_runs["val"] + split_runs["test"]))
    payload["run_fingerprint_sha256"] = hashlib.sha256(fingerprint_raw.encode("utf-8")).hexdigest()

    dump_json(args.output, payload)

    print(f"Wrote split -> {args.output}")
    print(json.dumps(payload["counts"], indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
