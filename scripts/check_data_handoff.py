#!/usr/bin/env python3
from __future__ import annotations

import argparse
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
import shlex
import sys
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = PROJECT_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from interact_morph.io_utils import dump_json, load_json_or_yaml
from interact_morph.run_id_utils import (
    canonicalize_run_id,
    ensure_unique_run_id,
    extract_source_run_id,
    is_canonical_run_id,
)
from interact_morph.schema_utils import validate_with_schema


DEFAULT_OUTPUT = (
    PROJECT_ROOT / "data" / "canonical" / "family_a" / "manifests" / "reports" / "data_handoff_check.json"
)
DEFAULT_SCHEMA = PROJECT_ROOT / "schemas" / "run_metadata.schema.json"
DEFAULT_PRODUCTION_DATASET_ROOT = PROJECT_ROOT / "data" / "canonical" / "family_a"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Check whether a raw Family A handoff is ready for inventory/ingest/pipeline "
            "execution (MVP-004/005/006)."
        )
    )
    parser.add_argument("--source-dir", required=True, type=Path)
    parser.add_argument("--output", default=DEFAULT_OUTPUT, type=Path)
    parser.add_argument("--schema", default=DEFAULT_SCHEMA, type=Path)
    parser.add_argument("--family", default="A", choices=["A", "B", "C"])
    parser.add_argument(
        "--require-labels",
        action="store_true",
        help="Require labels.json in each run directory before reporting ready=true.",
    )
    parser.add_argument(
        "--require-derived",
        action="store_true",
        help="Require derived_features.json in each run directory before reporting ready=true.",
    )
    return parser.parse_args()


def find_metadata_file(run_dir: Path) -> Path | None:
    for name in ("metadata.json", "metadata.yaml", "metadata.yml"):
        path = run_dir / name
        if path.exists():
            return path
    return None


def find_video_file(run_dir: Path) -> Path | None:
    for ext in ("*.mp4", "*.mov", "*.avi", "*.mkv"):
        hits = sorted(run_dir.glob(ext))
        if hits:
            return hits[0]
    return None


def iter_run_dirs(source_dir: Path) -> list[Path]:
    if not source_dir.exists() or not source_dir.is_dir():
        return []
    return [path for path in sorted(source_dir.iterdir()) if path.is_dir()]


def projected_metadata_for_ingest(
    metadata: dict[str, Any],
    run_dir: Path,
    family: str,
    run_id_mode: str,
    used_run_ids: set[str],
    video_path: Path | None,
) -> tuple[dict[str, Any] | None, list[str], dict[str, Any]]:
    issues: list[str] = []
    source_run_id = extract_source_run_id(metadata, run_dir.name)
    details: dict[str, Any] = {
        "source_run_id": source_run_id,
        "projected_run_id": None,
        "collision_resolved": False,
    }

    if run_id_mode == "canonicalize":
        candidate = canonicalize_run_id(
            family=family,
            source_run_id=source_run_id,
            run_dir_name=run_dir.name,
        )
        run_id, collision = ensure_unique_run_id(
            candidate=candidate,
            used_ids=used_run_ids,
            disambiguator=str(run_dir.resolve()),
        )
        details["projected_run_id"] = run_id
        details["collision_resolved"] = collision
    else:
        run_id = str(metadata.get("run_id", "")).strip()
        if not run_id:
            issues.append("preserve_mode_missing_run_id")
        elif run_id in used_run_ids:
            issues.append("preserve_mode_duplicate_run_id")
        else:
            used_run_ids.add(run_id)
        details["projected_run_id"] = run_id or None

    projected = dict(metadata)
    projected["source_run_id"] = source_run_id
    projected["run_id"] = str(details["projected_run_id"] or "")
    projected["family"] = family

    asset_paths = projected.get("asset_paths")
    if not isinstance(asset_paths, dict):
        asset_paths = {}
    else:
        asset_paths = dict(asset_paths)
    if video_path is not None:
        asset_paths["video_relpath"] = video_path.name
    if (run_dir / "labels.json").exists():
        asset_paths["labels_relpath"] = "labels.json"
    if (run_dir / "derived_features.json").exists():
        asset_paths["derived_features_relpath"] = "derived_features.json"
    projected["asset_paths"] = asset_paths

    return projected, issues, details


