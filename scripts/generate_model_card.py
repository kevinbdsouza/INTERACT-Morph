#!/usr/bin/env python3
from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = PROJECT_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from interact_capsules.io_utils import load_json

DEFAULT_TEMPLATE = PROJECT_ROOT / "templates" / "model_card.template.md"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate a standardized model card from model/eval artifacts (MVP-024)."
    )
    parser.add_argument("--model-artifact", required=True, type=Path, help="Path to *.model.json")
    parser.add_argument("--eval-artifact", required=True, type=Path, help="Path to *.eval.json")
    parser.add_argument(
        "--calibration-artifact",
        default=None,
        type=Path,
        help="Optional calibration artifact JSON from calibrate_multimodal_uncertainty.py",
    )
    parser.add_argument("--output", required=True, type=Path, help="Output markdown path")
    parser.add_argument(
        "--template",
        default=DEFAULT_TEMPLATE,
        type=Path,
        help="Markdown template with placeholders",
    )
    return parser.parse_args()


def fmt(value: Any, digits: int = 4) -> str:
    if value is None:
        return "N/A"
    if isinstance(value, float):
        return f"{value:.{digits}f}"
    return str(value)


def render_split_metric_table(evaluation: dict[str, Any], task_key: str) -> str:
    lines = ["| Split | Count | Accuracy | F1 | Macro-F1 |", "|---|---:|---:|---:|---:|"]
    for split_name in ("train", "val", "test"):
        split_payload = evaluation.get(split_name, {})
        if not isinstance(split_payload, dict):
            split_payload = {}

        metrics = split_payload.get(task_key, {})
        if not isinstance(metrics, dict):
            metrics = {}

        count = metrics.get("count")
        accuracy = metrics.get("accuracy")
        f1 = metrics.get("f1")
        macro_f1 = metrics.get("macro_f1")
        lines.append(
            f"| {split_name} | {fmt(count, 0)} | {fmt(accuracy)} | {fmt(f1)} | {fmt(macro_f1)} |"
        )
    return "\n".join(lines)


def render_regression_tables(evaluation: dict[str, Any]) -> str:
    target_names: set[str] = set()
    for split_name in ("train", "val", "test"):
        split_payload = evaluation.get(split_name, {})
        if not isinstance(split_payload, dict):
            continue
        metrics = split_payload.get("regression_metrics", {})
        if isinstance(metrics, dict):
            target_names.update(str(name) for name in metrics.keys())

    if not target_names:
        return "No regression metrics available."

    sections: list[str] = []
    for target_name in sorted(target_names):
        lines = [f"### {target_name}", "| Split | Count | MAE | RMSE |", "|---|---:|---:|---:|"]
        for split_name in ("train", "val", "test"):
            split_payload = evaluation.get(split_name, {})
            if not isinstance(split_payload, dict):
                split_payload = {}
            regression_metrics = split_payload.get("regression_metrics", {})
            if not isinstance(regression_metrics, dict):
                regression_metrics = {}
            target_metrics = regression_metrics.get(target_name, {})
            if not isinstance(target_metrics, dict):
                target_metrics = {}

            lines.append(
                f"| {split_name} | {fmt(target_metrics.get('count'), 0)} | {fmt(target_metrics.get('mae'))} | {fmt(target_metrics.get('rmse'))} |"
            )
        sections.append("\n".join(lines))

    return "\n\n".join(sections)


def render_feature_list(feature_names: list[Any]) -> str:
    if not feature_names:
        return "- N/A"
    return "\n".join(f"- `{str(name)}`" for name in feature_names)


def render_calibration_summary(calibration_payload: dict[str, Any] | None) -> str:
    if calibration_payload is None:
        return "Calibration artifact not provided."

    heads = calibration_payload.get("heads", {})
    if not isinstance(heads, dict):
        return "Calibration artifact has no `heads` object."

    success = heads.get("success_probability", {})
    if not isinstance(success, dict):
        success = {}
    metrics = success.get("metrics", {}) if isinstance(success.get("metrics"), dict) else {}
    final_block = metrics.get("final", {}) if isinstance(metrics.get("final"), dict) else {}
    uncal_block = metrics.get("uncalibrated", {}) if isinstance(metrics.get("uncalibrated"), dict) else {}

    uncal_overall = uncal_block.get("overall", {}) if isinstance(uncal_block.get("overall"), dict) else {}
    final_overall = final_block.get("overall", {}) if isinstance(final_block.get("overall"), dict) else {}

    temperature = None
    temp_block = success.get("temperature_scaling")
    if isinstance(temp_block, dict):
        temperature = temp_block.get("temperature")

    lines = [
        "- Success head calibration:",
        f"  temperature: `{fmt(temperature)}`",
        f"  log-loss (uncalibrated -> final): `{fmt(uncal_overall.get('log_loss'))}` -> `{fmt(final_overall.get('log_loss'))}`",
        f"  brier (uncalibrated -> final): `{fmt(uncal_overall.get('brier'))}` -> `{fmt(final_overall.get('brier'))}`",
        f"  ECE (uncalibrated -> final): `{fmt(uncal_overall.get('ece'))}` -> `{fmt(final_overall.get('ece'))}`",
    ]
    return "\n".join(lines)


