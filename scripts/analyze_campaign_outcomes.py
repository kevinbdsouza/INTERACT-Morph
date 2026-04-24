#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
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
            "Analyze model-guided vs baseline campaign outcomes and quantify "
            "experimental-load reduction (MVP-034)."
        )
    )
    parser.add_argument("--model-guided-log", required=True, type=Path, help="JSON/JSONL campaign log")
    parser.add_argument("--baseline-log", required=True, type=Path, help="JSON/JSONL campaign log")
    parser.add_argument("--config", required=True, type=Path, help="Campaign-analysis config JSON/YAML")
    parser.add_argument("--output", required=True, type=Path, help="Output analysis report JSON")
    parser.add_argument("--markdown-output", default=None, type=Path, help="Optional markdown report output")
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


def load_log_rows(path: Path) -> list[dict[str, Any]]:
    if path.suffix.lower() == ".jsonl":
        rows: list[dict[str, Any]] = []
        with path.open("r", encoding="utf-8") as f:
            for idx, line in enumerate(f, start=1):
                text = line.strip()
                if not text:
                    continue
                try:
                    payload = json.loads(text)
                except json.JSONDecodeError as exc:
                    raise ValueError(f"{path}:{idx}: invalid JSONL row ({exc})") from exc
                if not isinstance(payload, dict):
                    raise ValueError(f"{path}:{idx}: expected JSON object per row")
                rows.append(payload)
        return rows

    payload = load_json(path)
    if isinstance(payload, list):
        return [row for row in payload if isinstance(row, dict)]
    if isinstance(payload, dict):
        runs = payload.get("runs")
        if isinstance(runs, list):
            return [row for row in runs if isinstance(row, dict)]
    raise ValueError(f"Unsupported campaign log structure: {path}")


def read_outcome_value(row: dict[str, Any], *keys: str) -> Any:
    for key in keys:
        if key in row:
            return row[key]
    outcomes = row.get("outcomes")
    if isinstance(outcomes, dict):
        for key in keys:
            if key in outcomes:
                return outcomes[key]
    return None


def is_completed(row: dict[str, Any]) -> bool:
    status = row.get("status")
    if isinstance(status, str):
        normalized = status.strip().lower()
        if normalized in {"planned", "queued", "skipped", "cancelled", "canceled"}:
            return False
    completed = to_bool(row.get("completed"))
    if completed is not None:
        return completed
    return True


def is_target_hit(row: dict[str, Any], targets: dict[str, Any]) -> bool:
    require_success = bool(targets.get("require_success", True))
    allowed_regimes = targets.get("allowed_regimes")
    if not isinstance(allowed_regimes, list):
        allowed_regimes = []

    success = to_bool(read_outcome_value(row, "encapsulation_success", "success"))
    regime = read_outcome_value(row, "regime_label")
    thickness = to_float(read_outcome_value(row, "shell_thickness_mean_um"))
    eccentricity = to_float(read_outcome_value(row, "capsule_eccentricity"))

    if require_success and success is not True:
        return False

    thickness_target = targets.get("shell_thickness_mean_um", {})
    if not isinstance(thickness_target, dict):
        thickness_target = {}
    t_min = to_float(thickness_target.get("min"))
    t_max = to_float(thickness_target.get("max"))
    if t_min is not None and (thickness is None or thickness < t_min):
        return False
    if t_max is not None and (thickness is None or thickness > t_max):
        return False

    ecc_target = targets.get("capsule_eccentricity", {})
    if not isinstance(ecc_target, dict):
        ecc_target = {}
    e_max = to_float(ecc_target.get("max"))
    if e_max is not None and (eccentricity is None or eccentricity > e_max):
        return False

    if allowed_regimes:
        if not isinstance(regime, str) or regime not in allowed_regimes:
            return False

    return True


def summarize_campaign(rows: list[dict[str, Any]], targets: dict[str, Any]) -> dict[str, Any]:
    completed_rows = [row for row in rows if is_completed(row)]
    successes = 0
    target_hits = 0
    first_target_hit_index: int | None = None

    for idx, row in enumerate(completed_rows, start=1):
        success = to_bool(read_outcome_value(row, "encapsulation_success", "success"))
        if success is True:
            successes += 1
        if is_target_hit(row, targets):
            target_hits += 1
            if first_target_hit_index is None:
                first_target_hit_index = idx

    completed_count = len(completed_rows)
    return {
        "total_rows": len(rows),
        "completed_runs": completed_count,
        "success_count": successes,
        "success_rate": (successes / completed_count) if completed_count else None,
        "target_hit_count": target_hits,
        "target_hit_rate": (target_hits / completed_count) if completed_count else None,
        "runs_to_first_target_hit": first_target_hit_index,
    }


