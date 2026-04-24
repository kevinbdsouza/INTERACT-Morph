#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = PROJECT_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from interact_capsules.io_utils import dump_json, load_json


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Create immutable dataset snapshot metadata (MVP-007).")
    parser.add_argument("--dataset-root", required=True, type=Path, help="e.g., data/canonical/family_a")
    parser.add_argument("--name", required=True, help="snapshot name, e.g., family_a_v1")
    parser.add_argument("--output-dir", default=Path("data/canonical/snapshots"), type=Path)
    return parser.parse_args()


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def main() -> int:
    args = parse_args()

    manifest_path = args.dataset_root / "manifests" / "dataset_manifest.json"
    index_path = args.dataset_root / "manifests" / "runs_index.jsonl"

    if not manifest_path.exists() or not index_path.exists():
        print(f"Missing required manifest files under {args.dataset_root / 'manifests'}")
        return 1

    manifest = load_json(manifest_path)
    lines = index_path.read_text(encoding="utf-8").splitlines()
    normalized_index = "\n".join(sorted(line.strip() for line in lines if line.strip()))

    snapshot = {
        "snapshot_name": args.name,
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "dataset_root": str(args.dataset_root),
        "dataset_manifest": manifest,
        "run_count": len([line for line in lines if line.strip()]),
        "run_index_content_sha256": sha256_text(normalized_index),
    }

    out = args.output_dir / f"{args.name}.json"
    dump_json(out, snapshot)
    print(f"Wrote snapshot -> {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
