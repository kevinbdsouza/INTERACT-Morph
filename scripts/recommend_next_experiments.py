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

from interact_morph.io_utils import dump_json, load_json, load_json_or_yaml

EPS = 1e-12


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Rank next Family A experiments using multimodal model artifacts with "
            "multi-objective scoring, EI/UCB acquisition, and guardrails (MVP-025/026/027)."
        )
    )
    parser.add_argument("--model-artifact", required=True, type=Path, help="Path to *.model.json")
    parser.add_argument(
        "--candidates",
        required=True,
        type=Path,
        help="Candidate JSONL (e.g., output of plan_axisymmetric_sweep.py)",
    )
    parser.add_argument(
        "--config",
        required=True,
        type=Path,
        help="Recommendation config JSON/YAML",
    )
    parser.add_argument(
        "--output",
        required=True,
        type=Path,
        help="Output recommendation report JSON path",
    )
    parser.add_argument(
        "--calibration-artifact",
        default=None,
        type=Path,
        help="Optional calibration report JSON from calibrate_multimodal_uncertainty.py",
    )
    parser.add_argument(
        "--top-k",
        default=None,
        type=int,
        help="Optional top-k override for report recommendations",
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
                raise ValueError(f"{path}:{idx}: invalid JSON ({exc})") from exc
            if not isinstance(payload, dict):
                raise ValueError(f"{path}:{idx}: expected JSON object")
            rows.append(payload)
    return rows


def safe_get(payload: dict[str, Any], path: str) -> Any:
    current: Any = payload
    for token in path.split("."):
        if not isinstance(current, dict) or token not in current:
            return None
        current = current[token]
    return current


def first_present(payload: dict[str, Any], paths: list[str]) -> Any:
    for path in paths:
        value = safe_get(payload, path)
        if value is not None:
            return value
    return None


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


def to_str(value: Any) -> str | None:
    if isinstance(value, str):
        text = value.strip()
        return text or None
    return None


def to_string_list(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []
    items: list[str] = []
    for item in value:
        text = to_str(item)
        if text is not None:
            items.append(text)
    return items


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


def normal_pdf(x: float) -> float:
    return math.exp(-0.5 * x * x) / math.sqrt(2.0 * math.pi)


def normal_cdf(x: float) -> float:
    return 0.5 * (1.0 + math.erf(x / math.sqrt(2.0)))


def squared_distance(a: list[float], b: list[float]) -> float:
    return sum((x - y) ** 2 for x, y in zip(a, b))


def predict_centroid(
    x: list[float],
    model: dict[str, Any] | None,
) -> tuple[str | None, float | None, float | None]:
    if not model:
        return None, None, None

    centroids = model.get("centroids")
    priors = model.get("priors")
    if not isinstance(centroids, dict) or not isinstance(priors, dict) or not centroids:
        return None, None, None

    scores: list[tuple[str, float, float]] = []
    for label, centroid in centroids.items():
        if not isinstance(label, str) or not isinstance(centroid, list):
            continue
        centroid_vec: list[float] = []
        for item in centroid:
            value = to_float(item)
            if value is None:
                centroid_vec = []
                break
            centroid_vec.append(value)
        if len(centroid_vec) != len(x):
            continue
        distance = squared_distance(x, centroid_vec)
        prior = to_float(priors.get(label))
        scores.append((label, distance, float(prior) if prior is not None else 0.0))

    if not scores:
        return None, None, None

    scores.sort(key=lambda item: (item[1], -item[2], item[0]))
    best_label, best_distance, _ = scores[0]
    margin = (scores[1][1] - best_distance) if len(scores) > 1 else None
    return best_label, best_distance, margin


def predict_knn_regression(
    x: list[float],
    model: dict[str, Any] | None,
    distance_epsilon: float,
) -> float | None:
    if not model:
        return None
    vectors = model.get("train_vectors")
    values = model.get("train_values")
    if not isinstance(vectors, list) or not isinstance(values, list):
        return None

    train_pairs: list[tuple[list[float], float]] = []
    for vector_raw, value_raw in zip(vectors, values):
        if not isinstance(vector_raw, list):
            continue
        vector: list[float] = []
        valid = True
        for item in vector_raw:
            x_item = to_float(item)
            if x_item is None:
                valid = False
                break
            vector.append(x_item)
        y_item = to_float(value_raw)
        if not valid or y_item is None or len(vector) != len(x):
            continue
        train_pairs.append((vector, y_item))
    if not train_pairs:
        return None

    distances: list[tuple[float, float]] = []
    for train_vec, y_value in train_pairs:
        distances.append((squared_distance(x, train_vec), y_value))
    distances.sort(key=lambda item: item[0])

    k_neighbors = max(1, int(to_float(model.get("k_neighbors")) or 1))
    neighbors = distances[: min(k_neighbors, len(distances))]
    exact = [y for d, y in neighbors if d <= distance_epsilon]
    if exact:
        return sum(exact) / len(exact)

    weighted_sum = 0.0
    weight_total = 0.0
    for dist, y in neighbors:
        weight = 1.0 / (dist + distance_epsilon)
        weighted_sum += weight * y
        weight_total += weight
    return (weighted_sum / weight_total) if weight_total > 0 else None


def apply_isotonic(probability: float, model: dict[str, Any]) -> float:
    thresholds = model.get("thresholds")
    values = model.get("values")
    if not isinstance(thresholds, list) or not isinstance(values, list):
        return probability
    if len(thresholds) != len(values) or not thresholds:
        return probability

    p = min(1.0, max(0.0, probability))
    pairs: list[tuple[float, float]] = []
    for threshold_raw, value_raw in zip(thresholds, values):
        threshold = to_float(threshold_raw)
        value = to_float(value_raw)
        if threshold is None or value is None:
            continue
        pairs.append((threshold, value))
    if not pairs:
        return probability

    pairs.sort(key=lambda item: item[0])
    for threshold, value in pairs:
        if p <= threshold:
            return float(value)
    return float(pairs[-1][1])


def extract_calibration_head(
    calibration_payload: dict[str, Any] | None,
    head_key: str,
) -> dict[str, Any] | None:
    if not isinstance(calibration_payload, dict):
        return None
    heads = calibration_payload.get("heads")
    if not isinstance(heads, dict):
        return None
    block = heads.get(head_key)
    return block if isinstance(block, dict) else None


def apply_calibration_to_score(score: float, head_block: dict[str, Any] | None) -> dict[str, float]:
    uncal = clamp_prob(sigmoid(score))
    if not head_block:
        return {
            "uncalibrated_probability": uncal,
            "temperature_scaled_probability": uncal,
            "calibrated_probability": uncal,
        }

    temp = 1.0
    temp_block = head_block.get("temperature_scaling")
    if isinstance(temp_block, dict):
        temp_value = to_float(temp_block.get("temperature"))
        if temp_value is not None and temp_value > 0:
            temp = temp_value
    temp_prob = clamp_prob(sigmoid(score / temp))

    final_prob = temp_prob
    isotonic_block = head_block.get("isotonic")
    if isinstance(isotonic_block, dict):
        applied = bool(isotonic_block.get("applied", False))
        model = isotonic_block.get("model")
        if applied and isinstance(model, dict):
            final_prob = clamp_prob(apply_isotonic(temp_prob, model))

    return {
        "uncalibrated_probability": uncal,
        "temperature_scaled_probability": temp_prob,
        "calibrated_probability": final_prob,
    }


FEATURE_PATH_CANDIDATES: dict[str, list[str]] = {
    "impact_velocity_m_s": [
        "control_parameters.impact_velocity_m_s",
        "metadata.control_parameters.impact_velocity_m_s",
    ],
    "droplet_diameter_mm": [
        "control_parameters.droplet_diameter_mm",
        "metadata.control_parameters.droplet_diameter_mm",
    ],
    "shell_outer_diameter_mm": [
        "control_parameters.shell_outer_diameter_mm",
        "metadata.control_parameters.shell_outer_diameter_mm",
    ],
    "interfacial_layer_thickness_mm": [
        "control_parameters.interfacial_layer_thickness_mm",
        "fluid_system.interfacial_layer.thickness_mm",
        "metadata.control_parameters.interfacial_layer_thickness_mm",
        "metadata.fluid_system.interfacial_layer.thickness_mm",
    ],
    "core_density_kg_m3": [
        "fluid_system.core_density_kg_m3",
        "fluid_system.core.density_kg_m3",
        "metadata.fluid_system.core_density_kg_m3",
        "metadata.fluid_system.core.density_kg_m3",
    ],
    "core_viscosity_pa_s": [
        "fluid_system.core_viscosity_pa_s",
        "fluid_system.core.viscosity_pa_s",
        "metadata.fluid_system.core_viscosity_pa_s",
        "metadata.fluid_system.core.viscosity_pa_s",
    ],
    "interfacial_tension_n_m": [
        "fluid_system.interfacial_tension_n_m",
        "metadata.fluid_system.interfacial_tension_n_m",
    ],
    "penetration_depth_max_mm": [
        "summary.penetration_depth_max_mm",
        "derived.summary.penetration_depth_max_mm",
        "metadata.summary.penetration_depth_max_mm",
    ],
    "neck_radius_min_mm": [
        "summary.neck_radius_min_mm",
        "derived.summary.neck_radius_min_mm",
        "metadata.summary.neck_radius_min_mm",
    ],
    "closure_time_ms": [
        "events_ms.closure_time_ms",
        "derived.events_ms.closure_time_ms",
        "metadata.events_ms.closure_time_ms",
    ],
    "detachment_time_ms": [
        "events_ms.detachment_time_ms",
        "derived.events_ms.detachment_time_ms",
        "metadata.events_ms.detachment_time_ms",
    ],
}


def resolve_candidate_feature(candidate: dict[str, Any], feature_name: str) -> float | None:
    path_candidates = FEATURE_PATH_CANDIDATES.get(feature_name, [feature_name])
    for path in path_candidates:
        value = safe_get(candidate, path)
        numeric = to_float(value)
        if numeric is not None:
            return numeric
    direct_value = to_float(candidate.get(feature_name))
    if direct_value is not None:
        return direct_value
    return None


def build_standardized_feature_vector(
    candidate: dict[str, Any],
    feature_names: list[str],
    mean: list[float],
    std: list[float],
) -> tuple[list[float], list[str]]:
    x: list[float] = []
    imputed: list[str] = []
    for idx, name in enumerate(feature_names):
        value = resolve_candidate_feature(candidate, name)
        if value is None:
            value = mean[idx]
            imputed.append(name)
        denom = std[idx] if std[idx] != 0 else 1.0
        x.append((value - mean[idx]) / denom)
    return x, imputed


def collect_training_vectors(regression_heads: dict[str, Any]) -> list[list[float]]:
    vectors: list[list[float]] = []
    seen: set[tuple[float, ...]] = set()
    for model in regression_heads.values():
        if not isinstance(model, dict):
            continue
        raw_vectors = model.get("train_vectors")
        if not isinstance(raw_vectors, list):
            continue
        for raw_vec in raw_vectors:
            if not isinstance(raw_vec, list):
                continue
            vec: list[float] = []
            valid = True
            for item in raw_vec:
                value = to_float(item)
                if value is None:
                    valid = False
                    break
                vec.append(value)
            if not valid or not vec:
                continue
            key = tuple(vec)
            if key in seen:
                continue
            seen.add(key)
            vectors.append(vec)
    return vectors


def compute_feature_bounds(train_vectors: list[list[float]], dimension: int) -> tuple[list[float], list[float]]:
    if not train_vectors:
        return ([-math.inf] * dimension, [math.inf] * dimension)
    mins = [math.inf] * dimension
    maxs = [-math.inf] * dimension
    for vector in train_vectors:
        if len(vector) != dimension:
            continue
        for idx, value in enumerate(vector):
            mins[idx] = min(mins[idx], value)
            maxs[idx] = max(maxs[idx], value)
    for idx in range(dimension):
        if mins[idx] == math.inf:
            mins[idx] = -math.inf
        if maxs[idx] == -math.inf:
            maxs[idx] = math.inf
    return mins, maxs


def nearest_train_distance(x: list[float], train_vectors: list[list[float]]) -> float | None:
    if not train_vectors:
        return None
    distances = [math.sqrt(squared_distance(x, train_x)) for train_x in train_vectors if len(train_x) == len(x)]
    if not distances:
        return None
    return min(distances)


def score_target(value: float | None, target_cfg: dict[str, Any]) -> float | None:
    if value is None:
        return None
    target = to_float(target_cfg.get("target"))
    target_min = to_float(target_cfg.get("target_min"))
    target_max = to_float(target_cfg.get("target_max"))
    if target_min is None and target_max is None and target is not None:
        target_min = target
        target_max = target

    tolerance = to_float(target_cfg.get("soft_tolerance"))
    if tolerance is None:
        tolerance = to_float(target_cfg.get("tolerance"))
    if tolerance is None:
        tolerance = 0.0

    if target_min is not None and value < target_min:
        if tolerance <= 0:
            return 0.0
        return max(0.0, 1.0 - (target_min - value) / tolerance)
    if target_max is not None and value > target_max:
        if tolerance <= 0:
            return 0.0
        return max(0.0, 1.0 - (value - target_max) / tolerance)
    return 1.0


def compute_geometry_score(
    regression_predictions: dict[str, float | None],
    geometry_targets: dict[str, Any],
) -> tuple[float, dict[str, Any]]:
    per_target: dict[str, Any] = {}
    scores: list[float] = []
    for target_name, cfg in geometry_targets.items():
        if not isinstance(cfg, dict):
            continue
        score = score_target(regression_predictions.get(target_name), cfg)
        per_target[target_name] = {
            "prediction": regression_predictions.get(target_name),
            "score": score,
        }
        if score is not None:
            scores.append(score)
    if not scores:
        return 0.0, per_target
    return (sum(scores) / len(scores)), per_target


def compute_uncertainty_proxy(
    success_probability: float | None,
    regime_correctness_probability: float | None,
    nearest_distance: float | None,
    cfg: dict[str, Any],
) -> float:
    weights = cfg.get("weights", {})
    if not isinstance(weights, dict):
        weights = {}

    weight_success = to_float(weights.get("success_probability")) or 0.5
    weight_regime = to_float(weights.get("regime_correctness_probability")) or 0.25
    weight_distance = to_float(weights.get("distance")) or 0.25
    total_weight = max(EPS, weight_success + weight_regime + weight_distance)

    success_unc = 1.0
    if success_probability is not None:
        success_unc = 1.0 - abs(clamp_prob(success_probability) - 0.5) * 2.0

    regime_unc = 1.0
    if regime_correctness_probability is not None:
        regime_unc = 1.0 - clamp_prob(regime_correctness_probability)

    distance_scale = to_float(cfg.get("distance_scale")) or 3.0
    if distance_scale <= 0:
        distance_scale = 3.0
    if nearest_distance is None:
        distance_unc = 1.0
    else:
        distance_unc = min(1.0, max(0.0, nearest_distance / distance_scale))

    return (
        weight_success * success_unc
        + weight_regime * regime_unc
        + weight_distance * distance_unc
    ) / total_weight


def compute_expected_improvement(
    mean_objective: float,
    uncertainty_proxy: float,
    incumbent_objective: float,
    ei_cfg: dict[str, Any],
) -> float:
    xi = to_float(ei_cfg.get("xi")) or 0.0
    uncertainty_scale = to_float(ei_cfg.get("uncertainty_scale")) or 0.15
    sigma = max(EPS, uncertainty_scale * max(0.0, uncertainty_proxy))
    improvement = mean_objective - incumbent_objective - xi
    z = improvement / sigma
    return max(0.0, improvement * normal_cdf(z) + sigma * normal_pdf(z))


def compute_ucb(
    mean_objective: float,
    uncertainty_proxy: float,
    ucb_cfg: dict[str, Any],
) -> float:
    beta = to_float(ucb_cfg.get("beta")) or 0.4
    return mean_objective + beta * max(0.0, uncertainty_proxy)


def infer_candidate_id(candidate: dict[str, Any], idx: int) -> str:
    for key in ("candidate_id", "simulation_id", "run_id", "source_run_id"):
        value = candidate.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip()
    return f"candidate_{idx:06d}"


def build_guardrail_result(
    candidate: dict[str, Any],
    x: list[float],
    feature_names: list[str],
    feature_bounds: tuple[list[float], list[float]],
    nearest_distance: float | None,
    success_probability: float | None,
    guardrail_cfg: dict[str, Any],
) -> dict[str, Any]:
    min_z, max_z = feature_bounds
    max_feature_extrapolation_z = to_float(guardrail_cfg.get("max_feature_extrapolation_z")) or 0.0
    max_extrapolated_features = int(to_float(guardrail_cfg.get("max_extrapolated_features")) or 0)
    max_nearest_train_distance = to_float(guardrail_cfg.get("max_nearest_train_distance"))
    min_success_probability = to_float(guardrail_cfg.get("min_success_probability"))
    allowed_route_types = to_string_list(guardrail_cfg.get("allowed_route_types"))
    allowed_confinement_types = to_string_list(guardrail_cfg.get("allowed_confinement_types"))
    allowed_multilayer_sequences = guardrail_cfg.get("allowed_multilayer_sequences", [])
    if not isinstance(allowed_multilayer_sequences, list):
        allowed_multilayer_sequences = []
    allowed_sequence_keys = {
        tuple(to_string_list(sequence))
        for sequence in allowed_multilayer_sequences
        if to_string_list(sequence)
    }

    extrapolated_features: list[dict[str, Any]] = []
    for idx, value in enumerate(x):
        lower = min_z[idx]
        upper = max_z[idx]
        violation = None
        if value < lower - max_feature_extrapolation_z:
            violation = "below"
        elif value > upper + max_feature_extrapolation_z:
            violation = "above"
        if violation is not None:
            extrapolated_features.append(
                {
                    "feature": feature_names[idx],
                    "z_value": value,
                    "train_min_z": lower,
                    "train_max_z": upper,
                    "direction": violation,
                }
            )

    reasons: list[str] = []
    if len(extrapolated_features) > max_extrapolated_features:
        reasons.append(
            f"feature_extrapolation_count>{max_extrapolated_features}"
        )
    if (
        max_nearest_train_distance is not None
        and nearest_distance is not None
        and nearest_distance > max_nearest_train_distance
    ):
        reasons.append(
            f"nearest_train_distance>{max_nearest_train_distance}"
        )
    if (
        min_success_probability is not None
        and success_probability is not None
        and success_probability < min_success_probability
    ):
        reasons.append(
            f"success_probability<{min_success_probability}"
        )

    route_type = to_str(
        first_present(
            candidate,
            [
                "control_parameters.route_type",
                "metadata.control_parameters.route_type",
                "route_type",
            ],
        )
    )
    confinement_type = to_str(
        first_present(
            candidate,
            [
                "control_parameters.confinement_type",
                "metadata.control_parameters.confinement_type",
                "confinement_type",
            ],
        )
    )
    shell_volume_ul = to_float(
        first_present(
            candidate,
            [
                "control_parameters.shell_volume_ul",
                "metadata.control_parameters.shell_volume_ul",
                "shell_volume_ul",
            ],
        )
    )
    loop_min_volume_ul = to_float(
        first_present(
            candidate,
            [
                "control_parameters.loop_geometry.minimum_volume_ul",
                "metadata.control_parameters.loop_geometry.minimum_volume_ul",
            ],
        )
    )
    loop_overflow_volume_ul = to_float(
        first_present(
            candidate,
            [
                "control_parameters.loop_geometry.overflow_volume_ul",
                "metadata.control_parameters.loop_geometry.overflow_volume_ul",
            ],
        )
    )
    if loop_min_volume_ul is None:
        loop_min_volume_ul = to_float(guardrail_cfg.get("loop_min_volume_ul"))
    if loop_overflow_volume_ul is None:
        loop_overflow_volume_ul = to_float(guardrail_cfg.get("loop_overflow_volume_ul"))

    if allowed_route_types and route_type is not None and route_type not in allowed_route_types:
        reasons.append(f"route_type_not_allowed:{route_type}")
    if allowed_confinement_types and confinement_type is not None and confinement_type not in allowed_confinement_types:
        reasons.append(f"confinement_type_not_allowed:{confinement_type}")

    if confinement_type == "circular_loop_assisted":
        if shell_volume_ul is None:
            reasons.append("loop_shell_volume_missing")
        else:
            if loop_min_volume_ul is not None and shell_volume_ul < loop_min_volume_ul:
                reasons.append(f"loop_shell_volume<{loop_min_volume_ul}")
            if loop_overflow_volume_ul is not None and shell_volume_ul > loop_overflow_volume_ul:
                reasons.append(f"loop_shell_volume>{loop_overflow_volume_ul}")
    elif confinement_type != "circular_loop_assisted" and shell_volume_ul is not None:
        global_min_volume = to_float(guardrail_cfg.get("shell_volume_min_ul"))
        global_max_volume = to_float(guardrail_cfg.get("shell_volume_max_ul"))
        if global_min_volume is not None and shell_volume_ul < global_min_volume:
            reasons.append(f"shell_volume<{global_min_volume}")
        if global_max_volume is not None and shell_volume_ul > global_max_volume:
            reasons.append(f"shell_volume>{global_max_volume}")

    layer_sequence = to_string_list(
        first_present(
            candidate,
            [
                "outcomes.layer_sequence",
                "derived.summary.layer_sequence",
                "metadata.outcomes.layer_sequence",
                "layer_sequence",
            ],
        )
    )
    if route_type == "multilayer":
        if not layer_sequence:
            reasons.append("multilayer_sequence_missing")
        elif allowed_sequence_keys and tuple(layer_sequence) not in allowed_sequence_keys:
            reasons.append("multilayer_sequence_not_allowed")
    elif route_type == "single_layer" and len(layer_sequence) > 1:
        reasons.append("single_layer_route_has_multilayer_sequence")

    return {
        "accepted": len(reasons) == 0,
        "reasons": reasons,
        "nearest_train_distance": nearest_distance,
        "extrapolated_features": extrapolated_features,
        "route_type": route_type,
        "confinement_type": confinement_type,
        "shell_volume_ul": shell_volume_ul,
        "loop_volume_window_ul": {
            "minimum": loop_min_volume_ul,
            "overflow": loop_overflow_volume_ul,
        },
        "layer_sequence": layer_sequence,
    }


def collect_incumbent_from_training(
    success_model: dict[str, Any] | None,
    regression_heads: dict[str, Any],
    geometry_targets: dict[str, Any],
    objective_weights: dict[str, Any],
    uncertainty_penalty_default: float,
) -> float | None:
    run_map: dict[str, dict[str, Any]] = {}
    for target_name, model in regression_heads.items():
        if not isinstance(model, dict):
            continue
        run_ids = model.get("train_run_ids")
        vectors = model.get("train_vectors")
        values = model.get("train_values")
        if not isinstance(run_ids, list) or not isinstance(vectors, list) or not isinstance(values, list):
            continue
        for run_id_raw, vec_raw, value_raw in zip(run_ids, vectors, values):
            if not isinstance(run_id_raw, str) or not run_id_raw:
                continue
            if not isinstance(vec_raw, list):
                continue
            vec: list[float] = []
            valid = True
            for item in vec_raw:
                numeric = to_float(item)
                if numeric is None:
                    valid = False
                    break
                vec.append(numeric)
            value = to_float(value_raw)
            if not valid or value is None:
                continue
            state = run_map.setdefault(run_id_raw, {"x": vec, "regression": {}})
            state["regression"][target_name] = value

    if not run_map:
        return None

    w_success = to_float(objective_weights.get("success_probability")) or 0.55
    w_geometry = to_float(objective_weights.get("geometry_target")) or 0.35
    w_uncertainty = to_float(objective_weights.get("uncertainty_penalty")) or uncertainty_penalty_default

    objective_values: list[float] = []
    for state in run_map.values():
        x = state["x"]
        pred_success_label, _, success_margin = predict_centroid(x, success_model)
        if pred_success_label is None or success_margin is None:
            success_probability = 0.5
        else:
            signed = success_margin if pred_success_label == "true" else -success_margin
            success_probability = clamp_prob(sigmoid(signed))
        geometry_score, _ = compute_geometry_score(
            regression_predictions=state["regression"],
            geometry_targets=geometry_targets,
        )
        objective = (
            w_success * success_probability
            + w_geometry * geometry_score
            - w_uncertainty * 0.0
        )
        objective_values.append(objective)

    if not objective_values:
        return None
    return max(objective_values)


def main() -> int:
    args = parse_args()

    model = load_json(args.model_artifact)
    config = load_json_or_yaml(args.config)
    candidates = read_jsonl(args.candidates)
    calibration = load_json(args.calibration_artifact) if args.calibration_artifact else None

    if not isinstance(model, dict):
        raise ValueError("model artifact must be a JSON object")
    if not isinstance(config, dict):
        raise ValueError("recommendation config must be a JSON/YAML object")
    if calibration is not None and not isinstance(calibration, dict):
        raise ValueError("calibration artifact must be a JSON object")
    if not candidates:
        raise ValueError("candidate JSONL contains no rows")

    feature_names = model.get("feature_names")
    if not isinstance(feature_names, list) or not feature_names:
        raise ValueError("model artifact missing non-empty feature_names")
    feature_names = [str(name) for name in feature_names]

    preprocessing = model.get("preprocessing")
    if not isinstance(preprocessing, dict):
        raise ValueError("model artifact missing preprocessing block")
    mean_raw = preprocessing.get("mean")
    std_raw = preprocessing.get("std")
    if not isinstance(mean_raw, list) or not isinstance(std_raw, list):
        raise ValueError("model preprocessing must include mean/std arrays")
    if len(mean_raw) != len(feature_names) or len(std_raw) != len(feature_names):
        raise ValueError("feature_names and preprocessing mean/std lengths do not match")

    mean: list[float] = []
    std: list[float] = []
    for idx in range(len(feature_names)):
        mean_item = to_float(mean_raw[idx])
        std_item = to_float(std_raw[idx])
        if mean_item is None:
            raise ValueError(f"preprocessing.mean[{idx}] is non-numeric")
        if std_item is None:
            raise ValueError(f"preprocessing.std[{idx}] is non-numeric")
        mean.append(mean_item)
        std.append(std_item if std_item != 0 else 1.0)

    heads = model.get("heads")
    if not isinstance(heads, dict):
        raise ValueError("model artifact missing heads")
    success_model = heads.get("success_classification")
    regime_model = heads.get("regime_classification")
    regression_heads = heads.get("regression_knn")
    if not isinstance(regression_heads, dict):
        regression_heads = {}

    training_cfg = model.get("training")
    if not isinstance(training_cfg, dict):
        training_cfg = {}
    distance_epsilon = to_float(training_cfg.get("distance_epsilon")) or 1e-6
    if distance_epsilon <= 0:
        distance_epsilon = 1e-6

    objective_cfg = config.get("objective")
    if not isinstance(objective_cfg, dict):
        objective_cfg = {}
    objective_weights = objective_cfg.get("weights")
    if not isinstance(objective_weights, dict):
        objective_weights = {}
    geometry_targets = objective_cfg.get("geometry_targets")
    if not isinstance(geometry_targets, dict):
        geometry_targets = {}

    uncertainty_cfg = objective_cfg.get("uncertainty")
    if not isinstance(uncertainty_cfg, dict):
        uncertainty_cfg = {}

    w_success = to_float(objective_weights.get("success_probability")) or 0.55
    w_geometry = to_float(objective_weights.get("geometry_target")) or 0.35
    w_uncertainty = to_float(objective_weights.get("uncertainty_penalty")) or 0.10

    acquisition_cfg = config.get("acquisition")
    if not isinstance(acquisition_cfg, dict):
        acquisition_cfg = {}
    ranking_method = str(acquisition_cfg.get("method", "ei")).strip().lower()
    if ranking_method not in {"ei", "ucb"}:
        raise ValueError("acquisition.method must be 'ei' or 'ucb'")
    ei_cfg = acquisition_cfg.get("ei")
    if not isinstance(ei_cfg, dict):
        ei_cfg = {}
    ucb_cfg = acquisition_cfg.get("ucb")
    if not isinstance(ucb_cfg, dict):
        ucb_cfg = {}

    top_k = args.top_k if args.top_k is not None else int(to_float(acquisition_cfg.get("top_k")) or 10)
    if top_k <= 0:
        raise ValueError("top_k must be > 0")

    guardrail_cfg = config.get("guardrails")
    if not isinstance(guardrail_cfg, dict):
        guardrail_cfg = {}
    guardrails_enabled = bool(guardrail_cfg.get("enabled", True))

    success_calibration_head = extract_calibration_head(calibration, "success_probability")
    regime_calibration_head = extract_calibration_head(
        calibration,
        "regime_top1_correctness_probability",
    )

    train_vectors = collect_training_vectors(regression_heads)
    if not train_vectors:
        centroids = None
        if isinstance(success_model, dict):
            centroids = success_model.get("centroids")
        if isinstance(centroids, dict):
            for centroid in centroids.values():
                if not isinstance(centroid, list):
                    continue
                vector: list[float] = []
                valid = True
                for item in centroid:
                    value = to_float(item)
                    if value is None:
                        valid = False
                        break
                    vector.append(value)
                if valid and len(vector) == len(feature_names):
                    train_vectors.append(vector)

    feature_bounds = compute_feature_bounds(train_vectors, dimension=len(feature_names))

    incumbent_objective = to_float(ei_cfg.get("incumbent_objective"))
    if incumbent_objective is None:
        incumbent_objective = collect_incumbent_from_training(
            success_model=success_model if isinstance(success_model, dict) else None,
            regression_heads=regression_heads,
            geometry_targets=geometry_targets,
            objective_weights=objective_weights,
            uncertainty_penalty_default=w_uncertainty,
        )
    if incumbent_objective is None:
        incumbent_objective = 0.0

    accepted: list[dict[str, Any]] = []
    rejected: list[dict[str, Any]] = []
    for idx, candidate in enumerate(candidates, start=1):
        candidate_id = infer_candidate_id(candidate, idx)
        x, imputed_features = build_standardized_feature_vector(
            candidate=candidate,
            feature_names=feature_names,
            mean=mean,
            std=std,
        )

        pred_success_label, success_distance, success_margin = predict_centroid(
            x,
            success_model if isinstance(success_model, dict) else None,
        )
        pred_regime_label, regime_distance, regime_margin = predict_centroid(
            x,
            regime_model if isinstance(regime_model, dict) else None,
        )

        success_probability_block = None
        success_probability = None
        if pred_success_label is not None and success_margin is not None:
            signed_success_score = success_margin if pred_success_label == "true" else -success_margin
            success_probability_block = apply_calibration_to_score(
                score=signed_success_score,
                head_block=success_calibration_head,
            )
            success_probability = success_probability_block["calibrated_probability"]

        regime_correctness_block = None
        regime_correctness_probability = None
        if regime_margin is not None:
            regime_correctness_block = apply_calibration_to_score(
                score=regime_margin,
                head_block=regime_calibration_head,
            )
            regime_correctness_probability = regime_correctness_block["calibrated_probability"]

        regression_predictions: dict[str, float | None] = {}
        for target_name, reg_model in regression_heads.items():
            if not isinstance(target_name, str):
                continue
            regression_predictions[target_name] = predict_knn_regression(
                x=x,
                model=reg_model if isinstance(reg_model, dict) else None,
                distance_epsilon=distance_epsilon,
            )

        geometry_score, geometry_breakdown = compute_geometry_score(
            regression_predictions=regression_predictions,
            geometry_targets=geometry_targets,
        )

        nearest_distance = nearest_train_distance(x, train_vectors)
        uncertainty_proxy = compute_uncertainty_proxy(
            success_probability=success_probability,
            regime_correctness_probability=regime_correctness_probability,
            nearest_distance=nearest_distance,
            cfg=uncertainty_cfg,
        )

        mean_objective = (
            w_success * (success_probability if success_probability is not None else 0.0)
            + w_geometry * geometry_score
            - w_uncertainty * uncertainty_proxy
        )

        ei_score = compute_expected_improvement(
            mean_objective=mean_objective,
            uncertainty_proxy=uncertainty_proxy,
            incumbent_objective=incumbent_objective,
            ei_cfg=ei_cfg,
        )
        ucb_score = compute_ucb(
            mean_objective=mean_objective,
            uncertainty_proxy=uncertainty_proxy,
            ucb_cfg=ucb_cfg,
        )
        ranking_score = ei_score if ranking_method == "ei" else ucb_score

        guardrail_result = build_guardrail_result(
            candidate=candidate,
            x=x,
            feature_names=feature_names,
            feature_bounds=feature_bounds,
            nearest_distance=nearest_distance,
            success_probability=success_probability,
            guardrail_cfg=guardrail_cfg,
        )
        accepted_by_guardrail = (not guardrails_enabled) or bool(guardrail_result.get("accepted", False))

        record = {
            "candidate_id": candidate_id,
            "ranking_score": ranking_score,
            "objective": {
                "mean_objective": mean_objective,
                "success_probability_weighted": w_success
                * (success_probability if success_probability is not None else 0.0),
                "geometry_weighted": w_geometry * geometry_score,
                "uncertainty_penalty_weighted": w_uncertainty * uncertainty_proxy,
                "weights": {
                    "success_probability": w_success,
                    "geometry_target": w_geometry,
                    "uncertainty_penalty": w_uncertainty,
                },
                "geometry_score": geometry_score,
                "geometry_breakdown": geometry_breakdown,
            },
            "acquisition": {
                "method": ranking_method,
                "ei": ei_score,
                "ucb": ucb_score,
                "incumbent_objective": incumbent_objective,
            },
            "predictions": {
                "success_label": pred_success_label,
                "success_distance": success_distance,
                "success_margin": success_margin,
                "success_probability": success_probability_block,
                "regime_label": pred_regime_label,
                "regime_distance": regime_distance,
                "regime_margin": regime_margin,
                "regime_top1_correctness_probability": regime_correctness_block,
                "regression": regression_predictions,
            },
            "uncertainty_proxy": uncertainty_proxy,
            "guardrails": guardrail_result,
            "imputed_feature_names": imputed_features,
            "candidate": {
                "family": candidate.get("family"),
                "sweep_name": candidate.get("sweep_name"),
                "control_parameters": candidate.get("control_parameters"),
                "fluid_system": candidate.get("fluid_system"),
                "dimensionless": candidate.get("dimensionless"),
            },
        }

        if accepted_by_guardrail:
            accepted.append(record)
        else:
            rejected.append(record)

    accepted.sort(key=lambda item: (item["ranking_score"], item["objective"]["mean_objective"]), reverse=True)
    ranked = []
    for rank, item in enumerate(accepted[:top_k], start=1):
        output_item = dict(item)
        output_item["rank"] = rank
        ranked.append(output_item)

    report = {
        "name": str(config.get("name", "family_a_recommendation")),
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "model_id": model.get("model_id"),
        "inputs": {
            "model_artifact": str(args.model_artifact),
            "candidate_jsonl": str(args.candidates),
            "recommendation_config": str(args.config),
            "calibration_artifact": str(args.calibration_artifact) if args.calibration_artifact else None,
        },
        "summary": {
            "candidate_count": len(candidates),
            "accepted_count": len(accepted),
            "rejected_count": len(rejected),
            "ranking_method": ranking_method,
            "top_k": top_k,
            "incumbent_objective": incumbent_objective,
            "guardrails_enabled": guardrails_enabled,
        },
        "recommendations": ranked,
        "rejected_candidates": rejected,
    }
    dump_json(args.output, report)

    print(f"Wrote recommendation report -> {args.output}")
    print(
        f"Candidates: total={len(candidates)}, accepted={len(accepted)}, "
        f"rejected={len(rejected)}, returned_top_k={len(ranked)}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
