#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
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


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Train/validate a lightweight interface segmentation baseline from "
            "frame-level pixel samples (MVP-011)."
        )
    )
    parser.add_argument("--dataset-root", required=True, type=Path, help="Canonical or simulation dataset root")
    parser.add_argument("--annotations", required=True, type=Path, help="JSONL frame annotation/pixel-sample artifact")
    parser.add_argument("--config", required=True, type=Path, help="Segmentation config JSON/YAML")
    parser.add_argument("--split", default=None, type=Path, help="Optional split artifact from create_split.py")
    parser.add_argument(
        "--output-dir",
        default=Path("data/canonical/family_a/manifests/segmentation_models"),
        type=Path,
        help="Output directory for model and QC artifacts",
    )
    parser.add_argument(
        "--model-id",
        default=None,
        help="Optional model identifier; defaults to <config_name>_<UTC timestamp>",
    )
    return parser.parse_args()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as f:
        while True:
            chunk = f.read(1024 * 1024)
            if not chunk:
                break
            digest.update(chunk)
    return digest.hexdigest()


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


def to_bool(value: Any) -> bool | None:
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        return bool(value)
    if isinstance(value, str):
        lowered = value.strip().lower()
        if lowered in {"1", "true", "yes", "y"}:
            return True
        if lowered in {"0", "false", "no", "n"}:
            return False
    return None


def load_split_assignments(split_path: Path | None) -> tuple[dict[str, str], list[str]]:
    if split_path is None:
        return {}, []

    payload = load_json(split_path)
    runs = payload.get("runs", {})
    if not isinstance(runs, dict):
        return {}, ["split artifact missing runs object"]

    assignments: dict[str, str] = {}
    errors: list[str] = []
    for split_name in ("train", "val", "test"):
        split_runs = runs.get(split_name, [])
        if not isinstance(split_runs, list):
            errors.append(f"split '{split_name}' must be a list")
            continue
        for run_id in split_runs:
            if not isinstance(run_id, str) or not run_id.strip():
                errors.append(f"split '{split_name}' has invalid run_id={run_id!r}")
                continue
            if run_id in assignments:
                errors.append(
                    f"run_id={run_id} appears in multiple splits ({assignments[run_id]} and {split_name})"
                )
                continue
            assignments[run_id] = split_name
    return assignments, errors


def resolve_split(row: dict[str, Any], split_assignments: dict[str, str], run_id: str) -> str:
    explicit = row.get("split")
    if isinstance(explicit, str):
        split_name = explicit.strip().lower()
        if split_name in {"train", "val", "test"}:
            return split_name
    return split_assignments.get(run_id, "train")


def predict_label(intensity: float, threshold: float, direction: str) -> bool:
    if direction == "less_than_or_equal":
        return intensity <= threshold
    return intensity >= threshold


def compute_metrics(tp: int, fp: int, tn: int, fn: int) -> dict[str, Any]:
    total = tp + fp + tn + fn
    precision = tp / (tp + fp) if (tp + fp) else None
    recall = tp / (tp + fn) if (tp + fn) else None
    f1 = (2.0 * precision * recall / (precision + recall)) if (precision is not None and recall is not None and (precision + recall) > 0) else None
    iou = tp / (tp + fp + fn) if (tp + fp + fn) else None
    accuracy = (tp + tn) / total if total else None
    true_positive_rate = (tp + fn) / total if total else None
    predicted_positive_rate = (tp + fp) / total if total else None
    return {
        "n_pixels": total,
        "tp": tp,
        "fp": fp,
        "tn": tn,
        "fn": fn,
        "precision": precision,
        "recall": recall,
        "f1": f1,
        "iou": iou,
        "accuracy": accuracy,
        "true_positive_rate": true_positive_rate,
        "predicted_positive_rate": predicted_positive_rate,
    }


def add_confusion(acc: dict[str, int], truth: bool, pred: bool) -> None:
    if truth and pred:
        acc["tp"] += 1
    elif not truth and pred:
        acc["fp"] += 1
    elif truth and not pred:
        acc["fn"] += 1
    else:
        acc["tn"] += 1


