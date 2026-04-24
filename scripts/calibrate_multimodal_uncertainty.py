#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import math
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = PROJECT_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from interact_capsules.io_utils import dump_json, load_json_or_yaml

EPS = 1e-12


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Calibrate uncertainty from model prediction artifacts (MVP-023). "
            "Fits temperature scaling and optional isotonic calibration."
        )
    )
    parser.add_argument("--predictions", required=True, type=Path, help="Path to *.predictions.jsonl")
    parser.add_argument(
        "--config",
        required=True,
        type=Path,
        help="Calibration config JSON/YAML",
    )
    parser.add_argument("--output", required=True, type=Path, help="Calibration report JSON path")
    parser.add_argument(
        "--calibrated-predictions-output",
        default=None,
        type=Path,
        help="Optional output path for predictions JSONL augmented with calibrated probabilities",
    )
    return parser.parse_args()


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as f:
        for idx, line in enumerate(f, start=1):
            text = line.strip()
            if not text:
                continue
            try:
                payload = json.loads(text)
            except json.JSONDecodeError as exc:
                raise ValueError(f"{path}:{idx}: invalid JSONL ({exc})") from exc
            if not isinstance(payload, dict):
                raise ValueError(f"{path}:{idx}: expected JSON object")
            rows.append(payload)
    return rows


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        for row in rows:
            f.write(json.dumps(row, sort_keys=False) + "\n")


def to_float(value: Any) -> float | None:
    if isinstance(value, bool):
        return 1.0 if value else 0.0
    if isinstance(value, (int, float)):
        x = float(value)
        return x if math.isfinite(x) else None
    if isinstance(value, str):
        text = value.strip()
        if not text:
            return None
        try:
            x = float(text)
        except ValueError:
            return None
        return x if math.isfinite(x) else None
    return None


def clamp_prob(p: float) -> float:
    if p < EPS:
        return EPS
    if p > 1.0 - EPS:
        return 1.0 - EPS
    return p


def sigmoid(x: float) -> float:
    if x >= 0:
        z = math.exp(-x)
        return 1.0 / (1.0 + z)
    z = math.exp(x)
    return z / (1.0 + z)


def has_both_classes(labels: list[int]) -> bool:
    return len(set(labels)) >= 2


def mean_log_loss(labels: list[int], probs: list[float]) -> float:
    if not labels:
        return float("nan")
    total = 0.0
    for y, p in zip(labels, probs):
        q = clamp_prob(p)
        total += -(y * math.log(q) + (1 - y) * math.log(1.0 - q))
    return total / len(labels)


def mean_brier(labels: list[int], probs: list[float]) -> float:
    if not labels:
        return float("nan")
    return sum((p - y) ** 2 for y, p in zip(labels, probs)) / len(labels)


def reliability_bins(labels: list[int], probs: list[float], num_bins: int) -> tuple[float, list[dict[str, Any]]]:
    if not labels:
        return float("nan"), []
    bins: list[list[tuple[int, float]]] = [[] for _ in range(num_bins)]
    for y, p in zip(labels, probs):
        p_clamped = min(1.0, max(0.0, p))
        idx = min(num_bins - 1, int(p_clamped * num_bins))
        bins[idx].append((y, p_clamped))

    total_count = len(labels)
    ece = 0.0
    summary: list[dict[str, Any]] = []
    for idx, bucket in enumerate(bins):
        lower = idx / num_bins
        upper = (idx + 1) / num_bins
        if not bucket:
            summary.append(
                {
                    "bin_index": idx,
                    "bin_start": lower,
                    "bin_end": upper,
                    "count": 0,
                    "mean_probability": None,
                    "empirical_rate": None,
                    "abs_gap": None,
                }
            )
            continue

        count = len(bucket)
        mean_prob = sum(p for _, p in bucket) / count
        empirical = sum(y for y, _ in bucket) / count
        gap = abs(mean_prob - empirical)
        ece += (count / total_count) * gap
        summary.append(
            {
                "bin_index": idx,
                "bin_start": lower,
                "bin_end": upper,
                "count": count,
                "mean_probability": mean_prob,
                "empirical_rate": empirical,
                "abs_gap": gap,
            }
        )

    return ece, summary


