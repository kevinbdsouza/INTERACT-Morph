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

from interact_capsules.io_utils import dump_json, load_json_or_yaml


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Build internal handoff template, MVP go/no-go memo, and post-MVP roadmap "
            "draft from tracker state (MVP-038/039/040)."
        )
    )
    parser.add_argument("--progress-tracker", required=True, type=Path, help="Path to Progress_Tracking.md")
    parser.add_argument("--todo", required=True, type=Path, help="Path to ToDo.md")
    parser.add_argument("--config", required=True, type=Path, help="Governance config JSON/YAML")
    parser.add_argument("--output-dir", required=True, type=Path, help="Output directory for generated pack")
    parser.add_argument("--prefix", default="family_a_mvp", help="File prefix for generated outputs")
    return parser.parse_args()


def read_lines(path: Path) -> list[str]:
    return path.read_text(encoding="utf-8").splitlines()


def parse_markdown_table(lines: list[str], section_header: str) -> list[list[str]]:
    in_section = False
    rows: list[list[str]] = []

    for line in lines:
        if line.startswith("## ") and in_section and not line.startswith(section_header):
            break
        if line.startswith(section_header):
            in_section = True
            continue
        if not in_section:
            continue

        text = line.strip()
        if not text.startswith("|"):
            if rows:
                break
            continue

        parts = [part.strip() for part in text.strip("|").split("|")]
        if not parts:
            continue

        if all(token in {"-", ":", ""} for token in "".join(parts)):
            continue
        rows.append(parts)

    if len(rows) <= 1:
        return []
    return rows[1:]


def parse_todo_task_map(lines: list[str]) -> dict[str, str]:
    mapping: dict[str, str] = {}
    in_backlog = False
    for line in lines:
        if line.startswith("## 3) Detailed Implementation Backlog"):
            in_backlog = True
            continue
        if line.startswith("## ") and in_backlog:
            break
        if not in_backlog:
            continue

        text = line.strip()
        if not text.startswith("| MVP-"):
            continue

        parts = [part.strip() for part in text.strip("|").split("|")]
        if len(parts) < 3:
            continue
        task_id = parts[0]
        task_name = parts[2]
        if task_id:
            mapping[task_id] = task_name
    return mapping


def resolve_artifact_path(path_value: str) -> Path:
    path = Path(path_value)
    if path.is_absolute():
        return path
    return PROJECT_ROOT / path


def summarize_evidence_payload(payload: Any) -> dict[str, Any]:
    if not isinstance(payload, dict):
        return {}

    summary: dict[str, Any] = {}
    for key in (
        "name",
        "created_at_utc",
        "passed",
        "ready",
        "run_count",
        "ready_run_count",
        "error_count",
        "warning_count",
    ):
        if key in payload:
            summary[key] = payload[key]

    recommendation = payload.get("run_id_mode_recommendation")
    if isinstance(recommendation, dict) and recommendation.get("recommended"):
        summary["recommended_run_id_mode"] = recommendation.get("recommended")

    issue_counts = payload.get("issue_counts")
    if isinstance(issue_counts, dict) and issue_counts:
        summary["issue_counts"] = issue_counts

    next_actions = payload.get("next_actions")
    if isinstance(next_actions, list):
        summary["next_action_count"] = len(next_actions)
        summary["next_actions"] = [
            {
                "priority": action.get("priority"),
                "type": action.get("type"),
            }
            for action in next_actions[:3]
            if isinstance(action, dict)
        ]

    checks = payload.get("checks")
    if isinstance(checks, list):
        failed = [
            str(check.get("name", "unknown"))
            for check in checks
            if isinstance(check, dict) and not bool(check.get("passed"))
        ]
        summary["check_count"] = len(checks)
        summary["failed_checks"] = failed

    return summary


