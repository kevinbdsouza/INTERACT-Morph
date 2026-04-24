#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import math
import sys
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = PROJECT_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from interact_capsules.io_utils import dump_json, load_json, load_json_or_yaml

EVENT_KEYS = [
    "lamella_onset_ms",
    "first_contact_ms",
    "neck_formation_ms",
    "closure_time_ms",
    "detachment_time_ms",
    "rupture_time_ms",
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Extract deterministic trajectory features from contour-observation rows and "
            "emit derived-features artifacts (MVP-012)."
        )
    )
    parser.add_argument("--dataset-root", required=True, type=Path, help="Canonical or simulation dataset root")
    parser.add_argument(
        "--contours",
        required=True,
        type=Path,
        help=(
            "JSONL contour observations with fields run_id, frame_index/t_ms, "
            "penetration_depth_px, neck_radius_px, shell_outer_radius_px, shell_inner_radius_px"
        ),
    )
    parser.add_argument("--config", required=True, type=Path, help="Contour extraction config JSON/YAML")
    parser.add_argument(
        "--output-dir",
        default=Path("data/canonical/family_a/manifests/derived_features_from_contours"),
        type=Path,
        help="Output directory for per-run derived features and manifest",
    )
    parser.add_argument(
        "--model-version",
        default=None,
        help="Optional segmentation model version stamp for derived features",
    )
    parser.add_argument("--max-runs", default=None, type=int)
    return parser.parse_args()


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for idx, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        text = line.strip()
        if not text:
            continue
        payload = json.loads(text)
        if not isinstance(payload, dict):
            raise ValueError(f"{path}:{idx} must contain JSON objects")
        rows.append(payload)
    return rows


def dump_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        for row in rows:
            f.write(json.dumps(row, sort_keys=False) + "\n")


def to_float(value: Any) -> float | None:
    if isinstance(value, bool):
        return 1.0 if value else 0.0
    if isinstance(value, (int, float)):
        v = float(value)
        return v if math.isfinite(v) else None
    if isinstance(value, str):
        text = value.strip()
        if not text:
            return None
        try:
            v = float(text)
        except ValueError:
            return None
        return v if math.isfinite(v) else None
    return None


def first_time(values: list[tuple[float, float]], threshold: float) -> float | None:
    for t_ms, value in values:
        if value >= threshold:
            return t_ms
    return None


def safe_round(value: float, places: int = 6) -> float:
    return round(float(value), places)


def load_labels_events(labels_path: Path) -> dict[str, float | None] | None:
    if not labels_path.exists():
        return None
    labels = load_json(labels_path)
    events = labels.get("events_ms")
    if not isinstance(events, dict):
        return None
    payload: dict[str, float | None] = {}
    for key in EVENT_KEYS:
        raw = events.get(key)
        if raw is None:
            payload[key] = None
        else:
            parsed = to_float(raw)
            payload[key] = parsed
    return payload


def infer_events(
    penetration_series: list[tuple[float, float]],
    neck_series: list[tuple[float, float]],
    lamella_threshold_mm: float,
    closure_neck_radius_mm: float,
    closure_min_increase_mm: float,
) -> dict[str, float | None]:
    lamella = first_time(penetration_series, lamella_threshold_mm)
    first_contact = first_time(penetration_series, max(0.0, lamella_threshold_mm / 2.0))

    neck_min_value = float("inf")
    neck_min_time: float | None = None
    for t_ms, value in neck_series:
        if value < neck_min_value:
            neck_min_value = value
            neck_min_time = t_ms

    closure_time: float | None = None
    if neck_min_time is not None:
        target_neck = max(closure_neck_radius_mm, neck_min_value + closure_min_increase_mm)
        for t_ms, value in neck_series:
            if t_ms >= neck_min_time and value >= target_neck:
                closure_time = t_ms
                break

    detachment = penetration_series[-1][0] if penetration_series else None

    return {
        "lamella_onset_ms": lamella,
        "first_contact_ms": first_contact,
        "neck_formation_ms": neck_min_time,
        "closure_time_ms": closure_time,
        "detachment_time_ms": detachment,
        "rupture_time_ms": None,
    }


