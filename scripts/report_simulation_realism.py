#!/usr/bin/env python3
from __future__ import annotations

import argparse
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

from interact_morph.io_utils import dump_json, load_json


NUMERIC_FIELDS: dict[str, tuple[str, ...]] = {
    "impact_velocity_m_s": ("control_parameters", "impact_velocity_m_s"),
    "droplet_diameter_mm": ("control_parameters", "droplet_diameter_mm"),
    "shell_outer_diameter_mm": ("control_parameters", "shell_outer_diameter_mm"),
    "core_density_kg_m3": ("fluid_system", "core", "density_kg_m3"),
    "core_viscosity_pa_s": ("fluid_system", "core", "viscosity_pa_s"),
    "interfacial_tension_n_m": ("fluid_system", "interfacial_tension_n_m"),
    "shell_thickness_mean_um": ("outcomes", "shell_thickness_mean_um"),
    "capsule_eccentricity": ("outcomes", "capsule_eccentricity"),
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build MVP-018 simulation realism comparison report.")
    parser.add_argument("--simulation-dataset-root", required=True, type=Path, help="e.g., data/simulation/family_a/corpus/<name>")
    parser.add_argument(
        "--experimental-dataset-root",
        type=Path,
        default=None,
        help="Optional canonical experimental dataset root for direct sim-vs-exp comparison",
    )
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--max-runs", type=int, default=None)
    return parser.parse_args()


def safe_get(payload: dict[str, Any], path: tuple[str, ...]) -> Any:
    cur: Any = payload
    for key in path:
        if not isinstance(cur, dict) or key not in cur:
            return None
        cur = cur[key]
    return cur


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
        "median": quantile(ordered, 0.50),
        "q75": quantile(ordered, 0.75),
        "max": ordered[-1],
        "mean": mean,
        "std": math.sqrt(variance),
    }


def cdf_distance(a: list[float], b: list[float]) -> float | None:
    if not a or not b:
        return None
    a_sorted = sorted(a)
    b_sorted = sorted(b)
    points = sorted(set(a_sorted + b_sorted))
    i = 0
    j = 0
    n_a = len(a_sorted)
    n_b = len(b_sorted)
    max_gap = 0.0
    for point in points:
        while i < n_a and a_sorted[i] <= point:
            i += 1
        while j < n_b and b_sorted[j] <= point:
            j += 1
        gap = abs((i / n_a) - (j / n_b))
        if gap > max_gap:
            max_gap = gap
    return max_gap


def l1_distribution_distance(a: Counter[str], b: Counter[str]) -> float | None:
    n_a = sum(a.values())
    n_b = sum(b.values())
    if n_a == 0 or n_b == 0:
        return None
    labels = sorted(set(a.keys()) | set(b.keys()))
    return sum(abs((a[label] / n_a) - (b[label] / n_b)) for label in labels)


def load_metadata_rows(dataset_root: Path, max_runs: int | None) -> list[dict[str, Any]]:
    runs_root = dataset_root / "runs"
    rows: list[dict[str, Any]] = []
    if not runs_root.exists():
        return rows
    for run_dir in sorted(runs_root.iterdir()):
        if not run_dir.is_dir():
            continue
        metadata_path = run_dir / "metadata.json"
        if not metadata_path.exists():
            continue
        rows.append(load_json(metadata_path))
        if max_runs is not None and len(rows) >= max_runs:
            break
    return rows