def build_evidence_snapshot(config: dict[str, Any]) -> list[dict[str, Any]]:
    handoff_cfg = config.get("handoff", {})
    if not isinstance(handoff_cfg, dict):
        return []

    evidence_cfg = handoff_cfg.get("evidence_artifacts", [])
    if not isinstance(evidence_cfg, list):
        return []

    snapshot: list[dict[str, Any]] = []
    for item in evidence_cfg:
        if not isinstance(item, dict):
            continue
        label = str(item.get("label", "Evidence artifact"))
        configured_path = str(item.get("path", "")).strip()
        if not configured_path:
            continue

        resolved_path = resolve_artifact_path(configured_path)
        entry: dict[str, Any] = {
            "label": label,
            "path": configured_path,
            "exists": resolved_path.exists(),
            "summary": {},
        }
        if resolved_path.exists() and resolved_path.suffix.lower() == ".json":
            try:
                entry["summary"] = summarize_evidence_payload(load_json_or_yaml(resolved_path))
            except Exception as exc:
                entry["summary"] = {"read_error": str(exc)}
        snapshot.append(entry)

    return snapshot


def build_handoff_payload(
    *,
    config: dict[str, Any],
    generated_at_utc: str,
    task_rows: list[dict[str, Any]],
    todo_task_map: dict[str, str],
) -> dict[str, Any]:
    handoff_cfg = config.get("handoff", {})
    if not isinstance(handoff_cfg, dict):
        handoff_cfg = {}

    in_progress = [row for row in task_rows if row.get("status") == "In Progress"]
    in_progress.sort(key=lambda row: str(row.get("task_id", "")))
    max_items = int(handoff_cfg.get("max_in_progress_items", 10))

    selected_tasks: list[dict[str, Any]] = []
    for row in in_progress[:max_items]:
        task_id = str(row.get("task_id", ""))
        selected_tasks.append(
            {
                "task_id": task_id,
                "task_name": todo_task_map.get(task_id, ""),
                "owner": row.get("owner"),
                "status": row.get("status"),
                "due_date": row.get("due_date"),
                "notes": row.get("notes"),
            }
        )

    required_artifacts = handoff_cfg.get("required_artifacts", [])
    if not isinstance(required_artifacts, list):
        required_artifacts = []

    agenda = handoff_cfg.get("agenda", [])
    if not isinstance(agenda, list):
        agenda = []

    checklist = handoff_cfg.get("checklist", [])
    if not isinstance(checklist, list):
        checklist = []

    evidence_snapshot = build_evidence_snapshot(config)

    return {
        "task_id": "MVP-038",
        "name": str(config.get("name", "family_a_mvp_governance_v1")),
        "created_at_utc": generated_at_utc,
        "session_title": str(handoff_cfg.get("session_title", "INTERACT-Capsules Internal Handoff")),
        "objective": str(
            handoff_cfg.get(
                "objective",
                "Run a complete internal walkthrough so lab operators can execute the workflow without developer intervention.",
            )
        ),
        "agenda": [str(item) for item in agenda],
        "required_artifacts": [str(item) for item in required_artifacts],
        "evidence_snapshot": evidence_snapshot,
        "checklist": [str(item) for item in checklist],
        "in_progress_tasks_snapshot": selected_tasks,
    }


def status_satisfies(actual: str, expected: Any) -> bool:
    if isinstance(expected, str):
        return actual == expected
    if isinstance(expected, list):
        return actual in [str(item) for item in expected]
    return False


