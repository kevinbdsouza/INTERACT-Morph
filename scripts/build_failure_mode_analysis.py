#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = PROJECT_ROOT / "src"
import sys

if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from interact_capsules.io_utils import dump_json, load_json_or_yaml


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Build failure-mode taxonomy report from model prediction artifacts "
            "(MVP-035)."
        )
    )
    parser.add_argument("--predictions", required=True, type=Path, help="Prediction JSONL from model training/fine-tuning")
    parser.add_argument("--config", required=True, type=Path, help="Failure analysis config JSON/YAML")
    parser.add_argument("--output", required=True, type=Path, help="Failure analysis report JSON")
    parser.add_argument("--markdown-output", default=None, type=Path, help="Optional markdown report output")
    parser.add_argument("--max-runs", default=None, type=int, help="Optional max worst-runs cap override")
    return parser.parse_args()


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


def to_bool(value: Any) -> bool | None:
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        return bool(value)
    if isinstance(value, str):
        text = value.strip().lower()
        if text in {"1", "true", "yes", "y"}:
            return True
        if text in {"0", "false", "no", "n"}:
            return False
    return None


def load_jsonl(path: Path) -> list[dict[str, Any]]:
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


def fmt(value: float | None, digits: int = 3) -> str:
    if value is None:
        return "N/A"
    text = f"{value:.{digits}f}"
    return text.rstrip("0").rstrip(".")


