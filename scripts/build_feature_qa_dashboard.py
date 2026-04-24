#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import math
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = PROJECT_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from interact_capsules.io_utils import dump_json, load_json, load_json_or_yaml


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Generate derived-feature QA dashboard artifacts (MVP-013) with trajectory sanity checks, "
            "summary consistency checks, and outlier flags."
        )
    )
    parser.add_argument("--dataset-root", default=None, type=Path, help="Dataset root (used when --derived-features-index is omitted)")
    parser.add_argument(
        "--derived-features-index",
        default=None,
        type=Path,
        help="Optional JSONL index with run_id and derived_features_path fields",
    )
    parser.add_argument(
        "--features-glob",
        default="runs/*/derived_features.json",
        help="Glob under dataset-root for derived features when index is omitted",
    )
    parser.add_argument("--config", required=True, type=Path, help="Feature QA config JSON/YAML")
    parser.add_argument("--output", required=True, type=Path, help="JSON output report path")
    parser.add_argument("--markdown-output", default=None, type=Path, help="Optional markdown summary path")
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


def quantile(sorted_values: list[float], q: float) -> float:
    if not sorted_values:
        return float("nan")
    if len(sorted_values) == 1:
        return sorted_values[0]
    idx = (len(sorted_values) - 1) * q
    lo = int(math.floor(idx))
    hi = int(math.ceil(idx))
    if lo == hi:
        return sorted_values[lo]
    weight = idx - lo
    return sorted_values[lo] * (1.0 - weight) + sorted_values[hi] * weight


def numeric_stats(values: list[float]) -> dict[str, Any]:
    if not values:
        return {"count": 0}
    ordered = sorted(values)
    n = len(ordered)
    mean = sum(ordered) / n
    variance = sum((x - mean) ** 2 for x in ordered) / n
    return {
        "count": n,
        "min": ordered[0],
        "q25": quantile(ordered, 0.25),
        "median": quantile(ordered, 0.5),
        "q75": quantile(ordered, 0.75),
        "max": ordered[-1],
        "mean": mean,
        "std": math.sqrt(variance),
    }


def path_from_index_row(index_path: Path, row: dict[str, Any]) -> Path | None:
    raw = row.get("derived_features_path")
    if not isinstance(raw, str) or not raw.strip():
        return None
    candidate = Path(raw)
    if candidate.is_absolute():
        return candidate
    if candidate.exists():
        return candidate.resolve()
    return (index_path.parent / candidate).resolve()


def check_monotonic_time(series: list[dict[str, Any]]) -> bool:
    prev = None
    for point in series:
        t_ms = to_float(point.get("t_ms"))
        if t_ms is None:
            continue
        if prev is not None and t_ms < prev:
            return False
        prev = t_ms
    return True


