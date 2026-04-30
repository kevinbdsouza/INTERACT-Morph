#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import sys
from pathlib import Path
from typing import Iterator

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = PROJECT_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from interact_morph.io_utils import load_json_or_yaml
from interact_morph.run_id_utils import (
    canonicalize_run_id,
    ensure_unique_run_id,
    extract_source_run_id,
    normalize_token,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build raw-run inventory CSV (MVP-004).")
    parser.add_argument("--source-dir", required=True, type=Path, help="Raw runs directory")
    parser.add_argument("--output", required=True, type=Path, help="Output CSV path")
    parser.add_argument(
        "--family",
        default="A",
        choices=["A", "B", "C"],
        help="Fallback family for canonical ID derivation when metadata is missing/incomplete",
    )
    return parser.parse_args()


def find_metadata_file(run_dir: Path) -> Path | None:
    for name in ("metadata.json", "metadata.yaml", "metadata.yml"):
        path = run_dir / name
        if path.exists():
            return path
    return None


def find_video_file(run_dir: Path) -> Path | None:
    for ext in ("*.mp4", "*.mov", "*.avi", "*.mkv"):
        hits = list(run_dir.glob(ext))
        if hits:
            return hits[0]
    return None


def iter_runs(source_dir: Path) -> Iterator[Path]:
    for child in sorted(source_dir.iterdir()):
        if child.is_dir():
            yield child


def main() -> int:
    args = parse_args()
    args.output.parent.mkdir(parents=True, exist_ok=True)

    fieldnames = [
        "run_dir",
        "run_id",
        "source_run_id",
        "canonical_run_id",
        "canonical_collision_resolved",
        "family",
        "fluid_combination_id",
        "capture_timestamp",
        "has_metadata",
        "has_video",
        "video_name",
        "notes",
    ]

    rows = []
    used_canonical_ids: set[str] = set()
    for run_dir in iter_runs(args.source_dir):
        metadata_file = find_metadata_file(run_dir)
        video_file = find_video_file(run_dir)
        notes: list[str] = []

        row = {
            "run_dir": str(run_dir),
            "run_id": "",
            "source_run_id": "",
            "canonical_run_id": "",
            "canonical_collision_resolved": False,
            "family": "",
            "fluid_combination_id": "",
            "capture_timestamp": "",
            "has_metadata": bool(metadata_file),
            "has_video": bool(video_file),
            "video_name": video_file.name if video_file else "",
            "notes": "",
        }

        if metadata_file:
            try:
                data = load_json_or_yaml(metadata_file)
            except Exception as exc:  # noqa: BLE001
                notes.append(f"metadata_parse_error:{exc.__class__.__name__}")
                data = {}
            row["source_run_id"] = extract_source_run_id(data, run_dir.name)
            family_value = str(data.get("family", "")).strip().upper()
            if not family_value:
                family_value = args.family
                notes.append("family_missing_used_default")
            row["family"] = family_value
            row["fluid_combination_id"] = data.get("fluid_combination_id", "")
            row["capture_timestamp"] = data.get("capture_timestamp", "")
        else:
            row["source_run_id"] = run_dir.name
            row["family"] = args.family
            notes.append("metadata_missing_used_directory_name")

        family_for_id = normalize_token(str(row["family"]))[:1] or args.family
        canonical_base = canonicalize_run_id(
            family=family_for_id,
            source_run_id=row["source_run_id"],
            run_dir_name=run_dir.name,
        )
        canonical_id, collision = ensure_unique_run_id(
            candidate=canonical_base,
            used_ids=used_canonical_ids,
            disambiguator=str(run_dir.resolve()),
        )
        row["canonical_run_id"] = canonical_id
        row["canonical_collision_resolved"] = collision
        row["run_id"] = canonical_id
        if collision:
            notes.append("canonical_id_collision_resolved")
        row["notes"] = ";".join(notes)

        rows.append(row)

    with args.output.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    print(f"Wrote inventory for {len(rows)} run directories -> {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