def main() -> int:
    args = parse_args()
    config = load_json_or_yaml(args.config)
    if not isinstance(config, dict):
        print(f"Config must be an object: {args.config}")
        return 1

    threshold_cfg = config.get("regression_abs_error_thresholds", {})
    if not isinstance(threshold_cfg, dict):
        threshold_cfg = {}
    confidence_cfg = config.get("confidence", {})
    if not isinstance(confidence_cfg, dict):
        confidence_cfg = {}
    scoring_cfg = config.get("scoring", {})
    if not isinstance(scoring_cfg, dict):
        scoring_cfg = {}
    output_cfg = config.get("output", {})
    if not isinstance(output_cfg, dict):
        output_cfg = {}

    score_success = to_float(scoring_cfg.get("success_misclassification")) or 4.0
    score_regime = to_float(scoring_cfg.get("regime_misclassification")) or 3.0
    score_regression = to_float(scoring_cfg.get("regression_error")) or 2.0
    score_margin = to_float(scoring_cfg.get("low_margin")) or 1.0
    success_margin_warn = to_float(confidence_cfg.get("success_margin_warn")) or 1.0
    regime_margin_warn = to_float(confidence_cfg.get("regime_margin_warn")) or 1.0

    max_worst_runs = args.max_runs if args.max_runs is not None else int(output_cfg.get("max_worst_runs", 40))
    if max_worst_runs <= 0:
        print("--max-runs must be positive")
        return 1

    rows = load_jsonl(args.predictions)

    issue_counts: Counter[str] = Counter()
    split_issue_counts: dict[str, Counter[str]] = defaultdict(Counter)
    failure_by_regime: Counter[str] = Counter()
    failure_rows: list[dict[str, Any]] = []

    for row in rows:
        run_id = str(row.get("run_id", "unknown"))
        split = str(row.get("split", "unknown"))
        success_true = to_bool(row.get("success_true"))
        success_pred = to_bool(row.get("success_pred"))
        regime_true = row.get("regime_true")
        regime_pred = row.get("regime_pred")
        if not isinstance(regime_true, str):
            regime_true = None
        if not isinstance(regime_pred, str):
            regime_pred = None

        reasons: list[dict[str, Any]] = []
        severity = 0.0

        if success_true is not None and success_pred is not None and success_true != success_pred:
            reasons.append({"code": "success_misclassification", "true": success_true, "pred": success_pred})
            severity += score_success
            issue_counts["success_misclassification"] += 1
            split_issue_counts[split]["success_misclassification"] += 1

        if regime_true is not None and regime_pred is not None and regime_true != regime_pred:
            reasons.append({"code": "regime_misclassification", "true": regime_true, "pred": regime_pred})
            severity += score_regime
            issue_counts["regime_misclassification"] += 1
            split_issue_counts[split]["regime_misclassification"] += 1

        success_margin = to_float(row.get("success_margin"))
        if success_margin is not None and success_margin < success_margin_warn:
            reasons.append(
                {
                    "code": "low_success_margin",
                    "value": success_margin,
                    "threshold": success_margin_warn,
                }
            )
            severity += score_margin
            issue_counts["low_success_margin"] += 1
            split_issue_counts[split]["low_success_margin"] += 1

        regime_margin = to_float(row.get("regime_margin"))
        if regime_margin is not None and regime_margin < regime_margin_warn:
            reasons.append(
                {
                    "code": "low_regime_margin",
                    "value": regime_margin,
                    "threshold": regime_margin_warn,
                }
            )
            severity += score_margin
            issue_counts["low_regime_margin"] += 1
            split_issue_counts[split]["low_regime_margin"] += 1

        regression_true = row.get("regression_true", {})
        regression_pred = row.get("regression_pred", {})
        if not isinstance(regression_true, dict):
            regression_true = {}
        if not isinstance(regression_pred, dict):
            regression_pred = {}

        for target_name, threshold_raw in threshold_cfg.items():
            threshold = to_float(threshold_raw)
            if threshold is None:
                continue
            true_value = to_float(regression_true.get(target_name))
            pred_value = to_float(regression_pred.get(target_name))
            if true_value is None or pred_value is None:
                continue
            abs_error = abs(pred_value - true_value)
            if abs_error > threshold:
                code = f"high_abs_error:{target_name}"
                reasons.append(
                    {
                        "code": code,
                        "absolute_error": abs_error,
                        "threshold": threshold,
                        "true": true_value,
                        "pred": pred_value,
                    }
                )
                severity += score_regression
                issue_counts[code] += 1
                split_issue_counts[split][code] += 1

        if reasons:
            if regime_true is not None:
                failure_by_regime[regime_true] += 1
            failure_rows.append(
                {
                    "run_id": run_id,
                    "split": split,
                    "severity_score": severity,
                    "reason_count": len(reasons),
                    "reasons": reasons,
                    "success_true": success_true,
                    "success_pred": success_pred,
                    "regime_true": regime_true,
                    "regime_pred": regime_pred,
                    "success_margin": success_margin,
                    "regime_margin": regime_margin,
                }
            )

    failure_rows.sort(key=lambda r: (-float(r["severity_score"]), str(r["run_id"])))
    worst_runs = failure_rows[:max_worst_runs]

    recommendations: list[str] = []
    if issue_counts.get("success_misclassification", 0) > 0:
        recommendations.append("Audit class balance and threshold calibration for encapsulation-success prediction head.")
    if issue_counts.get("regime_misclassification", 0) > 0:
        recommendations.append("Review regime-label boundary definitions and hard-negative examples for frequent confusions.")
    if any(key.startswith("high_abs_error:shell_thickness_mean_um") for key in issue_counts):
        recommendations.append("Prioritize shell-thickness feature quality checks and retrain with updated regression weighting.")
    if any(key.startswith("high_abs_error:capsule_eccentricity") for key in issue_counts):
        recommendations.append("Inspect eccentricity extraction consistency and normalize camera/viewpoint variance.")
    if issue_counts.get("low_success_margin", 0) > 0 or issue_counts.get("low_regime_margin", 0) > 0:
        recommendations.append("Review low-margin runs for label ambiguity; feed them into active correction and fine-tuning.")
    if not recommendations:
        recommendations.append("No major failure clusters detected; proceed to prospective validation with periodic monitoring.")

    split_breakdown = {
        split: dict(counter)
        for split, counter in sorted(split_issue_counts.items(), key=lambda item: item[0])
    }
    runs_scanned = len(rows)
    runs_with_failures = len(failure_rows)

    report = {
        "task_id": "MVP-035",
        "name": str(config.get("name", "family_a_failure_mode_analysis_v1")),
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "inputs": {
            "predictions": str(args.predictions),
            "config": str(args.config),
        },
        "summary": {
            "runs_scanned": runs_scanned,
            "runs_with_failures": runs_with_failures,
            "failure_rate": (runs_with_failures / runs_scanned) if runs_scanned else None,
            "issue_counts": dict(issue_counts),
            "failures_by_true_regime": dict(failure_by_regime),
            "split_breakdown": split_breakdown,
        },
        "thresholds": {
            "regression_abs_error_thresholds": threshold_cfg,
            "confidence": {
                "success_margin_warn": success_margin_warn,
                "regime_margin_warn": regime_margin_warn,
            },
        },
        "worst_runs": worst_runs,
        "recommended_actions": recommendations,
    }
    dump_json(args.output, report)

    if args.markdown_output is not None:
        lines: list[str] = []
        lines.append("# Failure-Mode Analysis (MVP-035)")
        lines.append("")
        lines.append(f"- Generated: `{report['created_at_utc']}`")
        lines.append(f"- Predictions: `{args.predictions}`")
        lines.append(f"- Runs scanned: `{runs_scanned}`")
        lines.append(f"- Runs with failures: `{runs_with_failures}`")
        lines.append("")
        lines.append("## Failure Taxonomy")
        lines.append("")
        lines.append("| Failure Code | Count |")
        lines.append("|---|---:|")
        if issue_counts:
            for code, count in sorted(issue_counts.items(), key=lambda item: (-item[1], item[0])):
                lines.append(f"| {code} | {count} |")
        else:
            lines.append("| none | 0 |")
        lines.append("")
        lines.append("## Highest-Severity Runs")
        lines.append("")
        lines.append("| Run ID | Split | Severity | Reasons |")
        lines.append("|---|---|---:|---|")
        for row in worst_runs[: min(15, len(worst_runs))]:
            reason_codes = ", ".join(reason["code"] for reason in row.get("reasons", []))
            lines.append(
                f"| {row['run_id']} | {row['split']} | {fmt(to_float(row['severity_score']), 2)} | {reason_codes} |"
            )
        lines.append("")
        lines.append("## Recommended Actions")
        lines.append("")
        for action in recommendations:
            lines.append(f"- {action}")
        args.markdown_output.parent.mkdir(parents=True, exist_ok=True)
        args.markdown_output.write_text("\n".join(lines) + "\n", encoding="utf-8")

    print(f"Wrote failure-mode analysis -> {args.output}")
    if args.markdown_output is not None:
        print(f"Wrote failure-mode analysis markdown -> {args.markdown_output}")
    print(f"Runs scanned: {runs_scanned} | runs with failures: {runs_with_failures}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