def check_run(
    run_dir: Path,
    schema_path: Path,
    family: str,
    canonical_used_ids: set[str],
    preserve_used_ids: set[str],
    require_labels: bool,
    require_derived: bool,
) -> dict[str, Any]:
    metadata_path = find_metadata_file(run_dir)
    video_path = find_video_file(run_dir)
    labels_path = run_dir / "labels.json"
    derived_path = run_dir / "derived_features.json"

    errors: list[str] = []
    warnings: list[str] = []
    metadata: dict[str, Any] = {}
    preserve_issues: list[str] = []
    canonical_details: dict[str, Any] = {}
    preserve_details: dict[str, Any] = {}

    if metadata_path is None:
        errors.append("missing_metadata")
    else:
        try:
            loaded = load_json_or_yaml(metadata_path)
            if not isinstance(loaded, dict):
                errors.append("metadata_root_not_object")
            else:
                metadata = loaded
        except Exception as exc:  # noqa: BLE001
            errors.append(f"metadata_parse_error:{exc.__class__.__name__}")

    if video_path is None:
        errors.append("missing_video")
    if require_labels and not labels_path.exists():
        errors.append("missing_labels")
    elif not labels_path.exists():
        warnings.append("labels_missing")
    if require_derived and not derived_path.exists():
        errors.append("missing_derived_features")
    elif not derived_path.exists():
        warnings.append("derived_features_missing")

    if metadata:
        metadata_family = str(metadata.get("family", "")).strip().upper()
        if metadata_family and metadata_family != family:
            errors.append(f"family_mismatch:{metadata_family}")
        elif not metadata_family:
            errors.append("family_missing")

        canonical_projected, canonical_mode_issues, canonical_details = projected_metadata_for_ingest(
            metadata=metadata,
            run_dir=run_dir,
            family=family,
            run_id_mode="canonicalize",
            used_run_ids=canonical_used_ids,
            video_path=video_path,
        )
        preserve_projected, preserve_issues, preserve_details = projected_metadata_for_ingest(
            metadata=metadata,
            run_dir=run_dir,
            family=family,
            run_id_mode="preserve",
            used_run_ids=preserve_used_ids,
            video_path=video_path,
        )
        errors.extend(canonical_mode_issues)
        if canonical_projected is not None:
            schema_errors = validate_with_schema(canonical_projected, schema_path)
            errors.extend(f"schema:{err}" for err in schema_errors)
        if preserve_projected is not None:
            if preserve_details["projected_run_id"] and not is_canonical_run_id(
                str(preserve_details["projected_run_id"]),
                family=family,
            ):
                preserve_issues.append("preserve_mode_noncanonical_run_id")

    return {
        "run_dir": str(run_dir),
        "metadata_file": str(metadata_path) if metadata_path else None,
        "video_file": str(video_path) if video_path else None,
        "has_labels": labels_path.exists(),
        "has_derived_features": derived_path.exists(),
        "canonicalize": canonical_details,
        "preserve": {
            **preserve_details,
            "issues": preserve_issues,
        },
        "warnings": warnings,
        "errors": errors,
        "ready": not errors,
    }


def recommend_run_id_mode(run_reports: list[dict[str, Any]]) -> dict[str, Any]:
    preserve_issue_counts = Counter(
        issue
        for report in run_reports
        for issue in report.get("preserve", {}).get("issues", [])
    )
    canonical_collisions = sum(
        1 for report in run_reports if report.get("canonicalize", {}).get("collision_resolved")
    )

    if preserve_issue_counts:
        return {
            "recommended": "canonicalize",
            "reason": "Preserve mode would carry missing, duplicate, or noncanonical run IDs.",
            "preserve_issue_counts": dict(sorted(preserve_issue_counts.items())),
            "canonical_collision_count": canonical_collisions,
        }

    return {
        "recommended": "preserve",
        "reason": "All metadata run IDs are present, unique, and canonical for the requested family.",
        "preserve_issue_counts": {},
        "canonical_collision_count": canonical_collisions,
    }


def collect_issue_examples(
    run_reports: list[dict[str, Any]],
    *,
    max_issues: int = 8,
    max_examples_per_issue: int = 3,
) -> dict[str, list[str]]:
    examples: dict[str, list[str]] = {}
    for report in run_reports:
        run_dir = str(report.get("run_dir", ""))
        for issue in report.get("errors", []):
            issue_key = str(issue).split(":", 1)[0]
            if issue_key not in examples:
                if len(examples) >= max_issues:
                    continue
                examples[issue_key] = []
            if run_dir and len(examples[issue_key]) < max_examples_per_issue:
                examples[issue_key].append(run_dir)
    return examples


def format_command(parts: list[str | Path]) -> str:
    return " ".join(shlex.quote(str(part)) for part in parts)