def summarize_dataset(rows: list[dict[str, Any]]) -> dict[str, Any]:
    numeric_values: dict[str, list[float]] = {key: [] for key in NUMERIC_FIELDS}
    regime_counter: Counter[str] = Counter()
    failure_counter: Counter[str] = Counter()
    success_count = 0

    for row in rows:
        outcomes = row.get("outcomes", {})
        regime = outcomes.get("regime_label")
        failure_mode = outcomes.get("failure_mode")
        if isinstance(regime, str):
            regime_counter[regime] += 1
        if isinstance(failure_mode, str):
            failure_counter[failure_mode] += 1
        if outcomes.get("encapsulation_success") is True:
            success_count += 1

        for key, path in NUMERIC_FIELDS.items():
            value = safe_get(row, path)
            if isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(float(value)):
                numeric_values[key].append(float(value))

    numeric_summary = {key: numeric_stats(values) for key, values in numeric_values.items()}
    n = len(rows)
    return {
        "run_count": n,
        "success_rate": (success_count / n) if n else None,
        "regime_distribution": dict(regime_counter),
        "failure_mode_distribution": dict(failure_counter),
        "numeric": numeric_summary,
    }


def compare_summaries(sim_rows: list[dict[str, Any]], exp_rows: list[dict[str, Any]]) -> dict[str, Any]:
    sim_numeric: dict[str, list[float]] = {key: [] for key in NUMERIC_FIELDS}
    exp_numeric: dict[str, list[float]] = {key: [] for key in NUMERIC_FIELDS}

    sim_regime = Counter(
        str(row.get("outcomes", {}).get("regime_label"))
        for row in sim_rows
        if isinstance(row.get("outcomes", {}).get("regime_label"), str)
    )
    exp_regime = Counter(
        str(row.get("outcomes", {}).get("regime_label"))
        for row in exp_rows
        if isinstance(row.get("outcomes", {}).get("regime_label"), str)
    )

    for row in sim_rows:
        for key, path in NUMERIC_FIELDS.items():
            value = safe_get(row, path)
            if isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(float(value)):
                sim_numeric[key].append(float(value))

    for row in exp_rows:
        for key, path in NUMERIC_FIELDS.items():
            value = safe_get(row, path)
            if isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(float(value)):
                exp_numeric[key].append(float(value))

    field_comparison: dict[str, Any] = {}
    for key in NUMERIC_FIELDS:
        sim_values = sim_numeric[key]
        exp_values = exp_numeric[key]
        sim_mean = sum(sim_values) / len(sim_values) if sim_values else None
        exp_mean = sum(exp_values) / len(exp_values) if exp_values else None
        field_comparison[key] = {
            "sim_count": len(sim_values),
            "exp_count": len(exp_values),
            "mean_delta": (sim_mean - exp_mean) if sim_mean is not None and exp_mean is not None else None,
            "cdf_distance": cdf_distance(sim_values, exp_values),
        }

    return {
        "numeric_field_comparison": field_comparison,
        "regime_distribution_l1_distance": l1_distribution_distance(sim_regime, exp_regime),
        "notes": "Lower cdf_distance and L1 values indicate closer simulation-experiment alignment.",
    }


def main() -> int:
    args = parse_args()

    sim_rows = load_metadata_rows(args.simulation_dataset_root, args.max_runs)
    if not sim_rows:
        print(f"No simulation metadata rows found under {args.simulation_dataset_root / 'runs'}")
        return 1

    report: dict[str, Any] = {
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "simulation_dataset_root": str(args.simulation_dataset_root),
        "simulation_summary": summarize_dataset(sim_rows),
    }

    if args.experimental_dataset_root is not None:
        exp_rows = load_metadata_rows(args.experimental_dataset_root, args.max_runs)
        report["experimental_dataset_root"] = str(args.experimental_dataset_root)
        report["experimental_summary"] = summarize_dataset(exp_rows)
        report["comparison"] = compare_summaries(sim_rows, exp_rows)
    else:
        report["comparison"] = None
        report["notes"] = "Experimental dataset not supplied; generated simulation-only summary."

    dump_json(args.output, report)
    print(f"Wrote realism report -> {args.output}")
    print(f"Simulation rows: {len(sim_rows)}")
    if args.experimental_dataset_root is not None:
        print(f"Experimental rows: {report['experimental_summary']['run_count']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