def build_go_no_go_payload(
    *,
    config: dict[str, Any],
    generated_at_utc: str,
    milestone_rows: list[dict[str, Any]],
    task_rows: list[dict[str, Any]],
    blocker_rows: list[dict[str, Any]],
) -> dict[str, Any]:
    go_cfg = config.get("go_no_go", {})
    if not isinstance(go_cfg, dict):
        go_cfg = {}

    requirements = go_cfg.get("gate_requirements", {})
    if not isinstance(requirements, dict):
        requirements = {}

    milestone_status: dict[str, str] = {
        str(row.get("milestone", "")): str(row.get("status", ""))
        for row in milestone_rows
        if row.get("milestone")
    }

    gate_checks: list[dict[str, Any]] = []
    unmet_gates = 0
    for gate_name, expected in requirements.items():
        actual = milestone_status.get(str(gate_name), "Unknown")
        passed = status_satisfies(actual, expected)
        if not passed:
            unmet_gates += 1
        gate_checks.append(
            {
                "gate": str(gate_name),
                "expected": expected,
                "actual": actual,
                "passed": passed,
            }
        )

    blocked_count = sum(1 for row in task_rows if str(row.get("status", "")) == "Blocked")
    at_risk_count = sum(1 for row in task_rows if str(row.get("status", "")) == "At Risk")

    active_blockers = [row for row in blocker_rows if str(row.get("blocker", "")).strip()]
    max_blocked_tasks = int(go_cfg.get("max_blocked_tasks", 0))
    max_active_blockers = int(go_cfg.get("max_active_blockers", 0))
    max_at_risk_tasks = int(go_cfg.get("max_at_risk_tasks", 0))

    reasons: list[str] = []
    if unmet_gates > 0:
        reasons.append(f"{unmet_gates} required gate(s) not yet satisfied.")
    if blocked_count > max_blocked_tasks:
        reasons.append(
            f"Blocked tasks {blocked_count} exceeds configured maximum {max_blocked_tasks}."
        )
    if len(active_blockers) > max_active_blockers:
        reasons.append(
            f"Active blockers {len(active_blockers)} exceeds configured maximum {max_active_blockers}."
        )
    if at_risk_count > max_at_risk_tasks:
        reasons.append(f"At-risk tasks {at_risk_count} exceeds configured maximum {max_at_risk_tasks}.")

    decision = "GO" if not reasons else "NO_GO"

    return {
        "task_id": "MVP-039",
        "name": str(config.get("name", "family_a_mvp_governance_v1")),
        "created_at_utc": generated_at_utc,
        "decision": decision,
        "gate_checks": gate_checks,
        "risk_snapshot": {
            "blocked_tasks": blocked_count,
            "at_risk_tasks": at_risk_count,
            "active_blockers": len(active_blockers),
        },
        "decision_reasons": reasons,
    }


def build_roadmap_payload(
    *,
    config: dict[str, Any],
    generated_at_utc: str,
    go_no_go_payload: dict[str, Any],
    task_rows: list[dict[str, Any]],
    todo_task_map: dict[str, str],
) -> dict[str, Any]:
    roadmap_cfg = config.get("roadmap", {})
    if not isinstance(roadmap_cfg, dict):
        roadmap_cfg = {}

    decision = str(go_no_go_payload.get("decision", "NO_GO"))
    if decision == "GO":
        phase_seed = roadmap_cfg.get("phases_if_go", [])
    else:
        phase_seed = roadmap_cfg.get("phases_if_no_go", [])
    if not isinstance(phase_seed, list):
        phase_seed = []

    carryover = [row for row in task_rows if str(row.get("status", "")) != "Done"]
    carryover.sort(key=lambda row: str(row.get("task_id", "")))
    max_carryover = int(roadmap_cfg.get("max_carryover_tasks", 20))

    carryover_rows: list[dict[str, Any]] = []
    for row in carryover[:max_carryover]:
        task_id = str(row.get("task_id", ""))
        carryover_rows.append(
            {
                "task_id": task_id,
                "task_name": todo_task_map.get(task_id, ""),
                "status": row.get("status"),
                "due_date": row.get("due_date"),
            }
        )

    phases: list[dict[str, Any]] = []
    for phase in phase_seed:
        if not isinstance(phase, dict):
            continue
        phases.append(
            {
                "phase": str(phase.get("phase", "")),
                "objective": str(phase.get("objective", "")),
                "focus": [str(item) for item in phase.get("focus", []) if isinstance(item, (str, int, float))],
            }
        )

    return {
        "task_id": "MVP-040",
        "name": str(config.get("name", "family_a_mvp_governance_v1")),
        "created_at_utc": generated_at_utc,
        "decision_context": {
            "go_no_go_decision": decision,
            "decision_reasons": go_no_go_payload.get("decision_reasons", []),
        },
        "phases": phases,
        "carryover_tasks": carryover_rows,
    }


