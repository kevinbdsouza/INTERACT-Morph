#!/usr/bin/env python3
from __future__ import annotations

import argparse
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = PROJECT_ROOT / "src"
import sys

if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from interact_capsules.io_utils import dump_json, load_json, load_json_or_yaml


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Build an experiment execution template from recommendation outputs "
            "(MVP-031)."
        )
    )
    parser.add_argument(
        "--recommendation-report",
        required=True,
        type=Path,
        help="Recommendation report JSON from recommend_next_experiments.py",
    )
    parser.add_argument(
        "--config",
        required=True,
        type=Path,
        help="Execution-template config JSON/YAML",
    )
    parser.add_argument("--output", required=True, type=Path, help="Output template JSON path")
    parser.add_argument(
        "--markdown-output",
        default=None,
        type=Path,
        help="Optional markdown protocol output path",
    )
    parser.add_argument(
        "--top-k",
        default=None,
        type=int,
        help="Optional top-k override for planned runs",
    )
    parser.add_argument(
        "--campaign-id",
        default=None,
        help="Optional campaign identifier override",
    )
    return parser.parse_args()


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
        return float(value)
    if isinstance(value, str) and value.strip():
        try:
            return float(value.strip())
        except ValueError:
            return None
    return None


def fmt(value: float | None, digits: int = 4) -> str:
    if value is None:
        return "N/A"
    text = f"{value:.{digits}f}"
    return text.rstrip("0").rstrip(".")