def main() -> int:
    args = parse_args()
    config = load_json_or_yaml(args.config)
    if not isinstance(config, dict):
        print(f"Config must be an object: {args.config}")
        return 1

    config_name = str(config.get("name", "family_a_contour_extraction_v1"))
    schema_version = str(config.get("schema_version", "1.0.1"))
    pixel_to_mm = to_float(config.get("pixel_to_mm"))
    default_fps = to_float(config.get("default_frame_rate_fps"))
    if pixel_to_mm is None or pixel_to_mm <= 0:
        print("Config field pixel_to_mm must be > 0")
        return 1
    if default_fps is None or default_fps <= 0:
        default_fps = 5000.0

    heuristic_cfg = config.get("heuristic_events", {})
    if not isinstance(heuristic_cfg, dict):
        heuristic_cfg = {}
    lamella_threshold_mm = to_float(heuristic_cfg.get("lamella_onset_penetration_mm"))
    closure_neck_radius_mm = to_float(heuristic_cfg.get("closure_neck_radius_mm"))
    closure_min_increase_mm = to_float(heuristic_cfg.get("closure_min_increase_mm"))
    if lamella_threshold_mm is None:
        lamella_threshold_mm = 0.05
    if closure_neck_radius_mm is None:
        closure_neck_radius_mm = 0.55
    if closure_min_increase_mm is None:
        closure_min_increase_mm = 0.05

    rows = load_jsonl(args.contours)
    if not rows:
        print(f"No contour observations found in {args.contours}")
        return 1

    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    parse_errors: list[str] = []
    for idx, row in enumerate(rows, start=1):
        run_id = row.get("run_id")
        if not isinstance(run_id, str) or not run_id.strip():
            parse_errors.append(f"row {idx}: missing valid run_id")
            continue
        grouped[run_id.strip()].append(row)

    if parse_errors:
        for err in parse_errors[:30]:
            print(f"- {err}")
        if len(parse_errors) > 30:
            print(f"... {len(parse_errors) - 30} additional parsing issue(s)")

    run_ids = sorted(grouped.keys())
    if args.max_runs is not None:
        run_ids = run_ids[: max(0, int(args.max_runs))]

    model_version = args.model_version or f"{config_name}:contour_extractor"

    written_rows: list[dict[str, Any]] = []
    failed_runs: list[dict[str, Any]] = []
    now_utc = datetime.now(timezone.utc).isoformat()

    for run_id in run_ids:
        run_rows = grouped[run_id]
        normalized_rows: list[dict[str, float]] = []

        run_dir = args.dataset_root / "runs" / run_id
        metadata_path = run_dir / "metadata.json"
        labels_path = run_dir / "labels.json"

        source_video = "video.mp4"
        frame_rate_fps = default_fps
        if metadata_path.exists():
            metadata = load_json(metadata_path)
            source_video_candidate = metadata.get("asset_paths", {}).get("video_relpath")
            if isinstance(source_video_candidate, str) and source_video_candidate.strip():
                source_video = source_video_candidate
            fps_candidate = to_float(metadata.get("source", {}).get("frame_rate_fps"))
            if fps_candidate is not None and fps_candidate > 0:
                frame_rate_fps = fps_candidate

        for row in run_rows:
            frame_idx = row.get("frame_index")
            frame_idx_value = int(frame_idx) if isinstance(frame_idx, int) else None
            t_ms = to_float(row.get("t_ms"))
            if t_ms is None:
                if frame_idx_value is None:
                    continue
                t_ms = (frame_idx_value / frame_rate_fps) * 1000.0

            penetration_px = to_float(row.get("penetration_depth_px"))
            neck_px = to_float(row.get("neck_radius_px"))
            outer_px = to_float(row.get("shell_outer_radius_px"))
            inner_px = to_float(row.get("shell_inner_radius_px"))
            major_px = to_float(row.get("capsule_major_axis_px"))
            minor_px = to_float(row.get("capsule_minor_axis_px"))

            if any(v is None for v in [penetration_px, neck_px, outer_px, inner_px, major_px, minor_px]):
                continue

            normalized_rows.append(
                {
                    "t_ms": float(t_ms),
                    "penetration_px": float(penetration_px),
                    "neck_px": float(neck_px),
                    "outer_px": float(outer_px),
                    "inner_px": float(inner_px),
                    "major_px": float(major_px),
                    "minor_px": float(minor_px),
                }
            )

        if not normalized_rows:
            failed_runs.append({"run_id": run_id, "reason": "no valid contour rows"})
            continue

        normalized_rows.sort(key=lambda row: row["t_ms"])

        penetration_series: list[tuple[float, float]] = []
        neck_series: list[tuple[float, float]] = []
        thickness_series: list[tuple[float, float]] = []
        eccentricity_values: list[float] = []

        for row in normalized_rows:
            t_ms = row["t_ms"]
            penetration_mm = max(0.0, row["penetration_px"] * pixel_to_mm)
            neck_mm = max(0.0, row["neck_px"] * pixel_to_mm)
            thickness_um = max(0.0, (row["outer_px"] - row["inner_px"]) * pixel_to_mm * 1000.0)

            major = max(1e-9, row["major_px"])
            minor = max(0.0, row["minor_px"])
            minor_clamped = min(minor, major)
            eccentricity = max(0.0, min(1.0, 1.0 - (minor_clamped / major)))
            eccentricity_values.append(eccentricity)

            penetration_series.append((t_ms, penetration_mm))
            neck_series.append((t_ms, neck_mm))
            thickness_series.append((t_ms, thickness_um))

        labels_events = load_labels_events(labels_path)
        if labels_events is not None:
            events = labels_events
        else:
            events = infer_events(
                penetration_series=penetration_series,
                neck_series=neck_series,
                lamella_threshold_mm=lamella_threshold_mm,
                closure_neck_radius_mm=closure_neck_radius_mm,
                closure_min_increase_mm=closure_min_increase_mm,
            )

        penetration_values = [v for _, v in penetration_series]
        neck_values = [v for _, v in neck_series]
        thickness_values = [v for _, v in thickness_series]

        if not penetration_values or not neck_values or not thickness_values:
            failed_runs.append({"run_id": run_id, "reason": "empty trajectory after normalization"})
            continue

        features = {
            "schema_version": schema_version,
            "run_id": run_id,
            "source_video": source_video,
            "frame_rate_fps": frame_rate_fps,
            "segmentation_model_version": model_version,
            "extraction_timestamp": now_utc,
            "events_ms": {key: events.get(key) for key in EVENT_KEYS},
            "summary": {
                "penetration_depth_max_mm": safe_round(max(penetration_values), 6),
                "neck_radius_min_mm": safe_round(min(neck_values), 6),
                "shell_thickness_mean_um": safe_round(sum(thickness_values) / len(thickness_values), 6),
                "capsule_eccentricity": safe_round(max(eccentricity_values) if eccentricity_values else 0.0, 6),
            },
            "trajectories": {
                "penetration_depth_mm": [
                    {"t_ms": safe_round(t_ms, 6), "value": safe_round(value, 6)} for t_ms, value in penetration_series
                ],
                "neck_radius_mm": [
                    {"t_ms": safe_round(t_ms, 6), "value": safe_round(value, 6)} for t_ms, value in neck_series
                ],
                "shell_thickness_um": [
                    {"t_ms": safe_round(t_ms, 6), "value": safe_round(value, 6)} for t_ms, value in thickness_series
                ],
            },
        }

        out_path = args.output_dir / "by_run" / f"{run_id}.derived_features.json"
        dump_json(out_path, features)

        written_rows.append(
            {
                "run_id": run_id,
                "derived_features_path": str(Path("by_run") / f"{run_id}.derived_features.json"),
                "n_frames": len(normalized_rows),
                "events_source": "labels" if labels_events is not None else "heuristic",
            }
        )

    index_path = args.output_dir / "derived_features_index.jsonl"
    report_path = args.output_dir / "extraction_report.json"
    dump_jsonl(index_path, written_rows)
    dump_json(
        report_path,
        {
            "created_at_utc": now_utc,
            "task_id": "MVP-012",
            "dataset_root": str(args.dataset_root),
            "contours": str(args.contours),
            "config": str(args.config),
            "model_version": model_version,
            "runs_written": len(written_rows),
            "runs_failed": len(failed_runs),
            "failures": failed_runs,
            "index": str(index_path),
        },
    )

    print(f"Wrote derived-features index -> {index_path}")
    print(f"Wrote extraction report -> {report_path}")
    print(f"Runs written: {len(written_rows)} | runs failed: {len(failed_runs)}")
    return 0 if written_rows else 1


if __name__ == "__main__":
    raise SystemExit(main())
