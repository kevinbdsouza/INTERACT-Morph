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
            "Prepare structured prospective-campaign plans and append-ready log templates "
            "for primary and robustness validation arms (MVP-032/033)."
        )
    )
    parser.add_argument("--runs-input", required=True, type=Path, help="Input recommendations/template JSON")
    parser.add_argument("--config", required=True, type=Path, help="Campaign-prep config JSON/YAML")
    parser.add_argument(
        "--analysis-config",
        required=True,
        type=Path,
        help="Campaign analysis target config JSON/YAML (MVP-034 config)",
    )
    parser.add_argument(
        "--campaign-profile",
        required=True,
        help="Profile key from config.profiles (e.g., model_guided_primary)",
    )
    parser.add_argument("--output", required=True, type=Path, help="Output campaign plan JSON")
    parser.add_argument(
        "--campaign-log-output",
        default=None,
        type=Path,
        help="Optional JSONL output for append-ready campaign run log",
    )
    parser.add_argument("--markdown-output", default=None, type=Path, help="Optional markdown plan summary")
    parser.add_argument("--max-runs", default=None, type=int, help="Optional max-runs override")
    return parser.parse_args()


def safe_get(payload: Any, path: str) -> Any:
    current = payload
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


def normalize_rows(payload: Any) -> list[dict[str, Any]]:
    if isinstance(payload, dict):
        if isinstance(payload.get("planned_runs"), list):
            rows = payload.get("planned_runs", [])
        elif isinstance(payload.get("recommendations"), list):
            rows = payload.get("recommendations", [])
        elif isinstance(payload.get("runs"), list):
            rows = payload.get("runs", [])
        else:
            rows = []
    elif isinstance(payload, list):
        rows = payload
    else:
        rows = []

    return [row for row in rows if isinstance(row, dict)]


def matches_filter(row: dict[str, Any], rule: dict[str, Any]) -> bool:
    path = str(rule.get("path", "")).strip()
    if not path:
        return True

    value = safe_get(row, path)
    if value is None:
        return bool(rule.get("allow_missing", False))

    equals = rule.get("equals")
    if equals is not None and value != equals:
        return False

    in_values = rule.get("in")
    if isinstance(in_values, list) and value not in in_values:
        return False

    min_value = to_float(rule.get("min"))
    if min_value is not None:
        numeric = to_float(value)
        if numeric is None or numeric < min_value:
            return False

    max_value = to_float(rule.get("max"))
    if max_value is not None:
        numeric = to_float(value)
        if numeric is None or numeric > max_value:
            return False

    return True


def apply_filters(rows: list[dict[str, Any]], rules: list[dict[str, Any]]) -> list[dict[str, Any]]:
    if not rules:
        return rows

    filtered: list[dict[str, Any]] = []
    for row in rows:
        if all(matches_filter(row, rule) for rule in rules):
            filtered.append(row)
    return filtered


def pick_evenly_spaced(rows: list[dict[str, Any]], count: int) -> list[dict[str, Any]]:
    if count <= 0 or not rows:
        return []
    if count >= len(rows):
        return rows
    if count == 1:
        return [rows[0]]

    last_index = len(rows) - 1
    selected_indices: list[int] = []
    for idx in range(count):
        position = int(round(idx * last_index / (count - 1)))
        if position not in selected_indices:
            selected_indices.append(position)
    return [rows[idx] for idx in selected_indices]


def select_rows(rows: list[dict[str, Any]], strategy: str, count: int) -> list[dict[str, Any]]:
    ranked_rows = sorted(rows, key=lambda row: int(row.get("rank", 10**9)))
    if strategy == "ranked_top_k":
        return ranked_rows[:count]
    if strategy == "reverse_rank_top_k":
        ranked_rows.reverse()
        return ranked_rows[:count]
    if strategy == "evenly_spaced_rank":
        return pick_evenly_spaced(ranked_rows, count)
    if strategy == "first_n":
        return rows[:count]
    raise ValueError(f"Unsupported selection strategy: {strategy}")


def format_float(value: float | None, digits: int) -> str:
    if value is None:
        return "N/A"
    text = f"{value:.{digits}f}"
    return text.rstrip("0").rstrip(".")


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        for row in rows:
            f.write(json.dumps(row, sort_keys=False) + "\n")