def main() -> int:
    args = parse_args()

    recommendation_report = load_json(args.recommendation_report)
    if not isinstance(recommendation_report, dict):
        print(f"Recommendation report must be an object: {args.recommendation_report}")
        return 1

    config = load_json_or_yaml(args.config)
    if not isinstance(config, dict):
        print(f"Config must be an object: {args.config}")
        return 1

    protocol_cfg = config.get("protocol", {})
    if not isinstance(protocol_cfg, dict):
        protocol_cfg = {}

    output_cfg = config.get("output", {})
    if not isinstance(output_cfg, dict):
        output_cfg = {}

    recommendations = recommendation_report.get("recommendations", [])
    if not isinstance(recommendations, list):
        recommendations = []

    default_top_k = int(protocol_cfg.get("default_top_k", 5))
    top_k = args.top_k if args.top_k is not None else default_top_k
    if top_k <= 0:
        print("--top-k must be positive")
        return 1

    campaign_prefix = str(protocol_cfg.get("campaign_id_prefix", "C3_MODEL_GUIDED")).strip() or "C3_MODEL_GUIDED"
    run_prefix = str(protocol_cfg.get("run_id_prefix", "A_EXP")).strip() or "A_EXP"
    created_at = datetime.now(timezone.utc).isoformat()
    today = datetime.now(timezone.utc).strftime("%Y%m%d")
    campaign_id = args.campaign_id or f"{campaign_prefix}_{today}"

    planned_runs: list[dict[str, Any]] = []
    for idx, row in enumerate(recommendations[:top_k], start=1):
        if not isinstance(row, dict):
            continue

        candidate_id = str(row.get("candidate_id", f"CAND_{idx:03d}"))
        run_id = f"{run_prefix}_{idx:03d}"

        success_probability = to_float(
            safe_get(row, "predictions.success_probability.calibrated_probability")
        )
        if success_probability is None:
            success_probability = to_float(
                safe_get(row, "predictions.success_probability.temperature_scaled_probability")
            )
        if success_probability is None:
            success_probability = to_float(
                safe_get(row, "predictions.success_probability.uncalibrated_probability")
            )

        guardrail_reasons = safe_get(row, "guardrails.reasons")
        if not isinstance(guardrail_reasons, list):
            guardrail_reasons = []

        planned_runs.append(
            {
                "rank": int(row.get("rank", idx)),
                "planned_run_id": run_id,
                "candidate_id": candidate_id,
                "ranking_score": to_float(row.get("ranking_score")),
                "predicted_success_probability": success_probability,
                "predicted_regime": safe_get(row, "predictions.regime_label"),
                "predicted_geometry": safe_get(row, "predictions.regression") or {},
                "uncertainty_proxy": to_float(row.get("uncertainty_proxy")),
                "guardrail_status": {
                    "accepted": bool(safe_get(row, "guardrails.accepted")),
                    "reasons": guardrail_reasons,
                    "nearest_train_distance": to_float(safe_get(row, "guardrails.nearest_train_distance")),
                },
                "candidate_parameters": row.get("candidate", {}),
                "execution_status": "planned",
                "operator_notes": "",
            }
        )

    global_checklist = config.get("global_checklist", [])
    if not isinstance(global_checklist, list):
        global_checklist = []
    per_run_measurements = config.get("per_run_measurements", [])
    if not isinstance(per_run_measurements, list):
        per_run_measurements = []
    stop_conditions = config.get("stop_conditions", [])
    if not isinstance(stop_conditions, list):
        stop_conditions = []

    template = {
        "task_id": "MVP-031",
        "name": str(config.get("name", "family_a_experiment_execution_v1")),
        "created_at_utc": created_at,
        "campaign_id": campaign_id,
        "source_recommendation_report": str(args.recommendation_report),
        "objective_note": str(
            config.get(
                "objective_note",
                "Execute model-ranked Family A runs with protocolized measurement capture.",
            )
        ),
        "recommendation_summary": recommendation_report.get("summary", {}),
        "protocol": {
            "top_k_selected": len(planned_runs),
            "global_checklist": global_checklist,
            "per_run_measurements": per_run_measurements,
            "stop_conditions": stop_conditions,
        },
        "planned_runs": planned_runs,
        "signoff": {
            "prepared_by": "",
            "prepared_at_utc": created_at,
            "approved_by": "",
            "approval_notes": "",
        },
    }

    dump_json(args.output, template)

    markdown_output = args.markdown_output
    if markdown_output is None and bool(output_cfg.get("write_default_markdown", False)):
        markdown_output = args.output.with_suffix(".md")

    if markdown_output is not None:
        lines: list[str] = []
        lines.append("# Experiment Execution Template (MVP-031)")
        lines.append("")
        lines.append(f"- Campaign ID: `{campaign_id}`")
        lines.append(f"- Generated: `{created_at}`")
        lines.append(f"- Source recommendation report: `{args.recommendation_report}`")
        lines.append(f"- Planned runs: `{len(planned_runs)}`")
        lines.append("")
        lines.append("## Objective")
        lines.append("")
        lines.append(str(template["objective_note"]))
        lines.append("")
        lines.append("## Pre-Run Checklist")
        lines.append("")
        if global_checklist:
            for item in global_checklist:
                lines.append(f"- [ ] {item}")
        else:
            lines.append("- [ ] Confirm latest model, calibration, and recommendation artifacts are version-locked.")
        lines.append("")
        lines.append("## Planned Runs")
        lines.append("")
        lines.append("| Rank | Planned Run ID | Candidate ID | Success Prob | Thickness (um) | Eccentricity | Guardrail |")
        lines.append("|---:|---|---|---:|---:|---:|---|")
        for run in planned_runs:
            geometry = run.get("predicted_geometry", {})
            if not isinstance(geometry, dict):
                geometry = {}
            accepted = safe_get(run, "guardrail_status.accepted")
            guardrail = "accepted" if accepted else "review"
            lines.append(
                f"| {run['rank']} | {run['planned_run_id']} | {run['candidate_id']} | "
                f"{fmt(to_float(run.get('predicted_success_probability')), 3)} | "
                f"{fmt(to_float(geometry.get('shell_thickness_mean_um')), 2)} | "
                f"{fmt(to_float(geometry.get('capsule_eccentricity')), 4)} | "
                f"{guardrail} |"
            )
        lines.append("")
        lines.append("## Per-Run Measurements")
        lines.append("")
        if per_run_measurements:
            for item in per_run_measurements:
                lines.append(f"- [ ] {item}")
        else:
            lines.append("- [ ] Capture run metadata, outcome labels, and derived geometry metrics.")
        lines.append("")
        lines.append("## Stop Conditions")
        lines.append("")
        if stop_conditions:
            for item in stop_conditions:
                lines.append(f"- [ ] {item}")
        else:
            lines.append("- [ ] Pause campaign if guardrail violations or repeated unsafe outcomes are observed.")
        markdown_output.parent.mkdir(parents=True, exist_ok=True)
        markdown_output.write_text("\n".join(lines) + "\n", encoding="utf-8")

    print(f"Wrote experiment execution template -> {args.output}")
    if markdown_output is not None:
        print(f"Wrote experiment execution markdown -> {markdown_output}")
    print(f"Planned runs: {len(planned_runs)} (top_k requested={top_k})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