def build_metric_block(examples: list[dict[str, Any]], prob_key: str, num_bins: int) -> dict[str, Any]:
    def compute(rows: list[dict[str, Any]]) -> dict[str, Any]:
        labels = [int(r["label"]) for r in rows]
        probs = [float(r[prob_key]) for r in rows]
        if not labels:
            return {
                "count": 0,
                "positive_rate": None,
                "log_loss": None,
                "brier": None,
                "ece": None,
                "reliability_bins": [],
            }
        ece, bins = reliability_bins(labels, probs, num_bins=num_bins)
        return {
            "count": len(labels),
            "positive_rate": (sum(labels) / len(labels)) if labels else None,
            "log_loss": mean_log_loss(labels, probs),
            "brier": mean_brier(labels, probs),
            "ece": ece,
            "reliability_bins": bins,
        }

    by_split: dict[str, Any] = {}
    split_names = sorted({str(r["split"]) for r in examples})
    for split_name in split_names:
        by_split[split_name] = compute([r for r in examples if r["split"] == split_name])

    return {
        "overall": compute(examples),
        "by_split": by_split,
    }


def logspace(min_value: float, max_value: float, steps: int) -> list[float]:
    if min_value <= 0 or max_value <= 0:
        raise ValueError("temperature grid min/max must be > 0")
    if steps <= 1:
        return [min_value]
    log_min = math.log(min_value)
    log_max = math.log(max_value)
    return [math.exp(log_min + (log_max - log_min) * i / (steps - 1)) for i in range(steps)]


def fit_temperature(
    fit_rows: list[dict[str, Any]],
    grid_min: float,
    grid_max: float,
    grid_steps: int,
) -> tuple[float, float, float, list[float]]:
    labels = [int(r["label"]) for r in fit_rows]
    scores = [float(r["score"]) for r in fit_rows]
    candidate_temps = logspace(grid_min, grid_max, grid_steps)

    baseline_probs = [sigmoid(score) for score in scores]
    baseline_loss = mean_log_loss(labels, baseline_probs)

    best_t = 1.0
    best_loss = baseline_loss
    for temp in candidate_temps:
        probs = [sigmoid(score / temp) for score in scores]
        loss = mean_log_loss(labels, probs)
        if loss < best_loss:
            best_loss = loss
            best_t = temp
    return best_t, baseline_loss, best_loss, candidate_temps


def fit_isotonic(probabilities: list[float], labels: list[int]) -> dict[str, Any] | None:
    if len(probabilities) != len(labels) or not probabilities:
        return None

    pairs = sorted((float(p), int(y)) for p, y in zip(probabilities, labels))
    blocks: list[dict[str, Any]] = []
    for x, y in pairs:
        blocks.append({"x_low": x, "x_high": x, "sum_y": float(y), "count": 1})
        while len(blocks) >= 2:
            left = blocks[-2]
            right = blocks[-1]
            left_avg = left["sum_y"] / left["count"]
            right_avg = right["sum_y"] / right["count"]
            if left_avg <= right_avg:
                break
            merged = {
                "x_low": left["x_low"],
                "x_high": right["x_high"],
                "sum_y": left["sum_y"] + right["sum_y"],
                "count": left["count"] + right["count"],
            }
            blocks = blocks[:-2]
            blocks.append(merged)

    thresholds: list[float] = []
    values: list[float] = []
    for block in blocks:
        thresholds.append(float(block["x_high"]))
        values.append(float(block["sum_y"]) / float(block["count"]))

    return {
        "thresholds": thresholds,
        "values": values,
        "x_min": thresholds[0],
        "x_max": thresholds[-1],
    }


def apply_isotonic(probability: float, model: dict[str, Any]) -> float:
    p = min(1.0, max(0.0, probability))
    thresholds = model["thresholds"]
    values = model["values"]
    for threshold, value in zip(thresholds, values):
        if p <= threshold:
            return float(value)
    return float(values[-1])