def to_milestone_rows(table_rows: list[list[str]]) -> list[dict[str, Any]]:
    parsed: list[dict[str, Any]] = []
    for cells in table_rows:
        if len(cells) < 5:
            continue
        parsed.append(
            {
                "milestone": cells[0],
                "target_date": cells[1],
                "status": cells[2],
                "acceptance": cells[3],
                "evidence": cells[4],
            }
        )
    return parsed


def to_task_rows(table_rows: list[list[str]]) -> list[dict[str, Any]]:
    parsed: list[dict[str, Any]] = []
    for cells in table_rows:
        if len(cells) < 6:
            continue
        parsed.append(
            {
                "task_id": cells[0],
                "owner": cells[1],
                "status": cells[2],
                "start_date": cells[3],
                "due_date": cells[4],
                "notes": cells[5],
            }
        )
    return parsed


def to_blocker_rows(table_rows: list[list[str]]) -> list[dict[str, Any]]:
    parsed: list[dict[str, Any]] = []
    for cells in table_rows:
        if len(cells) < 6:
            continue
        parsed.append(
            {
                "date": cells[0],
                "blocker": cells[1],
                "affected_tasks": cells[2],
                "owner": cells[3],
                "escalation_needed": cells[4],
                "resolution_eta": cells[5],
            }
        )
    return parsed