def max_jump(values: list[float]) -> tuple[float, float]:
    if len(values) < 2:
        return 0.0, 0.0
    diffs = [abs(values[i] - values[i - 1]) for i in range(1, len(values))]
    max_diff = max(diffs)
    ordered = sorted(diffs)
    median = ordered[len(ordered) // 2]
    return max_diff, median


def main() -> int:
    args = parse_args()
    config = load_json_or_yaml(args.config)
    if not isinstance(config, dict):
        print(f"Config must be an object: {args.config}")
        return 1

    tolerance_cfg = config.get("tolerance", {})
    if not isinstance(tolerance_cfg, dict):
        tolerance_cfg = {}
    tol_penetration = to_float(tolerance_cfg.get("penetration_depth_max_mm"))
    tol_neck = to_float(tolerance_cfg.get("neck_radius_min_mm"))
    tol_thickness = to_float(tolerance_cfg.get("shell_thickness_mean_um"))
    if tol_penetration is None:
        tol_penetration = 0.05
    if tol_neck is None:
        tol_neck = 0.05
    if tol_thickness is None:
        tol_thickness = 15.0

    jump_cfg = config.get("jump_detection", {})
    if not isinstance(jump_cfg, dict):
        jump_cfg = {}
    jump_factor = to_float(jump_cfg.get("factor"))
    if jump_factor is None:
        jump_factor = 8.0

    abs_min_cfg = jump_cfg.get("absolute_min", {})
    if not isinstance(abs_min_cfg, dict):
        abs_min_cfg = {}
    abs_min_defaults = {
        "penetration_depth_mm": 0.25,
        "neck_radius_mm": 0.25,
        "shell_thickness_um": 40.0,
    }
    abs_min: dict[str, float] = {}
    for key, default in abs_min_defaults.items():
        value = to_float(abs_min_cfg.get(key))
        abs_min[key] = value if value is not None else default

    max_worst_runs = int(config.get("max_reported_worst_runs", 20))

    feature_files: list[tuple[str | None, Path]] = []
    if args.derived_features_index is not None:
        index_rows = load_jsonl(args.derived_features_index)
        for row in index_rows:
            path = path_from_index_row(args.derived_features_index, row)
            if path is None:
                continue
            run_id = row.get("run_id") if isinstance(row.get("run_id"), str) else None
            feature_files.append((run_id, path))
    else:
        if args.dataset_root is None:
            print("Either --dataset-root or --derived-features-index must be provided")
            return 1
        for path in sorted(args.dataset_root.glob(args.features_glob)):
            feature_files.append((None, path))

    if args.max_runs is not None:
        feature_files = feature_files[: max(0, int(args.max_runs))]

    if not feature_files:
        print("No derived feature files found for QA")
        return 1

    issue_counts: Counter[str] = Counter()
    run_rows: list[dict[str, Any]] = []

    summary_penetration: list[float] = []
    summary_neck: list[float] = []
    summary_thickness: list[float] = []
    summary_eccentricity: list[float] = []

    for hinted_run_id, path in feature_files:
        if not path.exists():
            issue_counts["missing_file"] += 1
            run_rows.append(
                {
                    "run_id": hinted_run_id,
                    "path": str(path),
                    "issue_count": 1,
                    "issues": ["missing_file"],
                }
            )
            continue

        payload = load_json(path)
        run_id_raw = payload.get("run_id")
        run_id = run_id_raw if isinstance(run_id_raw, str) else hinted_run_id

        issues: list[str] = []

        events = payload.get("events_ms")
        if not isinstance(events, dict):
            issues.append("missing_events")
        else:
            for event_key in [
                "lamella_onset_ms",
                "first_contact_ms",
                "neck_formation_ms",
                "closure_time_ms",
                "detachment_time_ms",
                "rupture_time_ms",
            ]:
                if event_key not in events:
                    issues.append(f"missing_event:{event_key}")

        summary = payload.get("summary")
        if not isinstance(summary, dict):
            issues.append("missing_summary")
            summary = {}

        trajectories = payload.get("trajectories")
        if not isinstance(trajectories, dict):
            issues.append("missing_trajectories")
            trajectories = {}

        penetration_series = trajectories.get("penetration_depth_mm") if isinstance(trajectories.get("penetration_depth_mm"), list) else []
        neck_series = trajectories.get("neck_radius_mm") if isinstance(trajectories.get("neck_radius_mm"), list) else []
        thickness_series = trajectories.get("shell_thickness_um") if isinstance(trajectories.get("shell_thickness_um"), list) else []

        for name, series in [
            ("penetration_depth_mm", penetration_series),
            ("neck_radius_mm", neck_series),
            ("shell_thickness_um", thickness_series),
        ]:
            if not series:
                issues.append(f"empty_series:{name}")
            if series and not check_monotonic_time(series):
                issues.append(f"non_monotonic_time:{name}")

        penetration_values = [to_float(point.get("value")) for point in penetration_series]
        neck_values = [to_float(point.get("value")) for point in neck_series]
        thickness_values = [to_float(point.get("value")) for point in thickness_series]

        if any(v is None for v in penetration_values):
            issues.append("nan_series:penetration_depth_mm")
        if any(v is None for v in neck_values):
            issues.append("nan_series:neck_radius_mm")
        if any(v is None for v in thickness_values):
            issues.append("nan_series:shell_thickness_um")

        penetration_clean = [float(v) for v in penetration_values if v is not None]
        neck_clean = [float(v) for v in neck_values if v is not None]
        thickness_clean = [float(v) for v in thickness_values if v is not None]

        if any(v < 0 for v in penetration_clean):
            issues.append("negative_value:penetration_depth_mm")
        if any(v < 0 for v in neck_clean):
            issues.append("negative_value:neck_radius_mm")
        if any(v < 0 for v in thickness_clean):
            issues.append("negative_value:shell_thickness_um")

        summary_pen = to_float(summary.get("penetration_depth_max_mm"))
        summary_neck_min = to_float(summary.get("neck_radius_min_mm"))
        summary_thickness_mean = to_float(summary.get("shell_thickness_mean_um"))
        summary_ecc = to_float(summary.get("capsule_eccentricity"))

        if summary_pen is None:
            issues.append("missing_summary:penetration_depth_max_mm")
        if summary_neck_min is None:
            issues.append("missing_summary:neck_radius_min_mm")
        if summary_thickness_mean is None:
            issues.append("missing_summary:shell_thickness_mean_um")
        if summary_ecc is None:
            issues.append("missing_summary:capsule_eccentricity")

        if summary_pen is not None:
            summary_penetration.append(summary_pen)
        if summary_neck_min is not None:
            summary_neck.append(summary_neck_min)
        if summary_thickness_mean is not None:
            summary_thickness.append(summary_thickness_mean)
        if summary_ecc is not None:
            summary_eccentricity.append(summary_ecc)

        if summary_pen is not None and penetration_clean:
            if abs(max(penetration_clean) - summary_pen) > tol_penetration:
                issues.append("summary_mismatch:penetration_depth_max_mm")

        if summary_neck_min is not None and neck_clean:
            if abs(min(neck_clean) - summary_neck_min) > tol_neck:
                issues.append("summary_mismatch:neck_radius_min_mm")

        if summary_thickness_mean is not None and thickness_clean:
            if abs((sum(thickness_clean) / len(thickness_clean)) - summary_thickness_mean) > tol_thickness:
                issues.append("summary_mismatch:shell_thickness_mean_um")

        if summary_ecc is not None and not (0.0 <= summary_ecc <= 1.0):
            issues.append("out_of_range:capsule_eccentricity")

        for series_name, values in [
            ("penetration_depth_mm", penetration_clean),
            ("neck_radius_mm", neck_clean),
            ("shell_thickness_um", thickness_clean),
        ]:
            max_diff, median_diff = max_jump(values)
            baseline = max(abs_min[series_name], jump_factor * median_diff)
            if max_diff > baseline:
                issues.append(f"abrupt_jump:{series_name}")

        for issue in issues:
            issue_counts[issue] += 1

        run_rows.append(
            {
                "run_id": run_id,
                "path": str(path),
                "issue_count": len(issues),
                "issues": issues,
            }
        )

    run_rows.sort(key=lambda row: (-int(row["issue_count"]), str(row.get("run_id") or "")))

    report = {
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "task_id": "MVP-013",
        "config": str(args.config),
        "derived_features_index": str(args.derived_features_index) if args.derived_features_index is not None else None,
        "dataset_root": str(args.dataset_root) if args.dataset_root is not None else None,
        "runs_scanned": len(run_rows),
        "runs_with_issues": sum(1 for row in run_rows if row["issue_count"] > 0),
        "issue_counts": dict(issue_counts),
        "thresholds": {
            "summary_tolerance": {
                "penetration_depth_max_mm": tol_penetration,
                "neck_radius_min_mm": tol_neck,
                "shell_thickness_mean_um": tol_thickness,
            },
            "jump_detection": {
                "factor": jump_factor,
                "absolute_min": abs_min,
            },
        },
        "summary_statistics": {
            "penetration_depth_max_mm": numeric_stats(summary_penetration),
            "neck_radius_min_mm": numeric_stats(summary_neck),
            "shell_thickness_mean_um": numeric_stats(summary_thickness),
            "capsule_eccentricity": numeric_stats(summary_eccentricity),
        },
        "worst_runs": run_rows[: max(1, max_worst_runs)],
    }

    dump_json(args.output, report)

    if args.markdown_output is not None:
        lines: list[str] = []
        lines.append("# Feature QA Dashboard (MVP-013)")
        lines.append("")
        lines.append(f"- Generated: {report['created_at_utc']}")
        lines.append(f"- Runs scanned: {report['runs_scanned']}")
        lines.append(f"- Runs with issues: {report['runs_with_issues']}")
        lines.append("")
        lines.append("## Issue Counts")
        lines.append("")
        lines.append("| Issue | Count |")
        lines.append("|---|---:|")
        if issue_counts:
            for issue, count in sorted(issue_counts.items(), key=lambda item: (-item[1], item[0])):
                lines.append(f"| {issue} | {count} |")
        else:
            lines.append("| none | 0 |")
        lines.append("")
        lines.append("## Worst Runs")
        lines.append("")
        lines.append("| Run ID | Issue Count | Issues |")
        lines.append("|---|---:|---|")
        for row in report["worst_runs"]:
            run_id = row.get("run_id") or "unknown"
            issues_text = ", ".join(row.get("issues", []))
            lines.append(f"| {run_id} | {row['issue_count']} | {issues_text} |")
        args.markdown_output.parent.mkdir(parents=True, exist_ok=True)
        args.markdown_output.write_text("\n".join(lines) + "\n", encoding="utf-8")

    print(f"Wrote feature QA report -> {args.output}")
    if args.markdown_output is not None:
        print(f"Wrote feature QA markdown -> {args.markdown_output}")
    print(f"Runs scanned: {report['runs_scanned']} | runs with issues: {report['runs_with_issues']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