def render_data_loading_notes(eval_payload: dict[str, Any]) -> str:
    errors = eval_payload.get("data_loading_errors", [])
    if not isinstance(errors, list):
        return "- Data loading diagnostics unavailable."
    if not errors:
        return "- No data-loading warnings were recorded."

    shown = [str(item) for item in errors[:10]]
    lines = [f"- {item}" for item in shown]
    if len(errors) > len(shown):
        lines.append(f"- ... ({len(errors) - len(shown)} additional warnings omitted)")
    return "\n".join(lines)


def build_context(
    model_payload: dict[str, Any],
    eval_payload: dict[str, Any],
    calibration_payload: dict[str, Any] | None,
) -> dict[str, str]:
    evaluation = eval_payload.get("evaluation", {})
    if not isinstance(evaluation, dict):
        evaluation = {}

    run_counts = model_payload.get("training", {}).get("run_counts", {})
    if not isinstance(run_counts, dict):
        run_counts = {}

    context = {
        "{{MODEL_ID}}": str(model_payload.get("model_id", "unknown_model")),
        "{{CREATED_AT_UTC}}": str(model_payload.get("created_at_utc", "unknown")),
        "{{DATASET_ROOT}}": str(model_payload.get("dataset_root", "unknown")),
        "{{SPLIT_PATH}}": str(model_payload.get("split_path", "unknown")),
        "{{RUN_COUNT_TOTAL}}": fmt(run_counts.get("total"), 0),
        "{{RUN_COUNT_TRAIN}}": fmt(run_counts.get("train"), 0),
        "{{RUN_COUNT_VAL}}": fmt(run_counts.get("val"), 0),
        "{{RUN_COUNT_TEST}}": fmt(run_counts.get("test"), 0),
        "{{FEATURE_LIST}}": render_feature_list(model_payload.get("feature_names", [])),
        "{{SUCCESS_METRICS_TABLE}}": render_split_metric_table(
            evaluation=evaluation,
            task_key="success_metrics",
        ),
        "{{REGIME_METRICS_TABLE}}": render_split_metric_table(
            evaluation=evaluation,
            task_key="regime_metrics",
        ),
        "{{REGRESSION_METRICS_TABLES}}": render_regression_tables(evaluation=evaluation),
        "{{CALIBRATION_SUMMARY}}": render_calibration_summary(calibration_payload),
        "{{DATA_LOADING_NOTES}}": render_data_loading_notes(eval_payload),
        "{{CONFIG_SHA256}}": str(model_payload.get("config_sha256", "unknown")),
        "{{SPLIT_SHA256}}": str(model_payload.get("split_sha256", "unknown")),
        "{{MODEL_ARTIFACT_PATH}}": str(model_payload.get("model_artifact_path", "n/a")),
        "{{EVAL_ARTIFACT_PATH}}": str(eval_payload.get("eval_artifact_path", "n/a")),
        "{{CALIBRATION_ARTIFACT_PATH}}": (
            str(calibration_payload.get("calibration_artifact_path", "n/a"))
            if isinstance(calibration_payload, dict)
            else "n/a"
        ),
    }
    return context


def render_template(template_text: str, context: dict[str, str]) -> str:
    rendered = template_text
    for key, value in context.items():
        rendered = rendered.replace(key, value)
    return rendered


def main() -> int:
    args = parse_args()

    model_payload = load_json(args.model_artifact)
    eval_payload = load_json(args.eval_artifact)
    calibration_payload = load_json(args.calibration_artifact) if args.calibration_artifact else None

    if not isinstance(model_payload, dict):
        raise ValueError("Model artifact must contain a JSON object")
    if not isinstance(eval_payload, dict):
        raise ValueError("Eval artifact must contain a JSON object")
    if calibration_payload is not None and not isinstance(calibration_payload, dict):
        raise ValueError("Calibration artifact must contain a JSON object")

    model_payload = dict(model_payload)
    eval_payload = dict(eval_payload)
    if calibration_payload is not None:
        calibration_payload = dict(calibration_payload)

    model_payload["model_artifact_path"] = str(args.model_artifact)
    eval_payload["eval_artifact_path"] = str(args.eval_artifact)
    if calibration_payload is not None:
        calibration_payload["calibration_artifact_path"] = str(args.calibration_artifact)

    if args.template.exists():
        template_text = args.template.read_text(encoding="utf-8")
    else:
        raise FileNotFoundError(f"Template not found: {args.template}")

    context = build_context(
        model_payload=model_payload,
        eval_payload=eval_payload,
        calibration_payload=calibration_payload,
    )
    rendered = render_template(template_text, context)

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(rendered.rstrip() + "\n", encoding="utf-8")

    print(f"Wrote model card -> {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