def main() -> int:
    args = parse_args()

    config = load_json_or_yaml(args.config)
    if not isinstance(config, dict):
        print(f"Config must be an object: {args.config}")
        return 1

    analysis_config = load_json_or_yaml(args.analysis_config)
    if not isinstance(analysis_config, dict):
        print(f"Analysis config must be an object: {args.analysis_config}")
        return 1

    profiles = config.get("profiles", {})
    if not isinstance(profiles, dict):
        print("Config field 'profiles' must be an object")
        return 1

    if args.campaign_profile not in profiles:
        available = ", ".join(sorted(profiles.keys())) or "<none>"
        print(f"Unknown --campaign-profile '{args.campaign_profile}'. Available: {available}")
        return 1

    profile = profiles[args.campaign_profile]
    if not isinstance(profile, dict):
        print(f"Profile '{args.campaign_profile}' must be an object")
        return 1

    runs_payload = load_json(args.runs_input)
    rows = normalize_rows(runs_payload)
    if not rows:
        print(f"No run rows found in --runs-input: {args.runs_input}")
        return 1

    default_max_runs = int(profile.get("default_max_runs", 12))
    max_runs = args.max_runs if args.max_runs is not None else default_max_runs
    if max_runs <= 0:
        print("--max-runs must be positive")
        return 1

    filters = profile.get("holdout_filters", [])
    if not isinstance(filters, list):
        filters = []
    filter_rules = [rule for rule in filters if isinstance(rule, dict)]

    filtered_rows = apply_filters(rows, filter_rules)
    if not filtered_rows:
        print("No rows matched configured filters. Nothing to plan.")
        return 1

    strategy = str(profile.get("selection_strategy", "ranked_top_k"))
    try:
        selected_rows = select_rows(filtered_rows, strategy=strategy, count=max_runs)
    except ValueError as exc:
        print(str(exc))
        return 1

    if not selected_rows:
        print("Selection yielded zero rows. Nothing to plan.")
        return 1

    id_prefix = str(profile.get("campaign_id_prefix", "C3_CAMPAIGN")).strip() or "C3_CAMPAIGN"
    run_id_prefix = str(profile.get("run_id_prefix", "A_EXP")).strip() or "A_EXP"
    arm = str(profile.get("arm", "unknown"))
    today = datetime.now(timezone.utc).strftime("%Y%m%d")
    campaign_id = f"{id_prefix}_{today}"
    created_at_utc = datetime.now(timezone.utc).isoformat()

    planned_runs: list[dict[str, Any]] = []
    log_rows: list[dict[str, Any]] = []

    for idx, row in enumerate(selected_rows, start=1):
        rank = int(row.get("rank", idx))
        candidate_id = str(
            row.get("candidate_id") or row.get("planned_run_id") or row.get("run_id") or f"CAND_{idx:03d}"
        )

        candidate_parameters = row.get("candidate_parameters")
        if not isinstance(candidate_parameters, dict):
            candidate_parameters = row.get("candidate")
        if not isinstance(candidate_parameters, dict):
            candidate_parameters = {}

        predicted_success = to_float(safe_get(row, "predicted_success_probability"))
        if predicted_success is None:
            predicted_success = to_float(safe_get(row, "predictions.success_probability.calibrated_probability"))

        predicted_regime = row.get("predicted_regime")
        if not isinstance(predicted_regime, str):
            candidate_regime = safe_get(row, "predictions.regime_label")
            predicted_regime = candidate_regime if isinstance(candidate_regime, str) else None

        geometry = row.get("predicted_geometry")
        if not isinstance(geometry, dict):
            geometry = safe_get(row, "predictions.regression")
        if not isinstance(geometry, dict):
            geometry = {}

        planned_run_id = f"{run_id_prefix}_{idx:03d}"

        planned_row = {
            "plan_index": idx,
            "rank": rank,
            "planned_run_id": planned_run_id,
            "candidate_id": candidate_id,
            "ranking_score": to_float(row.get("ranking_score")),
            "predicted_success_probability": predicted_success,
            "predicted_regime": predicted_regime,
            "predicted_geometry": geometry,
            "candidate_parameters": candidate_parameters,
            "execution_status": "planned",
            "operator_notes": "",
        }
        planned_runs.append(planned_row)

        log_rows.append(
            {
                "run_id": planned_run_id,
                "campaign_id": campaign_id,
                "campaign_profile": args.campaign_profile,
                "arm": arm,
                "source_candidate_id": candidate_id,
                "status": "planned",
                "completed": False,
                "encapsulation_success": None,
                "regime_label": None,
                "shell_thickness_mean_um": None,
                "capsule_eccentricity": None,
                "operator_notes": "",
                "candidate_parameters": candidate_parameters,
            }
        )

    targets = analysis_config.get("targets", {})
    if not isinstance(targets, dict):
        targets = {}

    acceptance = analysis_config.get("acceptance", {})
    if not isinstance(acceptance, dict):
        acceptance = {}

    report = {
        "name": str(config.get("name", "family_a_prospective_campaign_v1")),
        "task_id": str(profile.get("task_id", "MVP-032")),
        "task_ids": config.get("tasks", ["MVP-032", "MVP-033"]),
        "created_at_utc": created_at_utc,
        "campaign_id": campaign_id,
        "campaign_profile": args.campaign_profile,
        "campaign_arm": arm,
        "description": str(profile.get("description", "")),
        "source_runs_input": str(args.runs_input),
        "selection": {
            "strategy": strategy,
            "source_rows": len(rows),
            "rows_after_filters": len(filtered_rows),
            "selected_rows": len(planned_runs),
            "requested_max_runs": max_runs,
            "holdout_filters": filter_rules,
        },
        "acceptance_targets": {
            "targets": targets,
            "acceptance": acceptance,
        },
        "planned_runs": planned_runs,
        "log_template": {
            "campaign_log_output": str(args.campaign_log_output) if args.campaign_log_output is not None else None,
            "required_fields": [
                "run_id",
                "status",
                "completed",
                "encapsulation_success",
                "regime_label",
                "shell_thickness_mean_um",
                "capsule_eccentricity",
            ],
        },
    }
    dump_json(args.output, report)

    if args.campaign_log_output is not None:
        write_jsonl(args.campaign_log_output, log_rows)

    if args.markdown_output is not None:
        lines: list[str] = []
        lines.append("# Prospective Campaign Plan")
        lines.append("")
        lines.append(f"- Task: `{report['task_id']}`")
        lines.append(f"- Profile: `{args.campaign_profile}`")
        lines.append(f"- Campaign ID: `{campaign_id}`")
        lines.append(f"- Generated: `{created_at_utc}`")
        lines.append(f"- Runs input: `{args.runs_input}`")
        if args.campaign_log_output is not None:
            lines.append(f"- Campaign log template: `{args.campaign_log_output}`")
        lines.append("")
        lines.append("## Selection Summary")
        lines.append("")
        lines.append(f"- Strategy: `{strategy}`")
        lines.append(f"- Source rows: `{len(rows)}`")
        lines.append(f"- Rows after filters: `{len(filtered_rows)}`")
        lines.append(f"- Selected rows: `{len(planned_runs)}`")
        lines.append("")
        lines.append("## Planned Runs")
        lines.append("")
        lines.append("| Plan Index | Planned Run ID | Candidate ID | Predicted Success | Predicted Regime |")
        lines.append("|---:|---|---|---:|---|")
        for row in planned_runs:
            lines.append(
                f"| {row['plan_index']} | {row['planned_run_id']} | {row['candidate_id']} | "
                f"{format_float(to_float(row.get('predicted_success_probability')), 3)} | "
                f"{row.get('predicted_regime') or 'N/A'} |"
            )
        lines.append("")
        lines.append("## Acceptance Targets")
        lines.append("")
        lines.append(f"- Targets source: `{args.analysis_config}`")
        min_reduction = to_float(acceptance.get("minimum_reduction_percent"))
        if min_reduction is not None:
            lines.append(f"- Reduction target vs baseline: `{format_float(min_reduction, 1)}%`")
        if isinstance(targets.get("allowed_regimes"), list):
            regimes = ", ".join(str(item) for item in targets["allowed_regimes"])
            lines.append(f"- Allowed regimes: `{regimes}`")

        args.markdown_output.parent.mkdir(parents=True, exist_ok=True)
        args.markdown_output.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")

    print(f"Wrote campaign plan: {args.output}")
    if args.campaign_log_output is not None:
        print(f"Wrote campaign log template: {args.campaign_log_output}")
    if args.markdown_output is not None:
        print(f"Wrote markdown summary: {args.markdown_output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