def fmt_pct(value: float | None) -> str:
    if value is None:
        return "N/A"
    return f"{100.0 * value:.1f}%"


def main() -> int:
    args = parse_args()
    config = load_json_or_yaml(args.config)
    if not isinstance(config, dict):
        print(f"Config must be an object: {args.config}")
        return 1

    targets = config.get("targets", {})
    if not isinstance(targets, dict):
        targets = {}

    acceptance = config.get("acceptance", {})
    if not isinstance(acceptance, dict):
        acceptance = {}
    target_reduction_pct = to_float(acceptance.get("minimum_reduction_percent"))
    if target_reduction_pct is None:
        target_reduction_pct = 30.0

    guided_rows = load_log_rows(args.model_guided_log)
    baseline_rows = load_log_rows(args.baseline_log)

    guided_summary = summarize_campaign(guided_rows, targets)
    baseline_summary = summarize_campaign(baseline_rows, targets)

    guided_runs_to_hit = guided_summary["runs_to_first_target_hit"]
    baseline_runs_to_hit = baseline_summary["runs_to_first_target_hit"]

    reduction_absolute: int | None = None
    reduction_percent: float | None = None
    if isinstance(guided_runs_to_hit, int) and isinstance(baseline_runs_to_hit, int) and baseline_runs_to_hit > 0:
        reduction_absolute = baseline_runs_to_hit - guided_runs_to_hit
        reduction_percent = 100.0 * (reduction_absolute / baseline_runs_to_hit)

    report = {
        "task_id": "MVP-034",
        "name": str(config.get("name", "family_a_campaign_analysis_v1")),
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "inputs": {
            "model_guided_log": str(args.model_guided_log),
            "baseline_log": str(args.baseline_log),
            "config": str(args.config),
        },
        "targets": targets,
        "campaigns": {
            "model_guided": guided_summary,
            "baseline": baseline_summary,
        },
        "comparison": {
            "runs_to_first_target_hit": {
                "model_guided": guided_runs_to_hit,
                "baseline": baseline_runs_to_hit,
            },
            "experiment_reduction": {
                "absolute_runs": reduction_absolute,
                "percent": reduction_percent,
                "target_percent": target_reduction_pct,
                "meets_target": (reduction_percent is not None and reduction_percent >= target_reduction_pct),
            },
        },
    }
    dump_json(args.output, report)

    if args.markdown_output is not None:
        lines: list[str] = []
        lines.append("# Prospective Campaign Analysis (MVP-034)")
        lines.append("")
        lines.append(f"- Generated: `{report['created_at_utc']}`")
        lines.append(f"- Model-guided log: `{args.model_guided_log}`")
        lines.append(f"- Baseline log: `{args.baseline_log}`")
        lines.append("")
        lines.append("## Campaign Summary")
        lines.append("")
        lines.append("| Campaign | Completed Runs | Success Rate | Target Hit Rate | Runs To First Target Hit |")
        lines.append("|---|---:|---:|---:|---:|")
        lines.append(
            f"| Model-guided | {guided_summary['completed_runs']} | "
            f"{fmt_pct(guided_summary['success_rate'])} | {fmt_pct(guided_summary['target_hit_rate'])} | "
            f"{guided_summary['runs_to_first_target_hit'] if guided_summary['runs_to_first_target_hit'] is not None else 'N/A'} |"
        )
        lines.append(
            f"| Baseline | {baseline_summary['completed_runs']} | "
            f"{fmt_pct(baseline_summary['success_rate'])} | {fmt_pct(baseline_summary['target_hit_rate'])} | "
            f"{baseline_summary['runs_to_first_target_hit'] if baseline_summary['runs_to_first_target_hit'] is not None else 'N/A'} |"
        )
        lines.append("")
        lines.append("## Experiment Reduction")
        lines.append("")
        if reduction_percent is None:
            lines.append("- Reduction could not be computed because one or both campaigns never reached the target window.")
        else:
            lines.append(f"- Reduction vs baseline: `{reduction_percent:.1f}%` ({reduction_absolute} fewer runs to first hit)")
            lines.append(f"- Target threshold: `{target_reduction_pct:.1f}%`")
            meets = report["comparison"]["experiment_reduction"]["meets_target"]
            lines.append(f"- Meets target: `{'yes' if meets else 'no'}`")
        args.markdown_output.parent.mkdir(parents=True, exist_ok=True)
        args.markdown_output.write_text("\n".join(lines) + "\n", encoding="utf-8")

    print(f"Wrote campaign analysis -> {args.output}")
    if args.markdown_output is not None:
        print(f"Wrote campaign analysis markdown -> {args.markdown_output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