def write_markdown(path: Path, lines: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")


def main() -> int:
    args = parse_args()

    config = load_json_or_yaml(args.config)
    if not isinstance(config, dict):
        print(f"Config must be an object: {args.config}")
        return 1

    progress_lines = read_lines(args.progress_tracker)
    todo_lines = read_lines(args.todo)

    milestone_rows = to_milestone_rows(
        parse_markdown_table(progress_lines, "## 3) Milestone Status Board")
    )
    task_rows = to_task_rows(
        parse_markdown_table(progress_lines, "## 4) Task Progress (From ToDo.md)")
    )
    blocker_rows = to_blocker_rows(
        parse_markdown_table(progress_lines, "## 9) Blockers and Escalations")
    )

    if not milestone_rows:
        print("Could not parse milestone table from progress tracker.")
        return 1
    if not task_rows:
        print("Could not parse task progress table from progress tracker.")
        return 1

    todo_task_map = parse_todo_task_map(todo_lines)
    generated_at_utc = datetime.now(timezone.utc).isoformat()

    handoff = build_handoff_payload(
        config=config,
        generated_at_utc=generated_at_utc,
        task_rows=task_rows,
        todo_task_map=todo_task_map,
    )
    go_no_go = build_go_no_go_payload(
        config=config,
        generated_at_utc=generated_at_utc,
        milestone_rows=milestone_rows,
        task_rows=task_rows,
        blocker_rows=blocker_rows,
    )
    roadmap = build_roadmap_payload(
        config=config,
        generated_at_utc=generated_at_utc,
        go_no_go_payload=go_no_go,
        task_rows=task_rows,
        todo_task_map=todo_task_map,
    )

    output_dir = args.output_dir
    output_dir.mkdir(parents=True, exist_ok=True)

    handoff_json = output_dir / f"{args.prefix}.handoff.json"
    handoff_md = output_dir / f"{args.prefix}.handoff.md"
    go_json = output_dir / f"{args.prefix}.go_no_go.json"
    go_md = output_dir / f"{args.prefix}.go_no_go.md"
    roadmap_json = output_dir / f"{args.prefix}.roadmap.json"
    roadmap_md = output_dir / f"{args.prefix}.roadmap.md"

    dump_json(handoff_json, handoff)
    dump_json(go_json, go_no_go)
    dump_json(roadmap_json, roadmap)

    handoff_lines: list[str] = []
    handoff_lines.append("# Internal Handoff Session Pack (MVP-038)")
    handoff_lines.append("")
    handoff_lines.append(f"- Generated: `{handoff['created_at_utc']}`")
    handoff_lines.append(f"- Session title: `{handoff['session_title']}`")
    handoff_lines.append("")
    handoff_lines.append("## Objective")
    handoff_lines.append("")
    handoff_lines.append(str(handoff.get("objective", "")))
    handoff_lines.append("")
    handoff_lines.append("## Agenda")
    handoff_lines.append("")
    for item in handoff.get("agenda", []):
        handoff_lines.append(f"- {item}")
    handoff_lines.append("")
    handoff_lines.append("## Required Artifacts")
    handoff_lines.append("")
    for item in handoff.get("required_artifacts", []):
        handoff_lines.append(f"- [ ] {item}")
    handoff_lines.append("")
    handoff_lines.append("## Evidence Snapshot")
    handoff_lines.append("")
    evidence_snapshot = handoff.get("evidence_snapshot", [])
    if evidence_snapshot:
        handoff_lines.append("| Artifact | Path | Exists | Summary |")
        handoff_lines.append("|---|---|---|---|")
        for item in evidence_snapshot:
            summary = item.get("summary", {})
            summary_text = ", ".join(
                f"{key}={value}" for key, value in summary.items() if value not in (None, "", [])
            )
            handoff_lines.append(
                f"| {item.get('label', '')} | `{item.get('path', '')}` | {item.get('exists', False)} | {summary_text} |"
            )
    else:
        handoff_lines.append("- No evidence artifacts configured.")
    handoff_lines.append("")
    handoff_lines.append("## Checklist")
    handoff_lines.append("")
    for item in handoff.get("checklist", []):
        handoff_lines.append(f"- [ ] {item}")

    go_lines: list[str] = []
    go_lines.append("# MVP Go/No-Go Review (MVP-039)")
    go_lines.append("")
    go_lines.append(f"- Generated: `{go_no_go['created_at_utc']}`")
    go_lines.append(f"- Decision: `{go_no_go['decision']}`")
    go_lines.append("")
    go_lines.append("## Gate Checks")
    go_lines.append("")
    go_lines.append("| Gate | Expected | Actual | Passed |")
    go_lines.append("|---|---|---|---|")
    for check in go_no_go.get("gate_checks", []):
        go_lines.append(
            f"| {check.get('gate')} | {check.get('expected')} | {check.get('actual')} | {check.get('passed')} |"
        )
    go_lines.append("")
    go_lines.append("## Decision Reasons")
    go_lines.append("")
    reasons = go_no_go.get("decision_reasons", [])
    if reasons:
        for reason in reasons:
            go_lines.append(f"- {reason}")
    else:
        go_lines.append("- All configured checks passed.")

    roadmap_lines: list[str] = []
    roadmap_lines.append("# Post-MVP Roadmap Draft (MVP-040)")
    roadmap_lines.append("")
    roadmap_lines.append(f"- Generated: `{roadmap['created_at_utc']}`")
    roadmap_lines.append(
        f"- Decision context: `{roadmap.get('decision_context', {}).get('go_no_go_decision', 'NO_GO')}`"
    )
    roadmap_lines.append("")
    roadmap_lines.append("## Phases")
    roadmap_lines.append("")
    for phase in roadmap.get("phases", []):
        roadmap_lines.append(f"### {phase.get('phase', '')}")
        roadmap_lines.append("")
        roadmap_lines.append(str(phase.get("objective", "")))
        roadmap_lines.append("")
        focus = phase.get("focus", [])
        for item in focus:
            roadmap_lines.append(f"- {item}")
        roadmap_lines.append("")

    roadmap_lines.append("## Carryover Tasks")
    roadmap_lines.append("")
    roadmap_lines.append("| Task ID | Task | Status | Due Date |")
    roadmap_lines.append("|---|---|---|---|")
    for task in roadmap.get("carryover_tasks", []):
        roadmap_lines.append(
            f"| {task.get('task_id')} | {task.get('task_name', '')} | {task.get('status', '')} | {task.get('due_date', '')} |"
        )

    write_markdown(handoff_md, handoff_lines)
    write_markdown(go_md, go_lines)
    write_markdown(roadmap_md, roadmap_lines)

    print(f"Wrote handoff pack: {handoff_json} and {handoff_md}")
    print(f"Wrote go/no-go memo: {go_json} and {go_md}")
    print(f"Wrote roadmap draft: {roadmap_json} and {roadmap_md}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