def choose_fit_rows(
    examples: list[dict[str, Any]],
    preferred_split: str,
    min_fit_rows: int,
) -> tuple[list[dict[str, Any]], str, str | None]:
    split_order = [preferred_split, "val", "train", "test", "all"]
    seen: set[str] = set()
    note: str | None = None

    for split_name in split_order:
        if split_name in seen:
            continue
        seen.add(split_name)
        rows = examples if split_name == "all" else [r for r in examples if r["split"] == split_name]
        labels = [int(r["label"]) for r in rows]
        if len(rows) >= min_fit_rows and has_both_classes(labels):
            if split_name != preferred_split:
                note = (
                    f"preferred fit split '{preferred_split}' did not have enough rows with both classes; "
                    f"used '{split_name}'"
                )
            return rows, split_name, note

    # Final fallback: pick largest split even if one-class.
    candidate_groups: list[tuple[str, list[dict[str, Any]]]] = []
    split_names = sorted({str(r["split"]) for r in examples})
    for split_name in split_names:
        candidate_groups.append((split_name, [r for r in examples if r["split"] == split_name]))
    candidate_groups.append(("all", examples))
    candidate_groups.sort(key=lambda item: len(item[1]), reverse=True)

    if not candidate_groups or not candidate_groups[0][1]:
        return [], "none", "no rows available for calibration fit"

    split_name, rows = candidate_groups[0]
    note = (
        f"insufficient class diversity for robust temperature fit; falling back to split '{split_name}' with "
        f"{len(rows)} rows"
    )
    return rows, split_name, note


