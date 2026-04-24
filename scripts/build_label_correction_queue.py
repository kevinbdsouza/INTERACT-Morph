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
            "Build a prioritized active correction queue (MVP-014) by merging segmentation QC, "
            "trajectory feature QA, and contour extraction failures."
        )
    )
    parser.add_argument("--segmentation-qc", required=True, type=Path, help="Segmentation QC artifact JSON")
    parser.add_argument("--feature-qa", required=True, type=Path, help="Feature QA report JSON")
    parser.add_argument("--extraction-report", default=None, type=Path, help="Optional contour extraction report JSON")
    parser.add_argument("--config", required=True, type=Path, help="Correction-loop config JSON/YAML")
    parser.add_argument("--output", required=True, type=Path, help="Queue JSON output path")
    parser.add_argument("--markdown-output", default=None, type=Path, help="Optional markdown summary output")
    parser.add_argument("--max-runs", default=None, type=int, help="Optional maximum queue rows to emit")
    return parser.parse_args()


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


def normalize_run_id(raw: Any) -> str | None:
    if isinstance(raw, str) and raw.strip():
        return raw.strip()
    return None


def add_reason(
    per_run: dict[str, dict[str, Any]],
    run_id: str,
    source: str,
    code: str,
    score: float,
    evidence: dict[str, Any] | None = None,
) -> None:
    state = per_run.setdefault(
        run_id,
        {
            "run_id": run_id,
            "score": 0.0,
            "reasons": [],
            "issue_counts": Counter(),
            "source_counts": Counter(),
        },
    )

    state["score"] += max(0.0, float(score))
    state["reasons"].append(
        {
            "source": source,
            "code": code,
            "score": float(score),
            "evidence": evidence or {},
        }
    )
    state["issue_counts"][code] += 1
    state["source_counts"][source] += 1


def priority_label(score: float, bands: dict[str, float]) -> str:
    critical = float(bands.get("critical", 70.0))
    high = float(bands.get("high", 40.0))
    medium = float(bands.get("medium", 20.0))
    if score >= critical:
        return "critical"
    if score >= high:
        return "high"
    if score >= medium:
        return "medium"
    return "low"


def recommended_actions(reasons: list[dict[str, Any]]) -> list[str]:
    actions: list[str] = []

    def add(action: str) -> None:
        if action not in actions:
            actions.append(action)

    for reason in reasons:
        code = str(reason.get("code", ""))
        source = str(reason.get("source", ""))

        if source == "segmentation" and ("low_iou" in code or "low_f1" in code or "flagged" in code):
            add("Review and relabel representative interface mask/pixel samples for this run.")
            add("Retrain segmentation model and compare per-run IoU/F1 deltas before accepting updates.")
        if source == "feature_qa" and code.startswith("missing_event:"):
            add("Backfill event timestamps in labels.json and rerun contour-to-trajectory extraction.")
        if source == "feature_qa" and (
            code.startswith("summary_mismatch:")
            or code.startswith("abrupt_jump:")
            or code.startswith("nan_series:")
            or code.startswith("non_monotonic_time:")
        ):
            add("Inspect contour traces for frame alignment/noise issues and regenerate derived features.")
        if source == "feature_qa" and code.startswith("missing_summary:"):
            add("Regenerate derived_features.json and verify summary fields against trajectory aggregates.")
        if source == "extraction" and code.startswith("extraction_failed"):
            add("Fix contour-observation schema/values for this run and rerun extraction pipeline.")

    if not actions:
        add("Manual triage required; issue type did not match predefined correction playbooks.")
    return actions


