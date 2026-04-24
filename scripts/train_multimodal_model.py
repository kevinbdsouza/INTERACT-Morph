#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
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

G = 9.80665


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Train/evaluate a config-driven multimodal baseline model (MVP-020)."
    )
    parser.add_argument("--dataset-root", required=True, type=Path, help="Canonical dataset root")
    parser.add_argument("--split", required=True, type=Path, help="Split artifact from create_split.py")
    parser.add_argument("--config", required=True, type=Path, help="Model/training config JSON or YAML")
    parser.add_argument(
        "--output-dir",
        default=Path("data/canonical/family_a/manifests/models"),
        type=Path,
        help="Output directory for model/evaluation artifacts",
    )
    parser.add_argument(
        "--model-id",
        default=None,
        help="Optional model identifier override; defaults to <config_name>_<UTC timestamp>",
    )
    parser.add_argument(
        "--init-model",
        default=None,
        type=Path,
        help="Optional pretrained model artifact to warm-start/fine-tune from (MVP-022)",
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


def safe_get(payload: dict[str, Any], path: str) -> Any:
    current: Any = payload
    for token in path.split("."):
        if not isinstance(current, dict) or token not in current:
            return None
        current = current[token]
    return current


def to_float(value: Any) -> float | None:
    if isinstance(value, bool):
        return 1.0 if value else 0.0
    if isinstance(value, (int, float)):
        f = float(value)
        return f if math.isfinite(f) else None
    if isinstance(value, str):
        text = value.strip()
        if not text:
            return None
        try:
            f = float(text)
        except ValueError:
            return None
        return f if math.isfinite(f) else None
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


def resolve_spec_value(
    sources: dict[str, dict[str, Any]],
    spec: dict[str, Any],
) -> Any:
    candidates: list[dict[str, Any]] = [
        {"source": spec.get("source"), "path": spec.get("path")},
    ]
    fallback = spec.get("fallback", [])
    if isinstance(fallback, list):
        for item in fallback:
            if isinstance(item, dict):
                candidates.append(item)

    for candidate in candidates:
        source_name = candidate.get("source")
        path = candidate.get("path")
        if not isinstance(source_name, str) or not isinstance(path, str):
            continue
        source_payload = sources.get(source_name)
        if source_payload is None:
            continue
        value = safe_get(source_payload, path)
        if value is None:
            continue
        transform = candidate.get("transform", spec.get("transform"))
        value = apply_transform(value, transform)
        if value is not None:
            return value
    return None


def apply_transform(value: Any, transform: Any) -> Any:
    if transform is None:
        return value
    if not isinstance(transform, str):
        return None
    if transform == "height_mm_to_velocity_m_s":
        height_mm = to_float(value)
        if height_mm is None or height_mm < 0:
            return None
        return math.sqrt(2.0 * G * (height_mm / 1000.0))
    return None


def load_split_assignments(split_path: Path) -> tuple[dict[str, str], list[str]]:
    payload = load_json(split_path)
    runs = payload.get("runs", {})
    if not isinstance(runs, dict):
        raise ValueError("split payload missing runs object")

    assignments: dict[str, str] = {}
    errors: list[str] = []
    for split_name in ("train", "val", "test"):
        split_runs = runs.get(split_name, [])
        if not isinstance(split_runs, list):
            errors.append(f"split '{split_name}' must be a list")
            continue
        for run_id in split_runs:
            if not isinstance(run_id, str) or not run_id.strip():
                errors.append(f"split '{split_name}' contains invalid run_id={run_id!r}")
                continue
            if run_id in assignments:
                errors.append(
                    f"run_id={run_id} appears in multiple splits ({assignments[run_id]} and {split_name})"
                )
                continue
            assignments[run_id] = split_name
    return assignments, errors


def load_optional_derived_features(metadata: dict[str, Any], run_dir: Path) -> dict[str, Any] | None:
    relpath = metadata.get("asset_paths", {}).get("derived_features_relpath")
    candidate_paths: list[Path] = []
    if isinstance(relpath, str) and relpath.strip():
        candidate_paths.append(run_dir / relpath)
    candidate_paths.append(run_dir / "derived_features.json")

    for path in candidate_paths:
        if path.exists():
            return load_json(path)
    return None


def extract_feature_vector(
    sources: dict[str, dict[str, Any]],
    feature_specs: list[dict[str, Any]],
) -> tuple[list[float | None] | None, list[str]]:
    values: list[float | None] = []
    errors: list[str] = []

    for spec in feature_specs:
        name = str(spec.get("name", "<unnamed_feature>"))
        required = bool(spec.get("required", False))
        default = spec.get("default")

        raw = resolve_spec_value(sources, spec)
        if raw is None and default is not None:
            raw = default

        numeric = to_float(raw) if raw is not None else None
        if raw is not None and numeric is None:
            if required:
                errors.append(f"feature {name}: non-numeric value={raw!r}")
            values.append(None)
            continue
        if raw is None and required:
            errors.append(f"feature {name}: missing required value")
        values.append(numeric)

    return (None, errors) if errors else (values, [])


def extract_targets(
    sources: dict[str, dict[str, Any]],
    heads_cfg: dict[str, Any],
) -> dict[str, Any]:
    result: dict[str, Any] = {
        "success": None,
        "regime": None,
        "regression": {},
    }

    success_spec = heads_cfg.get("success_classification", {})
    if isinstance(success_spec, dict):
        success_raw = resolve_spec_value(sources, success_spec)
        result["success"] = to_bool(success_raw)

    regime_spec = heads_cfg.get("regime_classification", {})
    if isinstance(regime_spec, dict):
        regime_raw = resolve_spec_value(sources, regime_spec)
        if isinstance(regime_raw, str) and regime_raw.strip():
            result["regime"] = regime_raw.strip()

    regression_specs = heads_cfg.get("regression", [])
    if isinstance(regression_specs, list):
        for spec in regression_specs:
            if not isinstance(spec, dict):
                continue
            target_name = str(spec.get("name", "")).strip()
            if not target_name:
                continue
            raw = resolve_spec_value(sources, spec)
            result["regression"][target_name] = to_float(raw)

    return result


def fit_preprocessing(rows: list[dict[str, Any]], feature_names: list[str]) -> dict[str, Any]:
    n_features = len(feature_names)
    means: list[float] = []
    stds: list[float] = []
    for i in range(n_features):
        values = [float(r["x_raw"][i]) for r in rows if r["x_raw"][i] is not None]
        if not values:
            raise ValueError(f"feature '{feature_names[i]}' has no finite values in training split")
        mean = sum(values) / len(values)
        variance = sum((v - mean) ** 2 for v in values) / len(values)
        std = math.sqrt(variance)
        means.append(mean)
        stds.append(std if std > 0 else 1.0)
    return {"mean": means, "std": stds}


def transform_features(row: dict[str, Any], preprocess: dict[str, Any]) -> list[float]:
    values: list[float] = []
    means = preprocess["mean"]
    stds = preprocess["std"]
    for i, raw in enumerate(row["x_raw"]):
        value = float(raw) if raw is not None else float(means[i])
        values.append((value - float(means[i])) / float(stds[i]))
    return values


def squared_distance(a: list[float], b: list[float]) -> float:
    return sum((x - y) ** 2 for x, y in zip(a, b))


def fit_centroid_classifier(
    train_rows: list[dict[str, Any]],
    label_key: str,
) -> dict[str, Any] | None:
    grouped: dict[str, list[list[float]]] = {}
    for row in train_rows:
        label = row.get(label_key)
        if label is None:
            continue
        grouped.setdefault(str(label), []).append(row["x"])

    if not grouped:
        return None

    centroids: dict[str, list[float]] = {}
    priors: dict[str, float] = {}
    total = sum(len(vectors) for vectors in grouped.values())
    for label, vectors in grouped.items():
        dim = len(vectors[0])
        centroid = [sum(v[i] for v in vectors) / len(vectors) for i in range(dim)]
        centroids[label] = centroid
        priors[label] = len(vectors) / total

    return {"centroids": centroids, "priors": priors}


def label_counts_from_rows(
    rows: list[dict[str, Any]],
    label_key: str,
) -> dict[str, int]:
    counts: Counter[str] = Counter()
    for row in rows:
        label = row.get(label_key)
        if label is None:
            continue
        counts[str(label)] += 1
    return dict(counts)


def _validated_centroid_map(model: dict[str, Any] | None) -> dict[str, list[float]]:
    if not isinstance(model, dict):
        return {}
    centroids_raw = model.get("centroids")
    if not isinstance(centroids_raw, dict):
        return {}

    parsed: dict[str, list[float]] = {}
    for key, vector in centroids_raw.items():
        if not isinstance(key, str) or not isinstance(vector, list) or not vector:
            continue
        parsed_vector: list[float] = []
        valid = True
        for value in vector:
            numeric = to_float(value)
            if numeric is None:
                valid = False
                break
            parsed_vector.append(float(numeric))
        if valid:
            parsed[key] = parsed_vector
    return parsed


def blend_centroid_models(
    current_model: dict[str, Any] | None,
    prior_model: dict[str, Any] | None,
    current_label_counts: dict[str, int],
    prior_class_weight: float,
) -> dict[str, Any] | None:
    current_centroids = _validated_centroid_map(current_model)
    prior_centroids = _validated_centroid_map(prior_model)
    if not current_centroids and not prior_centroids:
        return None

    labels = sorted(set(current_centroids.keys()) | set(prior_centroids.keys()))
    blended_centroids: dict[str, list[float]] = {}
    blended_counts: dict[str, float] = {}

    for label in labels:
        current_vector = current_centroids.get(label)
        prior_vector = prior_centroids.get(label)
        current_count = float(current_label_counts.get(label, 0))
        prior_count = float(prior_class_weight) if prior_vector is not None else 0.0

        if current_vector is not None and prior_vector is not None:
            if len(current_vector) != len(prior_vector):
                # Feature mismatch in prior model for this head; prefer current fit.
                blended_centroids[label] = list(current_vector)
                blended_counts[label] = max(1.0, current_count)
                continue
            if current_count <= 0:
                current_count = 1.0
            total = current_count + prior_count
            blended_centroids[label] = [
                ((current_count * cur) + (prior_count * prior)) / total
                for cur, prior in zip(current_vector, prior_vector)
            ]
            blended_counts[label] = total
        elif current_vector is not None:
            blended_centroids[label] = list(current_vector)
            blended_counts[label] = max(1.0, current_count)
        elif prior_vector is not None:
            blended_centroids[label] = list(prior_vector)
            blended_counts[label] = max(1.0, prior_count)

    if not blended_centroids:
        return None

    total_count = sum(blended_counts.values())
    priors = {
        label: (blended_counts.get(label, 0.0) / total_count if total_count > 0 else 1.0 / len(blended_centroids))
        for label in blended_centroids.keys()
    }
    return {"centroids": blended_centroids, "priors": priors}


def predict_centroid(
    x: list[float],
    model: dict[str, Any] | None,
) -> tuple[str | None, float | None, float | None]:
    if not model:
        return None, None, None

    centroids: dict[str, list[float]] = model["centroids"]
    priors: dict[str, float] = model["priors"]
    scores: list[tuple[str, float, float]] = []
    for label, centroid in centroids.items():
        distance = squared_distance(x, centroid)
        prior = float(priors.get(label, 0.0))
        scores.append((label, distance, prior))

    scores.sort(key=lambda item: (item[1], -item[2], item[0]))
    best_label, best_distance, _ = scores[0]
    if len(scores) > 1:
        margin = scores[1][1] - best_distance
    else:
        margin = None
    return best_label, best_distance, margin


def fit_knn_regressors(
    train_rows: list[dict[str, Any]],
    target_names: list[str],
    k_neighbors: int,
) -> dict[str, Any]:
    models: dict[str, Any] = {}
    for target in target_names:
        vectors: list[list[float]] = []
        values: list[float] = []
        run_ids: list[str] = []
        for row in train_rows:
            value = row["regression_targets"].get(target)
            if value is None:
                continue
            vectors.append(row["x"])
            values.append(float(value))
            run_ids.append(row["run_id"])
        if vectors:
            models[target] = {
                "k_neighbors": k_neighbors,
                "train_vectors": vectors,
                "train_values": values,
                "train_run_ids": run_ids,
            }
    return models


def _parse_regressor_samples(model: dict[str, Any]) -> list[tuple[list[float], float, str]]:
    vectors_raw = model.get("train_vectors", [])
    values_raw = model.get("train_values", [])
    run_ids_raw = model.get("train_run_ids", [])
    if not isinstance(vectors_raw, list) or not isinstance(values_raw, list):
        return []
    if len(vectors_raw) != len(values_raw):
        return []

    samples: list[tuple[list[float], float, str]] = []
    for idx, (vector, value) in enumerate(zip(vectors_raw, values_raw)):
        if not isinstance(vector, list) or not vector:
            continue
        parsed_vector: list[float] = []
        valid = True
        for v in vector:
            fv = to_float(v)
            if fv is None:
                valid = False
                break
            parsed_vector.append(float(fv))
        if not valid:
            continue
        parsed_value = to_float(value)
        if parsed_value is None:
            continue
        if isinstance(run_ids_raw, list) and idx < len(run_ids_raw) and isinstance(run_ids_raw[idx], str):
            run_id = run_ids_raw[idx]
        else:
            run_id = f"sample_{idx:06d}"
        samples.append((parsed_vector, float(parsed_value), run_id))
    return samples


def merge_regression_memory(
    current_regressors: dict[str, Any],
    prior_regressors: dict[str, Any] | None,
    k_neighbors: int,
    max_prior_samples: int,
) -> dict[str, Any]:
    if not isinstance(prior_regressors, dict):
        return current_regressors

    merged: dict[str, Any] = {}
    all_targets = sorted(set(current_regressors.keys()) | set(prior_regressors.keys()))
    for target in all_targets:
        current_model = current_regressors.get(target)
        prior_model = prior_regressors.get(target)
        if not isinstance(current_model, dict) and not isinstance(prior_model, dict):
            continue

        current_samples = _parse_regressor_samples(current_model) if isinstance(current_model, dict) else []
        prior_samples = _parse_regressor_samples(prior_model) if isinstance(prior_model, dict) else []

        if max_prior_samples >= 0:
            prior_samples = prior_samples[:max_prior_samples]

        samples = list(current_samples)
        if current_samples and prior_samples:
            current_dim = len(current_samples[0][0])
            prior_samples = [sample for sample in prior_samples if len(sample[0]) == current_dim]
        samples.extend(prior_samples)

        if not samples:
            continue

        merged[target] = {
            "k_neighbors": int(k_neighbors),
            "train_vectors": [vector for vector, _, _ in samples],
            "train_values": [value for _, value, _ in samples],
            "train_run_ids": [run_id for _, _, run_id in samples],
        }
    return merged


def resolve_preprocessing(
    train_rows: list[dict[str, Any]],
    feature_names: list[str],
    pretrained_model: dict[str, Any] | None,
    reuse_pretrained_preprocessing: bool,
) -> tuple[dict[str, Any], str]:
    if reuse_pretrained_preprocessing and isinstance(pretrained_model, dict):
        preproc = pretrained_model.get("preprocessing")
        if isinstance(preproc, dict):
            means_raw = preproc.get("mean")
            stds_raw = preproc.get("std")
            if (
                isinstance(means_raw, list)
                and isinstance(stds_raw, list)
                and len(means_raw) == len(feature_names)
                and len(stds_raw) == len(feature_names)
            ):
                means: list[float] = []
                stds: list[float] = []
                valid = True
                for mean_raw, std_raw in zip(means_raw, stds_raw):
                    mean_value = to_float(mean_raw)
                    std_value = to_float(std_raw)
                    if mean_value is None or std_value is None or std_value <= 0:
                        valid = False
                        break
                    means.append(float(mean_value))
                    stds.append(float(std_value))
                if valid:
                    return {"mean": means, "std": stds}, "pretrained"

    return fit_preprocessing(train_rows, feature_names), "train_split"


def predict_knn_regression(
    x: list[float],
    model: dict[str, Any] | None,
    distance_epsilon: float,
) -> float | None:
    if not model:
        return None

    vectors = model["train_vectors"]
    values = model["train_values"]
    if not vectors:
        return None

    pairs: list[tuple[float, float]] = []
    for train_x, target in zip(vectors, values):
        pairs.append((squared_distance(x, train_x), float(target)))
    pairs.sort(key=lambda item: item[0])

    k = max(1, int(model["k_neighbors"]))
    neighbors = pairs[: min(k, len(pairs))]
    exact = [target for dist, target in neighbors if dist <= distance_epsilon]
    if exact:
        return sum(exact) / len(exact)

    weighted_sum = 0.0
    weight_total = 0.0
    for dist, target in neighbors:
        weight = 1.0 / (dist + distance_epsilon)
        weighted_sum += weight * target
        weight_total += weight
    return (weighted_sum / weight_total) if weight_total > 0 else None


def macro_f1(y_true: list[str], y_pred: list[str]) -> float | None:
    if not y_true:
        return None
    labels = sorted(set(y_true) | set(y_pred))
    f1_values: list[float] = []
    for label in labels:
        tp = sum(1 for truth, pred in zip(y_true, y_pred) if truth == label and pred == label)
        fp = sum(1 for truth, pred in zip(y_true, y_pred) if truth != label and pred == label)
        fn = sum(1 for truth, pred in zip(y_true, y_pred) if truth == label and pred != label)
        precision = tp / (tp + fp) if (tp + fp) else 0.0
        recall = tp / (tp + fn) if (tp + fn) else 0.0
        f1 = (2.0 * precision * recall / (precision + recall)) if (precision + recall) else 0.0
        f1_values.append(f1)
    return sum(f1_values) / len(f1_values)


def binary_metrics(y_true: list[bool], y_pred: list[bool]) -> dict[str, float | None]:
    if not y_true:
        return {"count": 0, "accuracy": None, "precision": None, "recall": None, "f1": None}
    tp = sum(1 for truth, pred in zip(y_true, y_pred) if truth and pred)
    tn = sum(1 for truth, pred in zip(y_true, y_pred) if (not truth) and (not pred))
    fp = sum(1 for truth, pred in zip(y_true, y_pred) if (not truth) and pred)
    fn = sum(1 for truth, pred in zip(y_true, y_pred) if truth and (not pred))
    precision = tp / (tp + fp) if (tp + fp) else 0.0
    recall = tp / (tp + fn) if (tp + fn) else 0.0
    f1 = (2.0 * precision * recall / (precision + recall)) if (precision + recall) else 0.0
    accuracy = (tp + tn) / len(y_true)
    return {
        "count": len(y_true),
        "accuracy": accuracy,
        "precision": precision,
        "recall": recall,
        "f1": f1,
    }


def regression_metrics(y_true: list[float], y_pred: list[float]) -> dict[str, float | None]:
    if not y_true:
        return {"count": 0, "mae": None, "rmse": None}
    abs_errors = [abs(a - b) for a, b in zip(y_true, y_pred)]
    sq_errors = [(a - b) ** 2 for a, b in zip(y_true, y_pred)]
    return {
        "count": len(y_true),
        "mae": sum(abs_errors) / len(abs_errors),
        "rmse": math.sqrt(sum(sq_errors) / len(sq_errors)),
    }


def evaluate_by_split(
    rows: list[dict[str, Any]],
    success_model: dict[str, Any] | None,
    regime_model: dict[str, Any] | None,
    regressors: dict[str, Any],
    distance_epsilon: float,
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    per_split_rows: dict[str, list[dict[str, Any]]] = {"train": [], "val": [], "test": []}
    for row in rows:
        per_split_rows[row["split"]].append(row)

    all_predictions: list[dict[str, Any]] = []
    evaluation: dict[str, Any] = {}
    for split_name in ("train", "val", "test"):
        split_rows = per_split_rows[split_name]
        success_true: list[bool] = []
        success_pred: list[bool] = []
        regime_true: list[str] = []
        regime_pred: list[str] = []
        regression_true: dict[str, list[float]] = {name: [] for name in regressors.keys()}
        regression_pred: dict[str, list[float]] = {name: [] for name in regressors.keys()}

        for row in split_rows:
            pred_success_label, success_dist, success_margin = predict_centroid(row["x"], success_model)
            pred_regime_label, regime_dist, regime_margin = predict_centroid(row["x"], regime_model)

            pred_success_bool = None
            if pred_success_label is not None:
                pred_success_bool = pred_success_label == "true"
            if row["success_target"] is not None and pred_success_bool is not None:
                success_true.append(bool(row["success_target"]))
                success_pred.append(pred_success_bool)

            if row["regime_target"] is not None and pred_regime_label is not None:
                regime_true.append(str(row["regime_target"]))
                regime_pred.append(str(pred_regime_label))

            regression_predictions: dict[str, float | None] = {}
            for target_name, model in regressors.items():
                y_hat = predict_knn_regression(row["x"], model, distance_epsilon=distance_epsilon)
                regression_predictions[target_name] = y_hat
                y_true = row["regression_targets"].get(target_name)
                if y_true is not None and y_hat is not None:
                    regression_true[target_name].append(float(y_true))
                    regression_pred[target_name].append(float(y_hat))

            all_predictions.append(
                {
                    "run_id": row["run_id"],
                    "split": row["split"],
                    "success_true": row["success_target"],
                    "success_pred": pred_success_bool,
                    "success_distance": success_dist,
                    "success_margin": success_margin,
                    "regime_true": row["regime_target"],
                    "regime_pred": pred_regime_label,
                    "regime_distance": regime_dist,
                    "regime_margin": regime_margin,
                    "regression_true": row["regression_targets"],
                    "regression_pred": regression_predictions,
                }
            )

        split_result = {
            "run_count": len(split_rows),
            "success_metrics": binary_metrics(success_true, success_pred),
            "regime_metrics": {
                "count": len(regime_true),
                "accuracy": (sum(1 for a, b in zip(regime_true, regime_pred) if a == b) / len(regime_true))
                if regime_true
                else None,
                "macro_f1": macro_f1(regime_true, regime_pred),
                "true_distribution": dict(Counter(regime_true)),
                "pred_distribution": dict(Counter(regime_pred)),
            },
            "regression_metrics": {},
        }
        for target_name in regressors.keys():
            split_result["regression_metrics"][target_name] = regression_metrics(
                regression_true[target_name],
                regression_pred[target_name],
            )
        evaluation[split_name] = split_result

    return evaluation, all_predictions


def write_predictions_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        for row in rows:
            f.write(json.dumps(row, sort_keys=False) + "\n")


def main() -> int:
    args = parse_args()

    cfg = load_json_or_yaml(args.config)
    config_name = str(cfg.get("name", "multimodal_model"))
    feature_specs = cfg.get("features", [])
    heads_cfg = cfg.get("heads", {})
    training_cfg = cfg.get("training", {})
    fine_tuning_cfg = cfg.get("fine_tuning", {})
    if not isinstance(fine_tuning_cfg, dict):
        fine_tuning_cfg = {}

    if not isinstance(feature_specs, list) or not feature_specs:
        raise ValueError("config.features must be a non-empty list")
    if not isinstance(heads_cfg, dict):
        raise ValueError("config.heads must be an object")

    pretrained_model: dict[str, Any] | None = None
    if args.init_model is not None:
        if not args.init_model.exists():
            print(f"Pretrained model artifact not found: {args.init_model}")
            return 1
        payload = load_json(args.init_model)
        if not isinstance(payload, dict):
            print(f"Pretrained model artifact must be a JSON object: {args.init_model}")
            return 1
        pretrained_model = payload

    assignments, split_errors = load_split_assignments(args.split)
    if split_errors:
        print("Split artifact errors:")
        for err in split_errors:
            print(f"- {err}")
        return 1
    if not assignments:
        print("Split artifact contains zero assigned runs.")
        return 1

    rows: list[dict[str, Any]] = []
    load_errors: list[str] = []
    for run_id, split_name in assignments.items():
        run_dir = args.dataset_root / "runs" / run_id
        metadata_path = run_dir / "metadata.json"
        if not metadata_path.exists():
            load_errors.append(f"{run_id}: missing metadata file")
            continue
        metadata = load_json(metadata_path)
        derived = load_optional_derived_features(metadata, run_dir)

        sources: dict[str, dict[str, Any]] = {"metadata": metadata}
        if derived is not None:
            sources["derived"] = derived

        x_raw, feature_errors = extract_feature_vector(sources, feature_specs)
        if feature_errors:
            load_errors.extend([f"{run_id}: {msg}" for msg in feature_errors])
            continue
        assert x_raw is not None

        targets = extract_targets(sources, heads_cfg)
        rows.append(
            {
                "run_id": run_id,
                "split": split_name,
                "x_raw": x_raw,
                "success_target": targets["success"],
                "regime_target": targets["regime"],
                "regression_targets": targets["regression"],
            }
        )

    if load_errors:
        print("Data loading warnings/errors:")
        for err in load_errors:
            print(f"- {err}")

    if not rows:
        print("No rows available for training/evaluation after parsing features.")
        return 1

    train_rows = [row for row in rows if row["split"] == "train"]
    if not train_rows:
        print("Training split has zero runs.")
        return 1

    feature_names = [str(spec.get("name", f"f_{idx}")) for idx, spec in enumerate(feature_specs)]
    if pretrained_model is not None:
        pretrained_feature_names = pretrained_model.get("feature_names")
        if not isinstance(pretrained_feature_names, list):
            print("Pretrained model artifact missing feature_names.")
            return 1
        pretrained_feature_name_values = [str(name) for name in pretrained_feature_names]
        if pretrained_feature_name_values != feature_names:
            print("Pretrained model feature_names mismatch with current config.")
            return 1

    reuse_pretrained_preprocessing = bool(
        fine_tuning_cfg.get("reuse_pretrained_preprocessing", pretrained_model is not None)
    )
    preprocess, preprocessing_source = resolve_preprocessing(
        train_rows=train_rows,
        feature_names=feature_names,
        pretrained_model=pretrained_model,
        reuse_pretrained_preprocessing=reuse_pretrained_preprocessing,
    )
    missing_count_by_feature = {
        feature_names[i]: sum(1 for row in rows if row["x_raw"][i] is None)
        for i in range(len(feature_names))
    }

    for row in rows:
        row["x"] = transform_features(row, preprocess)

    success_train_rows = [r for r in train_rows if r["success_target"] is not None]
    for r in success_train_rows:
        r["success_label"] = "true" if bool(r["success_target"]) else "false"
    success_model = fit_centroid_classifier(success_train_rows, "success_label")
    prior_class_weight = float(fine_tuning_cfg.get("prior_class_weight", 2.0))
    if prior_class_weight < 0:
        prior_class_weight = 0.0
    if pretrained_model is not None and prior_class_weight > 0:
        prior_success_model = None
        prior_heads = pretrained_model.get("heads")
        if isinstance(prior_heads, dict):
            prior_success_model = prior_heads.get("success_classification")
        success_counts = label_counts_from_rows(success_train_rows, "success_label")
        success_model = blend_centroid_models(
            current_model=success_model,
            prior_model=prior_success_model if isinstance(prior_success_model, dict) else None,
            current_label_counts=success_counts,
            prior_class_weight=prior_class_weight,
        )

    regime_model = fit_centroid_classifier(train_rows, "regime_target")
    if pretrained_model is not None and prior_class_weight > 0:
        prior_regime_model = None
        prior_heads = pretrained_model.get("heads")
        if isinstance(prior_heads, dict):
            prior_regime_model = prior_heads.get("regime_classification")
        regime_counts = label_counts_from_rows(train_rows, "regime_target")
        regime_model = blend_centroid_models(
            current_model=regime_model,
            prior_model=prior_regime_model if isinstance(prior_regime_model, dict) else None,
            current_label_counts=regime_counts,
            prior_class_weight=prior_class_weight,
        )

    regression_specs = heads_cfg.get("regression", [])
    regression_target_names = [
        str(spec.get("name", "")).strip()
        for spec in regression_specs
        if isinstance(spec, dict) and isinstance(spec.get("name"), str) and str(spec.get("name")).strip()
    ]
    k_neighbors = int(training_cfg.get("k_neighbors", 7))
    distance_epsilon = float(training_cfg.get("distance_epsilon", 1e-6))
    regressors = fit_knn_regressors(train_rows, regression_target_names, k_neighbors=k_neighbors)
    include_prior_regression_memory = bool(
        fine_tuning_cfg.get("include_prior_regression_memory", pretrained_model is not None)
    )
    max_prior_regression_samples = int(fine_tuning_cfg.get("max_prior_regression_samples", 5000))
    if max_prior_regression_samples < -1:
        max_prior_regression_samples = -1
    if pretrained_model is not None and include_prior_regression_memory:
        prior_regressors = None
        prior_heads = pretrained_model.get("heads")
        if isinstance(prior_heads, dict):
            prior_regressors = prior_heads.get("regression_knn")
        regressors = merge_regression_memory(
            current_regressors=regressors,
            prior_regressors=prior_regressors if isinstance(prior_regressors, dict) else None,
            k_neighbors=k_neighbors,
            max_prior_samples=max_prior_regression_samples,
        )

    evaluation, predictions = evaluate_by_split(
        rows=rows,
        success_model=success_model,
        regime_model=regime_model,
        regressors=regressors,
        distance_epsilon=distance_epsilon,
    )

    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    model_id = args.model_id or f"{config_name}_{timestamp}"
    created_at = datetime.now(timezone.utc).isoformat()

    model_artifact = {
        "model_id": model_id,
        "created_at_utc": created_at,
        "dataset_root": str(args.dataset_root),
        "split_path": str(args.split),
        "config_path": str(args.config),
        "config_sha256": sha256_file(args.config),
        "split_sha256": sha256_file(args.split),
        "feature_names": feature_names,
        "preprocessing": {
            "mean": preprocess["mean"],
            "std": preprocess["std"],
            "missing_count_by_feature": missing_count_by_feature,
            "source": preprocessing_source,
        },
        "heads": {
            "success_classification": success_model,
            "regime_classification": regime_model,
            "regression_knn": regressors,
        },
        "training": {
            "k_neighbors": k_neighbors,
            "distance_epsilon": distance_epsilon,
            "run_counts": {
                "total": len(rows),
                "train": sum(1 for row in rows if row["split"] == "train"),
                "val": sum(1 for row in rows if row["split"] == "val"),
                "test": sum(1 for row in rows if row["split"] == "test"),
            },
        },
        "fine_tuning": {
            "active": pretrained_model is not None,
            "init_model_path": str(args.init_model) if args.init_model is not None else None,
            "init_model_sha256": (sha256_file(args.init_model) if args.init_model is not None else None),
            "reuse_pretrained_preprocessing": reuse_pretrained_preprocessing,
            "prior_class_weight": prior_class_weight,
            "include_prior_regression_memory": include_prior_regression_memory,
            "max_prior_regression_samples": max_prior_regression_samples,
        },
    }

    eval_artifact = {
        "model_id": model_id,
        "created_at_utc": created_at,
        "evaluation": evaluation,
        "data_loading_errors": load_errors,
    }

    model_path = args.output_dir / f"{model_id}.model.json"
    eval_path = args.output_dir / f"{model_id}.eval.json"
    predictions_path = args.output_dir / f"{model_id}.predictions.jsonl"

    dump_json(model_path, model_artifact)
    dump_json(eval_path, eval_artifact)
    write_predictions_jsonl(predictions_path, predictions)

    print(f"Wrote model artifact -> {model_path}")
    print(f"Wrote evaluation artifact -> {eval_path}")
    print(f"Wrote predictions -> {predictions_path}")
    if pretrained_model is not None:
        print(f"Fine-tuning source model: {args.init_model}")
    print(json.dumps(evaluation.get("test", {}), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
