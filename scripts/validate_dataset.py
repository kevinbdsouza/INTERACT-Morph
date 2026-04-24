#!/usr/bin/env python3
from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = PROJECT_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from interact_capsules.io_utils import load_json
from interact_capsules.run_id_utils import is_canonical_run_id
from interact_capsules.schema_utils import validate_with_schema
from interact_capsules.units import find_unit_issues


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Validate canonical dataset (MVP-006).")
    parser.add_argument("--dataset-root", required=True, type=Path, help="e.g., data/canonical/family_a")
    parser.add_argument("--run-schema", default=Path("schemas/run_metadata.schema.json"), type=Path)
    parser.add_argument("--features-schema", default=Path("schemas/derived_features.schema.json"), type=Path)
    parser.add_argument("--require-labels", action="store_true")
    parser.add_argument("--require-derived", action="store_true")
    parser.add_argument(
        "--allow-noncanonical-run-id",
        action="store_true",
        help="Allow run_id values outside canonical Family-prefixed format",
    )
    return parser.parse_args()


def ensure_monotonic_times(series: list[dict[str, Any]], name: str) -> list[str]:
    issues: list[str] = []
    prev = None
    for idx, point in enumerate(series):
        t = point.get("t_ms")
        if prev is not None and t is not None and t < prev:
            issues.append(f"{name}[{idx}].t_ms decreases ({t} < {prev})")
        prev = t
    return issues


def validate_run(
    run_dir: Path,
    run_schema: Path,
    features_schema: Path,
    require_labels: bool,
    require_derived: bool,
    require_canonical_run_id: bool,
) -> tuple[str | None, list[str]]:
    errors: list[str] = []

    metadata_path = run_dir / "metadata.json"
    if not metadata_path.exists():
        return None, [f"{run_dir.name}: missing metadata.json"]

    metadata = load_json(metadata_path)
    run_id = metadata.get("run_id")
    family = metadata.get("family")

    errors.extend([f"{run_dir.name}: metadata schema: {m}" for m in validate_with_schema(metadata, run_schema)])
    errors.extend([f"{run_dir.name}: units: {m}" for m in find_unit_issues(metadata)])

    if isinstance(run_id, str):
        if run_dir.name != run_id:
            errors.append(f"{run_dir.name}: run directory name does not match metadata.run_id={run_id}")
        if require_canonical_run_id and not is_canonical_run_id(run_id, str(family) if isinstance(family, str) else None):
            errors.append(
                f"{run_dir.name}: run_id={run_id} does not match canonical format <FAMILY>_<TOKEN[_TOKEN...]>"
            )
    else:
        errors.append(f"{run_dir.name}: metadata.run_id missing or not a string")

    source_run_id = metadata.get("source_run_id")
    if source_run_id is not None and (not isinstance(source_run_id, str) or not source_run_id.strip()):
        errors.append(f"{run_dir.name}: source_run_id present but empty/invalid")

    video_relpath = metadata.get("asset_paths", {}).get("video_relpath")
    if video_relpath:
        if not (run_dir / video_relpath).exists():
            errors.append(f"{run_dir.name}: missing video asset {video_relpath}")
    else:
        errors.append(f"{run_dir.name}: metadata missing asset_paths.video_relpath")

    labels_relpath = metadata.get("asset_paths", {}).get("labels_relpath")
    if require_labels and not labels_relpath:
        errors.append(f"{run_dir.name}: labels required but labels_relpath missing")
    if labels_relpath and not (run_dir / labels_relpath).exists():
        errors.append(f"{run_dir.name}: labels_relpath points to missing file {labels_relpath}")

    features_relpath = metadata.get("asset_paths", {}).get("derived_features_relpath")
    if require_derived and not features_relpath:
        errors.append(f"{run_dir.name}: derived features required but derived_features_relpath missing")
    if features_relpath:
        feat_path = run_dir / features_relpath
        if not feat_path.exists():
            errors.append(f"{run_dir.name}: missing derived features file {features_relpath}")
        else:
            features = load_json(feat_path)
            errors.extend([f"{run_dir.name}: derived features schema: {m}" for m in validate_with_schema(features, features_schema)])
            if "run_id" in features and run_id and features["run_id"] != run_id:
                errors.append(f"{run_dir.name}: run_id mismatch metadata={run_id} features={features['run_id']}")
            trajectories = features.get("trajectories", {})
            for series_name, series in trajectories.items():
                if isinstance(series, list):
                    errors.extend(
                        [
                            f"{run_dir.name}: trajectory {msg}"
                            for msg in ensure_monotonic_times(series, series_name)
                        ]
                    )

    return run_id, errors


def main() -> int:
    args = parse_args()

    runs_root = args.dataset_root / "runs"
    if not runs_root.exists():
        print(f"Dataset runs dir not found: {runs_root}")
        return 1

    seen_run_ids: set[str] = set()
    duplicate_run_ids: set[str] = set()
    all_errors: list[str] = []
    run_count = 0

    for run_dir in sorted(runs_root.iterdir()):
        if not run_dir.is_dir():
            continue
        run_count += 1
        run_id, errors = validate_run(
            run_dir=run_dir,
            run_schema=args.run_schema,
            features_schema=args.features_schema,
            require_labels=args.require_labels,
            require_derived=args.require_derived,
            require_canonical_run_id=not args.allow_noncanonical_run_id,
        )
        if run_id:
            if run_id in seen_run_ids:
                duplicate_run_ids.add(run_id)
            seen_run_ids.add(run_id)
        all_errors.extend(errors)

    for dup in sorted(duplicate_run_ids):
        all_errors.append(f"duplicate run_id across dataset: {dup}")

    print(f"Validated runs: {run_count}")
    print(f"Errors: {len(all_errors)}")
    if all_errors:
        for err in all_errors:
            print(f"- {err}")

    return 1 if all_errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