def build_next_actions(
    *,
    source_dir: Path,
    ready: bool,
    top_level_errors: list[str],
    issue_counts: Counter[str],
    warning_counts: Counter[str],
    run_id_recommendation: dict[str, Any] | None,
    require_labels: bool,
    require_derived: bool,
) -> list[dict[str, Any]]:
    actions: list[dict[str, Any]] = []

    if top_level_errors:
        actions.append(
            {
                "priority": "P0",
                "type": "fix_source_directory",
                "description": "Resolve top-level handoff source issues before running inventory or ingest.",
                "details": top_level_errors,
            }
        )
        return actions

    if not ready:
        actions.append(
            {
                "priority": "P0",
                "type": "fix_blocking_run_issues",
                "description": "Fix blocking metadata/video/schema issues in the raw handoff, then rerun handoff-check.",
                "issue_counts": dict(sorted(issue_counts.items())),
            }
        )
        actions.append(
            {
                "priority": "P0",
                "type": "rerun_handoff_check",
                "description": "Rerun the non-mutating readiness check after source fixes.",
                "command": format_command(
                    [
                        "interact-morph",
                        "handoff-check",
                        "--source-dir",
                        source_dir,
                        "--output",
                        "data/canonical/family_a/manifests/reports/data_handoff_check.json",
                    ]
                ),
            }
        )
    else:
        mode = "canonicalize"
        if run_id_recommendation and run_id_recommendation.get("recommended"):
            mode = str(run_id_recommendation["recommended"])
        pipeline_command_parts: list[str | Path] = [
            "interact-morph",
            "pipeline",
            "--source-dir",
            source_dir,
            "--dataset-root",
            DEFAULT_PRODUCTION_DATASET_ROOT.relative_to(PROJECT_ROOT),
            "--run-id-mode",
            mode,
        ]
        if require_labels:
            pipeline_command_parts.append("--require-labels")
        if require_derived:
            pipeline_command_parts.append("--require-derived")
        actions.append(
            {
                "priority": "P0",
                "type": "run_pipeline",
                "description": "Run the first canonical pipeline using the recommended run-ID mode.",
                "command": format_command(pipeline_command_parts),
            }
        )
        actions.append(
            {
                "priority": "P1",
                "type": "attach_governance_evidence",
                "description": "Attach the handoff report and generated pipeline artifacts to the governance evidence list before operator review.",
            }
        )

    if warning_counts:
        actions.append(
            {
                "priority": "P1",
                "type": "review_warnings",
                "description": "Review non-blocking warnings before closing data QA acceptance.",
                "warning_counts": dict(sorted(warning_counts.items())),
            }
        )

    return actions


def build_report(args: argparse.Namespace) -> tuple[dict[str, Any], int]:
    source_dir = args.source_dir
    top_level_errors: list[str] = []
    run_dirs = iter_run_dirs(source_dir)

    if not source_dir.exists():
        top_level_errors.append("source_dir_missing")
    elif not source_dir.is_dir():
        top_level_errors.append("source_path_not_directory")
    elif not run_dirs:
        top_level_errors.append("no_run_directories_found")

    canonical_used_ids: set[str] = set()
    preserve_used_ids: set[str] = set()
    run_reports = [
        check_run(
            run_dir=run_dir,
            schema_path=args.schema,
            family=args.family,
            canonical_used_ids=canonical_used_ids,
            preserve_used_ids=preserve_used_ids,
            require_labels=args.require_labels,
            require_derived=args.require_derived,
        )
        for run_dir in run_dirs
    ]

    issue_counts = Counter(
        issue.split(":", 1)[0]
        for report in run_reports
        for issue in report["errors"]
    )
    warning_counts = Counter(
        warning.split(":", 1)[0]
        for report in run_reports
        for warning in report["warnings"]
    )
    ready = not top_level_errors and all(report["ready"] for report in run_reports)
    run_id_recommendation = recommend_run_id_mode(run_reports) if run_reports else None
    issue_examples = collect_issue_examples(run_reports)
    next_actions = build_next_actions(
        source_dir=source_dir,
        ready=ready,
        top_level_errors=top_level_errors,
        issue_counts=issue_counts,
        warning_counts=warning_counts,
        run_id_recommendation=run_id_recommendation,
        require_labels=args.require_labels,
        require_derived=args.require_derived,
    )

    report = {
        "name": "family_a_data_handoff_check",
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "source_dir": str(source_dir),
        "family": args.family,
        "schema": str(args.schema),
        "require_labels": bool(args.require_labels),
        "require_derived": bool(args.require_derived),
        "run_count": len(run_reports),
        "ready_run_count": sum(1 for report in run_reports if report["ready"]),
        "error_count": sum(len(report["errors"]) for report in run_reports) + len(top_level_errors),
        "warning_count": sum(len(report["warnings"]) for report in run_reports),
        "ready": ready,
        "top_level_errors": top_level_errors,
        "issue_counts": dict(sorted(issue_counts.items())),
        "warning_counts": dict(sorted(warning_counts.items())),
        "issue_examples": issue_examples,
        "run_id_mode_recommendation": run_id_recommendation,
        "next_actions": next_actions,
        "runs": run_reports,
    }
    return report, 0 if ready else 1


def main() -> int:
    args = parse_args()
    report, return_code = build_report(args)
    dump_json(args.output, report)

    status = "READY" if report["ready"] else "NOT_READY"
    print(f"{status}: {report['ready_run_count']}/{report['run_count']} run directories ready")
    print(f"Wrote handoff check report -> {args.output}")
    recommendation = report.get("run_id_mode_recommendation")
    if recommendation:
        print(f"Recommended run-id mode: {recommendation['recommended']}")
    if report["issue_counts"]:
        print(f"Issue counts: {report['issue_counts']}")
    next_actions = report.get("next_actions", [])
    if next_actions:
        print("Next actions:")
        for action in next_actions[:3]:
            print(f"- [{action.get('priority')}] {action.get('description')}")
            if action.get("command"):
                print(f"  {action['command']}")
    return return_code


if __name__ == "__main__":
    raise SystemExit(main())