def extract_success_examples(prediction_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    examples: list[dict[str, Any]] = []
    for row in prediction_rows:
        success_true = row.get("success_true")
        success_pred = row.get("success_pred")
        margin = to_float(row.get("success_margin"))
        if not isinstance(success_true, bool):
            continue
        if not isinstance(success_pred, bool):
            continue
        if margin is None:
            continue

        score = margin if success_pred else -margin
        examples.append(
            {
                "run_id": row.get("run_id"),
                "split": str(row.get("split", "unknown")),
                "label": 1 if success_true else 0,
                "score": score,
                "uncalibrated_probability": sigmoid(score),
            }
        )
    return examples


def extract_regime_top1_examples(prediction_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    examples: list[dict[str, Any]] = []
    for row in prediction_rows:
        regime_true = row.get("regime_true")
        regime_pred = row.get("regime_pred")
        margin = to_float(row.get("regime_margin"))
        if not isinstance(regime_true, str) or not regime_true.strip():
            continue
        if not isinstance(regime_pred, str) or not regime_pred.strip():
            continue
        if margin is None:
            continue

        is_correct = regime_true == regime_pred
        examples.append(
            {
                "run_id": row.get("run_id"),
                "split": str(row.get("split", "unknown")),
                "label": 1 if is_correct else 0,
                "score": margin,
                "uncalibrated_probability": sigmoid(margin),
            }
        )
    return examples


def calibrate_probability_head(
    head_name: str,
    examples: list[dict[str, Any]],
    head_cfg: dict[str, Any],
) -> tuple[dict[str, Any], dict[tuple[str, str], dict[str, float]]]:
    if not examples:
        return (
            {
                "head_name": head_name,
                "status": "no_data",
                "message": "No usable rows found for this calibration head.",
            },
            {},
        )

    fit_split = str(head_cfg.get("fit_split", "val"))
    min_fit_rows = int(head_cfg.get("min_fit_rows", 20))
    num_bins = int(head_cfg.get("num_bins", 10))

    grid_cfg = head_cfg.get("temperature_grid", {})
    if not isinstance(grid_cfg, dict):
        grid_cfg = {}
    grid_min = float(grid_cfg.get("min", 0.05))
    grid_max = float(grid_cfg.get("max", 20.0))
    grid_steps = int(grid_cfg.get("steps", 200))

    fit_rows, fit_split_used, fit_note = choose_fit_rows(
        examples=examples,
        preferred_split=fit_split,
        min_fit_rows=min_fit_rows,
    )

    labels = [int(r["label"]) for r in fit_rows]
    if not fit_rows:
        for r in examples:
            r["temperature_scaled_probability"] = r["uncalibrated_probability"]
            r["calibrated_probability"] = r["uncalibrated_probability"]
        metrics_uncal = build_metric_block(examples, prob_key="uncalibrated_probability", num_bins=num_bins)
        return (
            {
                "head_name": head_name,
                "status": "no_data",
                "message": "No calibration rows were available.",
                "metrics": {
                    "uncalibrated": metrics_uncal,
                    "temperature_scaled": metrics_uncal,
                    "final": metrics_uncal,
                },
            },
            {},
        )

    # One-class fallback: keep T=1 to avoid unstable fitting.
    if not has_both_classes(labels):
        best_temperature = 1.0
        fit_baseline_loss = mean_log_loss(labels, [float(r["uncalibrated_probability"]) for r in fit_rows])
        fit_best_loss = fit_baseline_loss
        temperature_candidates = [1.0]
        if fit_note is None:
            fit_note = "fit labels contained a single class; kept temperature at 1.0"
    else:
        (
            best_temperature,
            fit_baseline_loss,
            fit_best_loss,
            temperature_candidates,
        ) = fit_temperature(
            fit_rows=fit_rows,
            grid_min=grid_min,
            grid_max=grid_max,
            grid_steps=grid_steps,
        )

    for r in examples:
        r["temperature_scaled_probability"] = sigmoid(float(r["score"]) / best_temperature)

    isotonic_cfg = head_cfg.get("isotonic", {})
    if not isinstance(isotonic_cfg, dict):
        isotonic_cfg = {}
    isotonic_enabled = bool(isotonic_cfg.get("enabled", True))
    isotonic_min_rows = int(isotonic_cfg.get("min_fit_rows", 40))

    isotonic_model = None
    isotonic_note = None
    if isotonic_enabled and len(fit_rows) >= isotonic_min_rows and has_both_classes(labels):
        fit_temp_probs = [float(r["temperature_scaled_probability"]) for r in fit_rows]
        fit_labels = [int(r["label"]) for r in fit_rows]
        isotonic_model = fit_isotonic(fit_temp_probs, fit_labels)
        if isotonic_model is None:
            isotonic_note = "isotonic fitting returned no model"
    elif isotonic_enabled:
        isotonic_note = (
            f"isotonic skipped (requires >= {isotonic_min_rows} rows and both classes in fit split)"
        )
    else:
        isotonic_note = "isotonic disabled by config"

    if isotonic_model is not None:
        for r in examples:
            r["calibrated_probability"] = apply_isotonic(float(r["temperature_scaled_probability"]), isotonic_model)
    else:
        for r in examples:
            r["calibrated_probability"] = float(r["temperature_scaled_probability"])

    metrics_uncal = build_metric_block(examples, prob_key="uncalibrated_probability", num_bins=num_bins)
    metrics_temp = build_metric_block(examples, prob_key="temperature_scaled_probability", num_bins=num_bins)
    metrics_final = build_metric_block(examples, prob_key="calibrated_probability", num_bins=num_bins)

    run_probabilities: dict[tuple[str, str], dict[str, float]] = {}
    for r in examples:
        key = (str(r.get("run_id")), str(r.get("split")))
        run_probabilities[key] = {
            "uncalibrated_probability": float(r["uncalibrated_probability"]),
            "temperature_scaled_probability": float(r["temperature_scaled_probability"]),
            "calibrated_probability": float(r["calibrated_probability"]),
        }

    report = {
        "head_name": head_name,
        "status": "ok",
        "fit": {
            "preferred_split": fit_split,
            "used_split": fit_split_used,
            "row_count": len(fit_rows),
            "positive_rate": (sum(labels) / len(labels)) if labels else None,
            "note": fit_note,
        },
        "temperature_scaling": {
            "temperature": best_temperature,
            "fit_log_loss_before": fit_baseline_loss,
            "fit_log_loss_after": fit_best_loss,
            "grid": {
                "min": grid_min,
                "max": grid_max,
                "steps": grid_steps,
                "candidate_count": len(temperature_candidates),
            },
        },
        "isotonic": {
            "applied": isotonic_model is not None,
            "note": isotonic_note,
            "model": isotonic_model,
        },
        "metrics": {
            "uncalibrated": metrics_uncal,
            "temperature_scaled": metrics_temp,
            "final": metrics_final,
        },
    }
    return report, run_probabilities


def infer_model_id(predictions_path: Path) -> str:
    name = predictions_path.name
    if name.endswith(".predictions.jsonl"):
        return name[: -len(".predictions.jsonl")]
    return predictions_path.stem


def main() -> int:
    args = parse_args()

    cfg = load_json_or_yaml(args.config)
    if not isinstance(cfg, dict):
        raise ValueError("Calibration config must be a JSON/YAML object")

    prediction_rows = read_jsonl(args.predictions)
    if not prediction_rows:
        print("Predictions file is empty.")
        return 1

    success_cfg = cfg.get("success_probability", {})
    regime_cfg = cfg.get("regime_top1_correctness_probability", {})
    if not isinstance(success_cfg, dict):
        success_cfg = {}
    if not isinstance(regime_cfg, dict):
        regime_cfg = {}

    success_examples = extract_success_examples(prediction_rows)
    regime_examples = extract_regime_top1_examples(prediction_rows)

    success_report, success_prob_map = calibrate_probability_head(
        head_name="encapsulation_success_probability",
        examples=success_examples,
        head_cfg=success_cfg,
    )
    regime_report, regime_prob_map = calibrate_probability_head(
        head_name="regime_top1_correctness_probability",
        examples=regime_examples,
        head_cfg=regime_cfg,
    )

    calibrated_predictions_path = args.calibrated_predictions_output
    if calibrated_predictions_path is None:
        calibrated_predictions_path = args.output.with_name(
            f"{args.output.stem}.calibrated_predictions.jsonl"
        )

    augmented_predictions: list[dict[str, Any]] = []
    for row in prediction_rows:
        split = str(row.get("split", "unknown"))
        run_id = str(row.get("run_id", ""))
        key = (run_id, split)
        output_row = dict(row)

        success_probs = success_prob_map.get(key)
        if success_probs is not None:
            output_row["success_probability_uncalibrated"] = success_probs["uncalibrated_probability"]
            output_row["success_probability_temperature_scaled"] = success_probs[
                "temperature_scaled_probability"
            ]
            output_row["success_probability_calibrated"] = success_probs["calibrated_probability"]

        regime_probs = regime_prob_map.get(key)
        if regime_probs is not None:
            output_row["regime_top1_correctness_uncalibrated"] = regime_probs[
                "uncalibrated_probability"
            ]
            output_row["regime_top1_correctness_temperature_scaled"] = regime_probs[
                "temperature_scaled_probability"
            ]
            output_row["regime_top1_correctness_calibrated"] = regime_probs["calibrated_probability"]

        augmented_predictions.append(output_row)

    write_jsonl(calibrated_predictions_path, augmented_predictions)

    created_at = datetime.now(timezone.utc).isoformat()
    report = {
        "name": str(cfg.get("name", "uncertainty_calibration")),
        "model_id": infer_model_id(args.predictions),
        "created_at_utc": created_at,
        "inputs": {
            "predictions_path": str(args.predictions),
            "config_path": str(args.config),
            "prediction_count": len(prediction_rows),
        },
        "outputs": {
            "calibration_report_path": str(args.output),
            "calibrated_predictions_path": str(calibrated_predictions_path),
        },
        "heads": {
            "success_probability": success_report,
            "regime_top1_correctness_probability": regime_report,
        },
    }
    dump_json(args.output, report)

    print(f"Wrote calibration report -> {args.output}")
    print(f"Wrote calibrated predictions -> {calibrated_predictions_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