def main() -> int:
    args = parse_args()

    config = load_json_or_yaml(args.config)
    if not isinstance(config, dict):
        print(f"Config must be an object: {args.config}")
        return 1

    segmentation_qc = load_json(args.segmentation_qc)
    feature_qa = load_json(args.feature_qa)
    extraction_report = load_json(args.extraction_report) if args.extraction_report is not None else None

    scoring = config.get("scoring", {})
    if not isinstance(scoring, dict):
        scoring = {}

    score_seg_flagged = float(scoring.get("segmentation_flagged_run", 30.0))
    score_seg_iou = float(scoring.get("segmentation_low_iou", 20.0))
    score_seg_f1 = float(scoring.get("segmentation_low_f1", 20.0))
    score_feature_issue = float(scoring.get("feature_issue", 8.0))
    score_extraction_failure = float(scoring.get("extraction_failure", 25.0))

    thresholds = config.get("thresholds", {})
    if not isinstance(thresholds, dict):
        thresholds = {}

    iou_warn = to_float(thresholds.get("iou_warn"))
    f1_warn = to_float(thresholds.get("f1_warn"))

    quality_thresholds = segmentation_qc.get("quality_thresholds", {})
    if not isinstance(quality_thresholds, dict):
        quality_thresholds = {}

    if iou_warn is None:
        iou_warn = to_float(quality_thresholds.get("min_iou_warn"))
    if f1_warn is None:
        f1_warn = to_float(quality_thresholds.get("min_f1_warn"))
    if iou_warn is None:
        iou_warn = 0.65
    if f1_warn is None:
        f1_warn = 0.75

    output_cfg = config.get("output", {})
    if not isinstance(output_cfg, dict):
        output_cfg = {}
    max_queue_size = int(output_cfg.get("max_queue_size", 200))
    max_reasons = int(output_cfg.get("max_reasons_per_run", 20))
    max_actions = int(output_cfg.get("max_actions_per_run", 4))

    per_run: dict[str, dict[str, Any]] = {}

    flagged_runs = segmentation_qc.get("flagged_runs", [])
    if isinstance(flagged_runs, list):
        for item in flagged_runs:
            run_id = normalize_run_id(item)
            if run_id is None and isinstance(item, dict):
                run_id = normalize_run_id(item.get("run_id"))
            if run_id is None:
                continue
            add_reason(
                per_run,
                run_id,
                source="segmentation",
                code="flagged_run",
                score=score_seg_flagged,
                evidence={"flagged_entry": item},
            )

    worst_runs = segmentation_qc.get("worst_runs_by_iou", [])
    if isinstance(worst_runs, list):
        for row in worst_runs:
            if not isinstance(row, dict):
                continue
            run_id = normalize_run_id(row.get("run_id"))
            if run_id is None:
                continue
            iou = to_float(row.get("iou"))
            f1 = to_float(row.get("f1"))

            if iou is not None and iou < iou_warn:
                add_reason(
                    per_run,
                    run_id,
                    source="segmentation",
                    code="low_iou",
                    score=score_seg_iou,
                    evidence={"iou": iou, "threshold": iou_warn},
                )
            if f1 is not None and f1 < f1_warn:
                add_reason(
                    per_run,
                    run_id,
                    source="segmentation",
                    code="low_f1",
                    score=score_seg_f1,
                    evidence={"f1": f1, "threshold": f1_warn},
                )

    qa_runs = feature_qa.get("worst_runs", [])
    if isinstance(qa_runs, list):
        for row in qa_runs:
            if not isinstance(row, dict):
                continue
            run_id = normalize_run_id(row.get("run_id"))
            if run_id is None:
                continue
            issues = row.get("issues", [])
            if not isinstance(issues, list):
                continue
            for issue in issues:
                if not isinstance(issue, str) or not issue.strip():
                    continue
                add_reason(
                    per_run,
                    run_id,
                    source="feature_qa",
                    code=issue.strip(),
                    score=score_feature_issue,
                    evidence={"issue_count": row.get("issue_count")},
                )

    if isinstance(extraction_report, dict):
        failures = extraction_report.get("failures", [])
        if isinstance(failures, list):
            for failure in failures:
                if not isinstance(failure, dict):
                    continue
                run_id = normalize_run_id(failure.get("run_id"))
                if run_id is None:
                    continue
                reason = str(failure.get("reason", "unknown"))
                add_reason(
                    per_run,
                    run_id,
                    source="extraction",
                    code=f"extraction_failed:{reason}",
                    score=score_extraction_failure,
                    evidence=failure,
                )

    bands = config.get("priority_bands", {})
    if not isinstance(bands, dict):
        bands = {}

    queue_items: list[dict[str, Any]] = []
    issue_counts: Counter[str] = Counter()
    source_counts: Counter[str] = Counter()

    for run_id, state in per_run.items():
        reasons = sorted(
            state["reasons"],
            key=lambda item: (-float(item.get("score", 0.0)), str(item.get("source", "")), str(item.get("code", ""))),
        )
        if max_reasons >= 0:
            reasons = reasons[:max_reasons]

        for reason in reasons:
            issue_counts[str(reason.get("code", "unknown"))] += 1
            source_counts[str(reason.get("source", "unknown"))] += 1

        actions = recommended_actions(reasons)
        if max_actions >= 0:
            actions = actions[:max_actions]

        score = float(state["score"])
        queue_items.append(
            {
                "run_id": run_id,
                "priority": priority_label(score, bands),
                "score": round(score, 6),
                "reasons": reasons,
                "recommended_actions": actions,
                "status": "pending",
            }
        )

    priority_order = {"critical": 0, "high": 1, "medium": 2, "low": 3}
    queue_items.sort(
        key=lambda item: (
            priority_order.get(str(item.get("priority", "low")), 99),
            -float(item.get("score", 0.0)),
            str(item.get("run_id", "")),
        )
    )

    run_limit = max_queue_size
    if args.max_runs is not None:
        run_limit = min(run_limit, max(0, int(args.max_runs)))
    queue_items = queue_items[:run_limit]

    summary_priority_counts = dict(Counter(str(item.get("priority", "low")) for item in queue_items))

    report = {
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "task_id": "MVP-014",
        "config": str(args.config),
        "inputs": {
            "segmentation_qc": str(args.segmentation_qc),
            "feature_qa": str(args.feature_qa),
            "extraction_report": str(args.extraction_report) if args.extraction_report is not None else None,
        },
        "thresholds": {
            "iou_warn": iou_warn,
            "f1_warn": f1_warn,
        },
        "queue_size": len(queue_items),
        "priority_counts": summary_priority_counts,
        "source_counts": dict(source_counts),
        "issue_counts": dict(issue_counts),
        "queue": queue_items,
    }

    dump_json(args.output, report)

    if args.markdown_output is not None:
        lines: list[str] = []
        lines.append("# Label Correction Queue (MVP-014)")
        lines.append("")
        lines.append(f"- Generated: {report['created_at_utc']}")
        lines.append(f"- Queue size: {report['queue_size']}")
        lines.append("")
        lines.append("## Priority Counts")
        lines.append("")
        lines.append("| Priority | Count |")
        lines.append("|---|---:|")
        for priority in ["critical", "high", "medium", "low"]:
            lines.append(f"| {priority} | {summary_priority_counts.get(priority, 0)} |")
        lines.append("")
        lines.append("## Queue")
        lines.append("")
        lines.append("| Run ID | Priority | Score | Top Reasons | Recommended Actions |")
        lines.append("|---|---|---:|---|---|")
        for row in queue_items:
            reasons = ", ".join(str(reason.get("code", "")) for reason in row.get("reasons", [])[:3])
            actions = " ".join(str(action) for action in row.get("recommended_actions", [])[:2])
            lines.append(
                f"| {row.get('run_id')} | {row.get('priority')} | {row.get('score')} | {reasons} | {actions} |"
            )

        args.markdown_output.parent.mkdir(parents=True, exist_ok=True)
        args.markdown_output.write_text("\n".join(lines) + "\n", encoding="utf-8")

    print(f"Wrote label correction queue -> {args.output}")
    if args.markdown_output is not None:
        print(f"Wrote label correction markdown -> {args.markdown_output}")
    print(f"Queue size: {report['queue_size']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
