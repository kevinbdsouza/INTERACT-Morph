#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import math
import sys
from collections import Counter
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = PROJECT_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from interact_morph.io_utils import dump_json, load_json, load_json_or_yaml

G = 9.80665


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run baseline regime-map heuristic benchmark (MVP-009).")
    parser.add_argument("--dataset-root", required=True, type=Path)
    parser.add_argument("--config", default=Path("configs/baselines/family_a_heuristic.json"), type=Path)
    parser.add_argument("--split", type=Path, default=None, help="Optional split file from create_split.py")
    parser.add_argument("--output", required=True, type=Path)
    return parser.parse_args()


def compute_velocity_m_s(control: dict[str, Any]) -> float:
    if "impact_velocity_m_s" in control:
        return float(control["impact_velocity_m_s"])
    h_mm = float(control["impact_height_mm"])
    return math.sqrt(2.0 * G * (h_mm / 1000.0))


def compute_dimensionless(metadata: dict[str, Any]) -> dict[str, float]:
    control = metadata["control_parameters"]
    fluid = metadata["fluid_system"]
    rho = float(fluid["core"]["density_kg_m3"])
    mu = float(fluid["core"]["viscosity_pa_s"])
    sigma = float(fluid["interfacial_tension_n_m"])
    l = float(control["droplet_diameter_mm"]) / 1000.0
    v = compute_velocity_m_s(control)

    we = rho * v * v * l / sigma
    oh = mu / math.sqrt(rho * sigma * l)
    bo = rho * G * l * l / sigma
    return {"weber": we, "ohnesorge": oh, "bond": bo}


def predict_regime(dim: dict[str, float], cfg: dict[str, Any]) -> tuple[str, bool]:
    t = cfg["global_thresholds"]
    rules = cfg["regime_rules"]

    if dim["weber"] < float(rules["trapping_if_weber_below"]):
        regime = "trapping"
    elif dim["weber"] > float(rules["rupture_if_weber_above"]):
        regime = "rupture_after_wrap"
    elif dim["ohnesorge"] > float(rules["partial_wrap_if_ohnesorge_above"]):
        regime = "partial_wrapping"
    else:
        regime = str(rules["stable_wrap_default"])

    success = (
        t["weber_success_min"] <= dim["weber"] <= t["weber_success_max"]
        and dim["ohnesorge"] <= t["ohnesorge_max"]
        and dim["bond"] <= t["bond_max"]
    )
    return regime, bool(success)


def binary_accuracy(y_true: list[bool], y_pred: list[bool]) -> float:
    if not y_true:
        return float("nan")
    correct = sum(1 for a, b in zip(y_true, y_pred) if a == b)
    return correct / len(y_true)


def macro_f1(y_true: list[str], y_pred: list[str]) -> float:
    if not y_true:
        return float("nan")
    labels = sorted(set(y_true) | set(y_pred))
    f1s: list[float] = []
    for label in labels:
        tp = sum(1 for a, b in zip(y_true, y_pred) if a == label and b == label)
        fp = sum(1 for a, b in zip(y_true, y_pred) if a != label and b == label)
        fn = sum(1 for a, b in zip(y_true, y_pred) if a == label and b != label)
        precision = tp / (tp + fp) if (tp + fp) else 0.0
        recall = tp / (tp + fn) if (tp + fn) else 0.0
        if precision + recall == 0:
            f1s.append(0.0)
        else:
            f1s.append(2 * precision * recall / (precision + recall))
    return sum(f1s) / len(f1s)


def load_run_ids_from_split(split_path: Path) -> set[str]:
    payload = load_json(split_path)
    test_runs = payload.get("runs", {}).get("test", [])
    return set(test_runs)


def main() -> int:
    args = parse_args()

    cfg = load_json_or_yaml(args.config)
    filter_run_ids: set[str] | None = None
    if args.split:
        filter_run_ids = load_run_ids_from_split(args.split)

    rows: list[dict[str, Any]] = []
    runs_dir = args.dataset_root / "runs"
    for run_dir in sorted(runs_dir.iterdir()):
        if not run_dir.is_dir():
            continue
        metadata_path = run_dir / "metadata.json"
        if not metadata_path.exists():
            continue
        metadata = load_json(metadata_path)
        run_id = metadata.get("run_id")
        if filter_run_ids is not None and run_id not in filter_run_ids:
            continue

        dims = compute_dimensionless(metadata)
        pred_regime, pred_success = predict_regime(dims, cfg)

        row = {
            "run_id": run_id,
            "pred_regime": pred_regime,
            "pred_success": pred_success,
            "true_regime": metadata["outcomes"].get("regime_label"),
            "true_success": metadata["outcomes"].get("encapsulation_success"),
            **dims,
        }
        rows.append(row)

    y_true_regime = [r["true_regime"] for r in rows if r["true_regime"] is not None]
    y_pred_regime = [r["pred_regime"] for r in rows if r["true_regime"] is not None]
    y_true_success = [bool(r["true_success"]) for r in rows if r["true_success"] is not None]
    y_pred_success = [bool(r["pred_success"]) for r in rows if r["true_success"] is not None]

    report = {
        "baseline": cfg.get("name", "baseline"),
        "run_count": len(rows),
        "regime_macro_f1": macro_f1(y_true_regime, y_pred_regime),
        "success_accuracy": binary_accuracy(y_true_success, y_pred_success),
        "true_regime_distribution": dict(Counter(y_true_regime)),
        "pred_regime_distribution": dict(Counter(y_pred_regime)),
    }

    dump_json(args.output, {"report": report, "predictions": rows})

    print(json.dumps(report, indent=2))
    print(f"Wrote baseline report -> {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
