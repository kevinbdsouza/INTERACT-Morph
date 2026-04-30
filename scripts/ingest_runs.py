#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = PROJECT_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from interact_morph.io_utils import dump_json, load_json_or_yaml
from interact_morph.run_id_utils import (
    canonicalize_run_id,
    ensure_unique_run_id,
    extract_source_run_id,
)
from interact_morph.schema_utils import validate_with_schema


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Ingest raw runs into canonical layout (MVP-005).")
    parser.add_argument("--source-dir", required=True, type=Path)
    parser.add_argument("--dest-root", required=True, type=Path, help="e.g., data/canonical/family_a")
    parser.add_argument("--schema", default=Path("schemas/run_metadata.schema.json"), type=Path)
    parser.add_argument("--family", default="A", choices=["A", "B", "C"])
    parser.add_argument(
        "--run-id-mode",
        choices=["canonicalize", "preserve"],
        default="canonicalize",
        help="canonicalize: rewrite run_id to canonical format and retain source_run_id; preserve: keep metadata run_id",
    )
    parser.add_argument("--overwrite", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    return parser.parse_args()


def find_file(run_dir: Path, names: tuple[str, ...]) -> Path | None:
    for name in names:
        path = run_dir / name
        if path.exists():
            return path
    return None


def find_video(run_dir: Path) -> Path | None:
    for ext in ("*.mp4", "*.mov", "*.avi", "*.mkv"):
        found = list(run_dir.glob(ext))
        if found:
            return found[0]
    return None


def file_sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        while True:
            chunk = f.read(1024 * 1024)
            if not chunk:
                break
            h.update(chunk)
    return h.hexdigest()


def ingest_one_run(
    run_dir: Path,
    dest_runs_dir: Path,
    schema_path: Path,
    family: str,
    run_id_mode: str,
    used_run_ids: set[str],
    overwrite: bool,
    dry_run: bool,
) -> tuple[dict[str, Any] | None, dict[str, Any] | None, list[str]]:
    errors: list[str] = []

    metadata_path = find_file(run_dir, ("metadata.json", "metadata.yaml", "metadata.yml"))
    if not metadata_path:
        return None, None, [f"{run_dir.name}: missing metadata file"]

    video_path = find_video(run_dir)
    if not video_path:
        return None, None, [f"{run_dir.name}: missing video file"]

    metadata = load_json_or_yaml(metadata_path)
    if not isinstance(metadata, dict):
        return None, None, [f"{run_dir.name}: metadata root must be an object"]
    metadata_family = str(metadata.get("family", "")).strip().upper()
    if metadata_family != family:
        run_hint = metadata.get("run_id") or run_dir.name
        return None, None, [f"{run_hint}: family mismatch metadata={metadata_family or '<missing>'} expected={family}"]

    source_run_id = extract_source_run_id(metadata, run_dir.name)
    if run_id_mode == "canonicalize":
        canonical_base = canonicalize_run_id(
            family=family,
            source_run_id=source_run_id,
            run_dir_name=run_dir.name,
        )
        candidate_used = set(used_run_ids)
        run_id, collision_resolved = ensure_unique_run_id(
            candidate=canonical_base,
            used_ids=candidate_used,
            disambiguator=str(run_dir.resolve()),
        )
    else:
        raw_run_id = str(metadata.get("run_id", "")).strip()
        if not raw_run_id:
            return None, None, [f"{run_dir.name}: metadata.run_id missing in preserve mode"]
        run_id = raw_run_id
        if run_id in used_run_ids:
            return None, None, [f"{run_id}: duplicate run_id in preserve mode"]
        collision_resolved = False

    metadata["source_run_id"] = source_run_id
    metadata["run_id"] = run_id
    metadata["family"] = family

    # Ensure path container exists before setting canonical asset references.
    asset_paths = metadata.get("asset_paths")
    if not isinstance(asset_paths, dict):
        metadata["asset_paths"] = {}

    rel_video_name = video_path.name
    rel_labels_name = "labels.json" if (run_dir / "labels.json").exists() else None
    rel_features_name = "derived_features.json" if (run_dir / "derived_features.json").exists() else None

    metadata["asset_paths"]["video_relpath"] = rel_video_name
    if rel_labels_name:
        metadata["asset_paths"]["labels_relpath"] = rel_labels_name
    if rel_features_name:
        metadata["asset_paths"]["derived_features_relpath"] = rel_features_name

    schema_errors = validate_with_schema(metadata, schema_path)
    if schema_errors:
        return None, None, [f"{run_dir.name}: schema validation failed: {e}" for e in schema_errors]

    target_dir = dest_runs_dir / run_id
    if target_dir.exists() and not overwrite:
        return None, None, [f"{run_id}: destination exists ({target_dir}), use --overwrite"]

    used_run_ids.add(run_id)

    if not dry_run:
        if target_dir.exists() and overwrite:
            shutil.rmtree(target_dir)
        target_dir.mkdir(parents=True, exist_ok=True)

    if not dry_run:
        shutil.copy2(video_path, target_dir / rel_video_name)
        shutil.copy2(metadata_path, target_dir / f"metadata.source{metadata_path.suffix}")
        dump_json(target_dir / "metadata.json", metadata)

        if rel_labels_name:
            shutil.copy2(run_dir / rel_labels_name, target_dir / rel_labels_name)
        if rel_features_name:
            shutil.copy2(run_dir / rel_features_name, target_dir / rel_features_name)

    run_record = {
        "run_id": run_id,
        "source_run_id": source_run_id,
        "run_id_mode": run_id_mode,
        "family": metadata["family"],
        "fluid_combination_id": metadata["fluid_combination_id"],
        "capture_timestamp": metadata["capture_timestamp"],
        "encapsulation_success": metadata["outcomes"]["encapsulation_success"],
        "regime_label": metadata["outcomes"]["regime_label"],
        "quality_flags": metadata.get("quality_flags", {}),
        "run_relpath": f"runs/{run_id}",
        "video_file": rel_video_name,
    }

    run_id_map_row = {
        "source_run_dir": str(run_dir),
        "source_run_id": source_run_id,
        "canonical_run_id": run_id,
        "collision_resolved": collision_resolved,
    }

    return run_record, run_id_map_row, []


def main() -> int:
    args = parse_args()

    dest_runs_dir = args.dest_root / "runs"
    dest_manifest_dir = args.dest_root / "manifests"
    if not args.dry_run:
        dest_runs_dir.mkdir(parents=True, exist_ok=True)
        dest_manifest_dir.mkdir(parents=True, exist_ok=True)

    run_dirs = [p for p in sorted(args.source_dir.iterdir()) if p.is_dir()]
    index: list[dict[str, Any]] = []
    run_id_map_rows: list[dict[str, Any]] = []
    used_run_ids: set[str] = set()
    errors: list[str] = []

    for run_dir in run_dirs:
        record, map_row, run_errors = ingest_one_run(
            run_dir=run_dir,
            dest_runs_dir=dest_runs_dir,
            schema_path=args.schema,
            family=args.family,
            run_id_mode=args.run_id_mode,
            used_run_ids=used_run_ids,
            overwrite=args.overwrite,
            dry_run=args.dry_run,
        )
        if run_errors:
            errors.extend(run_errors)
            continue
        assert record is not None
        assert map_row is not None
        index.append(record)
        run_id_map_rows.append(map_row)

    if errors:
        print("Ingestion finished with errors:")
        for err in errors:
            print(f"- {err}")

    if not args.dry_run:
        index_path = dest_manifest_dir / "runs_index.jsonl"
        with index_path.open("w", encoding="utf-8") as f:
            for rec in index:
                f.write(json.dumps(rec, sort_keys=False) + "\n")

        run_id_map_path = dest_manifest_dir / "run_id_map.jsonl"
        with run_id_map_path.open("w", encoding="utf-8") as f:
            for row in run_id_map_rows:
                f.write(json.dumps(row, sort_keys=False) + "\n")

        dataset_manifest = {
            "created_at_utc": datetime.now(timezone.utc).isoformat(),
            "family": args.family,
            "run_id_mode": args.run_id_mode,
            "schema": str(args.schema),
            "source_dir": str(args.source_dir),
            "run_count": len(index),
            "error_count": len(errors),
            "run_index_sha256": file_sha256(index_path),
            "run_id_map_sha256": file_sha256(run_id_map_path),
        }
        dump_json(dest_manifest_dir / "dataset_manifest.json", dataset_manifest)

    print(f"Ingested runs: {len(index)}")
    print(f"Errors: {len(errors)}")

    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