def main() -> int:
    args = parse_args()

    config = load_json_or_yaml(args.config)
    if not isinstance(config, dict):
        print(f"Config must be an object: {args.config}")
        return 1

    data_cfg = config.get("data", {})
    if not isinstance(data_cfg, dict):
        data_cfg = {}
    intensity_key = str(data_cfg.get("intensity_key", "intensity"))
    label_key = str(data_cfg.get("label_key", "is_interface"))
    sample_key = str(data_cfg.get("sample_key", "pixel_samples"))

    quality_cfg = config.get("quality_report", {})
    if not isinstance(quality_cfg, dict):
        quality_cfg = {}
    min_iou_warn = to_float(quality_cfg.get("min_iou_warn"))
    min_f1_warn = to_float(quality_cfg.get("min_f1_warn"))
    if min_iou_warn is None:
        min_iou_warn = 0.65
    if min_f1_warn is None:
        min_f1_warn = 0.75

    split_assignments, split_errors = load_split_assignments(args.split)

    rows = load_jsonl(args.annotations)
    if not rows:
        print(f"No annotation rows found in {args.annotations}")
        return 1

    frame_records: list[dict[str, Any]] = []
    parse_errors: list[str] = []
    train_pos_values: list[float] = []
    train_neg_values: list[float] = []

    for row_idx, row in enumerate(rows, start=1):
        run_id = row.get("run_id")
        if not isinstance(run_id, str) or not run_id.strip():
            parse_errors.append(f"row {row_idx}: missing valid run_id")
            continue
        run_id = run_id.strip()

        frame_index = row.get("frame_index")
        frame_index_value = int(frame_index) if isinstance(frame_index, int) else None

        split_name = resolve_split(row, split_assignments, run_id)
        pixel_rows = row.get(sample_key, [])
        if not isinstance(pixel_rows, list) or not pixel_rows:
            parse_errors.append(f"row {row_idx}: missing non-empty {sample_key}")
            continue

        pixels: list[tuple[float, bool]] = []
        for sample in pixel_rows:
            if not isinstance(sample, dict):
                parse_errors.append(f"row {row_idx}: sample must be object")
                continue
            intensity = to_float(sample.get(intensity_key))
            label = to_bool(sample.get(label_key))
            if intensity is None or label is None:
                parse_errors.append(
                    f"row {row_idx}: invalid sample fields intensity={sample.get(intensity_key)!r} label={sample.get(label_key)!r}"
                )
                continue
            pixels.append((intensity, label))
            if split_name == "train":
                if label:
                    train_pos_values.append(intensity)
                else:
                    train_neg_values.append(intensity)

        if not pixels:
            parse_errors.append(f"row {row_idx}: no valid pixel samples after parsing")
            continue

        frame_records.append(
            {
                "run_id": run_id,
                "frame_index": frame_index_value,
                "split": split_name,
                "pixels": pixels,
            }
        )

    if split_errors:
        parse_errors.extend([f"split: {err}" for err in split_errors])

    if parse_errors:
        for err in parse_errors[:30]:
            print(f"- {err}")
        if len(parse_errors) > 30:
            print(f"... {len(parse_errors) - 30} additional parsing issue(s)")

    if not train_pos_values or not train_neg_values:
        print("Training requires both positive and negative pixel samples in train split.")
        return 1

    pos_mean = sum(train_pos_values) / len(train_pos_values)
    neg_mean = sum(train_neg_values) / len(train_neg_values)
    threshold = (pos_mean + neg_mean) / 2.0
    direction = "less_than_or_equal" if pos_mean <= neg_mean else "greater_than_or_equal"

    split_conf: dict[str, dict[str, int]] = {
        "train": {"tp": 0, "fp": 0, "tn": 0, "fn": 0},
        "val": {"tp": 0, "fp": 0, "tn": 0, "fn": 0},
        "test": {"tp": 0, "fp": 0, "tn": 0, "fn": 0},
    }
    run_conf: dict[str, dict[str, int]] = defaultdict(lambda: {"tp": 0, "fp": 0, "tn": 0, "fn": 0})
    frame_metrics: list[dict[str, Any]] = []

    for frame in frame_records:
        run_id = str(frame["run_id"])
        split_name = str(frame["split"])
        conf = {"tp": 0, "fp": 0, "tn": 0, "fn": 0}

        for intensity, truth in frame["pixels"]:
            pred = predict_label(intensity, threshold, direction)
            add_confusion(split_conf[split_name], truth, pred)
            add_confusion(run_conf[run_id], truth, pred)
            add_confusion(conf, truth, pred)

        metric = compute_metrics(conf["tp"], conf["fp"], conf["tn"], conf["fn"])
        frame_metrics.append(
            {
                "run_id": run_id,
                "frame_index": frame["frame_index"],
                "split": split_name,
                **metric,
            }
        )

    by_split = {
        split_name: compute_metrics(conf["tp"], conf["fp"], conf["tn"], conf["fn"])
        for split_name, conf in split_conf.items()
    }

    run_metrics: list[dict[str, Any]] = []
    for run_id, conf in run_conf.items():
        metric = compute_metrics(conf["tp"], conf["fp"], conf["tn"], conf["fn"])
        run_metrics.append({"run_id": run_id, **metric})
    run_metrics.sort(key=lambda row: (1.0 if row.get("iou") is None else float(row["iou"]), row["run_id"]))

    flagged_runs: list[dict[str, Any]] = []
    for row in run_metrics:
        iou = row.get("iou")
        f1 = row.get("f1")
        if (iou is not None and float(iou) < min_iou_warn) or (f1 is not None and float(f1) < min_f1_warn):
            flagged_runs.append(row)

    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    model_id = args.model_id or f"{args.config.stem}_{timestamp}"

    model_artifact = {
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "task_id": "MVP-011",
        "model_id": model_id,
        "model_type": "global_intensity_threshold",
        "dataset_root": str(args.dataset_root),
        "annotations": str(args.annotations),
        "split": str(args.split) if args.split is not None else None,
        "config": str(args.config),
        "config_sha256": sha256_file(args.config),
        "annotations_sha256": sha256_file(args.annotations),
        "threshold": threshold,
        "decision_rule": direction,
        "class_statistics": {
            "positive_mean_intensity": pos_mean,
            "negative_mean_intensity": neg_mean,
            "n_positive_pixels_train": len(train_pos_values),
            "n_negative_pixels_train": len(train_neg_values),
        },
        "evaluation": {
            "by_split": by_split,
            "n_frames": len(frame_records),
            "n_runs": len(run_conf),
        },
    }

    qc_report = {
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "task_id": "MVP-011",
        "model_id": model_id,
        "quality_thresholds": {
            "min_iou_warn": min_iou_warn,
            "min_f1_warn": min_f1_warn,
        },
        "metrics_by_split": by_split,
        "flagged_runs": flagged_runs,
        "worst_runs_by_iou": run_metrics[: min(20, len(run_metrics))],
        "parsing_warnings_count": len(parse_errors),
    }

    model_path = args.output_dir / f"{model_id}.model.json"
    qc_path = args.output_dir / f"{model_id}.qc.json"
    frame_metrics_path = args.output_dir / f"{model_id}.frame_metrics.jsonl"

    dump_json(model_path, model_artifact)
    dump_json(qc_path, qc_report)
    dump_jsonl(frame_metrics_path, frame_metrics)

    print(f"Wrote segmentation model artifact -> {model_path}")
    print(f"Wrote segmentation QC report -> {qc_path}")
    print(f"Wrote frame-level metrics -> {frame_metrics_path}")
    print(
        "Train metrics: "
        + f"IoU={by_split['train'].get('iou')} "
        + f"F1={by_split['train'].get('f1')} "
        + f"n_pixels={by_split['train'].get('n_pixels')}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
