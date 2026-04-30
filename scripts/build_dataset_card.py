#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = PROJECT_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from interact_morph.io_utils import dump_json, load_json

MORPHOLOGY_FIELDS = [
    "shell_thickness_mean_um",
    "shell_thickness_nonuniformity",
    "crown_index",
    "trapped_air_fraction",
    "encapsulated_volume_ul",
    "core_offset",
    "layer_sequence",
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate an INTERACT-Morph dataset card from canonical manifests (MVP-007/G1)."
    )
    parser.add_argument("--dataset-root", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path, help="Markdown dataset card path")
    parser.add_argument("--split", default=None, type=Path, help="Optional train/val/test split artifact")
    parser.add_argument("--json-output", default=None, type=Path, help="Optional machine-readable summary")
    parser.add_argument("--title", default="INTERACT-Morph Dataset Card")
    parser.add_argument("--max-gaps", default=12, type=int)
    return parser.parse_args()


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        if not line.strip():
            continue
        try:
            row = json.loads(line)
        except json.JSONDecodeError as exc:
            raise ValueError(f"Invalid JSONL at {path}:{line_number}: {exc}") from exc
        if isinstance(row, dict):
            rows.append(row)
    return rows


def safe_get(record: dict[str, Any], path: str) -> Any:
    value: Any = record
    for part in path.split("."):
        if not isinstance(value, dict):
            return None
        value = value.get(part)
    return value


def load_run_metadata(dataset_root: Path, row: dict[str, Any]) -> dict[str, Any]:
    run_relpath = row.get("run_relpath")
    if not isinstance(run_relpath, str) or not run_relpath:
        return {}
    metadata_path = dataset_root / run_relpath / "metadata.json"
    if not metadata_path.exists():
        return {}
    loaded = load_json(metadata_path)
    return loaded if isinstance(loaded, dict) else {}


def count_values(values: list[Any]) -> dict[str, int]:
    counter = Counter(str(value) for value in values if value is not None and str(value) != "")
    return dict(sorted(counter.items()))


def summarize_quality(rows: list[dict[str, Any]]) -> dict[str, Any]:
    expected_flags = ["video_complete", "annotation_complete", "sensors_calibrated"]
    counts: dict[str, dict[str, int]] = {}
    for flag in expected_flags:
        true_count = 0
        false_count = 0
        missing_count = 0
        for row in rows:
            value = safe_get(row, f"quality_flags.{flag}")
            if value is True:
                true_count += 1
            elif value is False:
                false_count += 1
            else:
                missing_count += 1
        counts[flag] = {"true": true_count, "false": false_count, "missing": missing_count}
    return counts


def summarize_morphology_coverage(
    rows: list[dict[str, Any]],
    metadata_by_run_id: dict[str, dict[str, Any]],
) -> dict[str, dict[str, int]]:
    coverage: dict[str, dict[str, int]] = {}
    for field in MORPHOLOGY_FIELDS:
        present = 0
        missing = 0
        for row in rows:
            run_id = str(row.get("run_id", ""))
            metadata = metadata_by_run_id.get(run_id, {})
            value = safe_get(metadata, f"outcomes.{field}")
            if value is None:
                missing += 1
            else:
                present += 1
        coverage[field] = {"present": present, "missing": missing}
    return coverage


def summarize_split(split_path: Path | None) -> dict[str, Any] | None:
    if split_path is None:
        return None
    split = load_json(split_path)
    if not isinstance(split, dict):
        return {"path": str(split_path), "error": "split artifact is not a JSON object"}
    return {
        "path": str(split_path),
        "split_name": split.get("split_name"),
        "seed": split.get("seed"),
        "group_by": split.get("group_by"),
        "counts": split.get("counts", {}),
        "group_counts": {
            name: len(values) for name, values in (split.get("groups", {}) or {}).items() if isinstance(values, list)
        },
    }


def build_gap_list(
    rows: list[dict[str, Any]],
    metadata_by_run_id: dict[str, dict[str, Any]],
    max_gaps: int,
) -> list[dict[str, Any]]:
    gaps: list[dict[str, Any]] = []
    for row in rows:
        run_id = str(row.get("run_id", ""))
        metadata = metadata_by_run_id.get(run_id, {})
        run_gaps: list[str] = []
        if not metadata:
            run_gaps.append("metadata_json_missing")
        for field in MORPHOLOGY_FIELDS:
            if safe_get(metadata, f"outcomes.{field}") is None:
                run_gaps.append(f"missing_outcome:{field}")
        for path in ("control_parameters.route_type", "control_parameters.confinement_type"):
            if safe_get(metadata, path) is None:
                run_gaps.append(f"missing_{path}")
        if run_gaps:
            gaps.append({"run_id": run_id, "gaps": run_gaps[:8]})
        if len(gaps) >= max_gaps:
            break
    return gaps


def build_dataset_card(
    dataset_root: Path,
    split_path: Path | None = None,
    title: str = "INTERACT-Morph Dataset Card",
    max_gaps: int = 12,
    generated_at_utc: str | None = None,
) -> tuple[dict[str, Any], str]:
    generated_at_utc = generated_at_utc or datetime.now(timezone.utc).isoformat()
    manifest_path = dataset_root / "manifests" / "dataset_manifest.json"
    run_index_path = dataset_root / "manifests" / "runs_index.jsonl"
    if not manifest_path.exists():
        raise FileNotFoundError(f"Missing dataset manifest: {manifest_path}")
    if not run_index_path.exists():
        raise FileNotFoundError(f"Missing run index: {run_index_path}")

    manifest = load_json(manifest_path)
    rows = load_jsonl(run_index_path)
    metadata_by_run_id = {
        str(row.get("run_id", "")): load_run_metadata(dataset_root, row) for row in rows
    }

    route_types = []
    confinement_types = []
    for row in rows:
        metadata = metadata_by_run_id.get(str(row.get("run_id", "")), {})
        route_types.append(safe_get(metadata, "control_parameters.route_type"))
        confinement_types.append(safe_get(metadata, "control_parameters.confinement_type"))

    summary = {
        "title": title,
        "generated_at_utc": generated_at_utc,
        "dataset_root": str(dataset_root),
        "manifest": manifest,
        "run_count": len(rows),
        "families": count_values([row.get("family") for row in rows]),
        "fluid_combination_count": len(
            {row.get("fluid_combination_id") for row in rows if row.get("fluid_combination_id")}
        ),
        "regime_distribution": count_values([row.get("regime_label") for row in rows]),
        "encapsulation_success_distribution": count_values(
            [row.get("encapsulation_success") for row in rows]
        ),
        "route_type_distribution": count_values(route_types),
        "confinement_type_distribution": count_values(confinement_types),
        "quality_flags": summarize_quality(rows),
        "morphology_coverage": summarize_morphology_coverage(rows, metadata_by_run_id),
        "split": summarize_split(split_path),
        "known_gaps_sample": build_gap_list(rows, metadata_by_run_id, max_gaps=max_gaps),
    }

    markdown = render_markdown(summary)
    return summary, markdown


def render_counter_table(counter: dict[str, int], empty_label: str = "No values found.") -> list[str]:
    if not counter:
        return [empty_label]
    lines = ["| Value | Count |", "|---|---:|"]
    for value, count in counter.items():
        lines.append(f"| `{value}` | {count} |")
    return lines


def render_markdown(summary: dict[str, Any]) -> str:
    manifest = summary.get("manifest", {})
    lines = [
        f"# {summary['title']}",
        "",
        f"- Generated at UTC: `{summary['generated_at_utc']}`",
        f"- Dataset root: `{summary['dataset_root']}`",
        f"- Family: `{manifest.get('family', 'unknown')}`",
        f"- Run count: `{summary['run_count']}`",
        f"- Fluid combinations: `{summary['fluid_combination_count']}`",
        f"- Run ID mode: `{manifest.get('run_id_mode', 'unknown')}`",
        f"- Source directory: `{manifest.get('source_dir', 'unknown')}`",
        "",
        "## Scope And Intended Use",
        "",
        "This dataset card summarizes canonical INTERACT-Morph runs for morphology-first inverse design. It is intended to support dataset review, split traceability, baseline/model training, recommendation guardrails, and MVP go/no-go evidence.",
        "",
        "## Distributions",
        "",
        "### Regime Labels",
        "",
        *render_counter_table(summary.get("regime_distribution", {})),
        "",
        "### Encapsulation Success",
        "",
        *render_counter_table(summary.get("encapsulation_success_distribution", {})),
        "",
        "### Route Types",
        "",
        *render_counter_table(summary.get("route_type_distribution", {})),
        "",
        "### Confinement Types",
        "",
        *render_counter_table(summary.get("confinement_type_distribution", {})),
        "",
        "## Morphology Label Coverage",
        "",
        "| Field | Present | Missing |",
        "|---|---:|---:|",
    ]
    for field, counts in summary.get("morphology_coverage", {}).items():
        lines.append(f"| `{field}` | {counts.get('present', 0)} | {counts.get('missing', 0)} |")

    lines.extend(["", "## Quality Flags", "", "| Flag | True | False | Missing |", "|---|---:|---:|---:|"])
    for flag, counts in summary.get("quality_flags", {}).items():
        lines.append(
            f"| `{flag}` | {counts.get('true', 0)} | {counts.get('false', 0)} | {counts.get('missing', 0)} |"
        )

    split = summary.get("split")
    lines.extend(["", "## Split Traceability", ""])
    if split is None:
        lines.append("No split artifact was provided.")
    else:
        lines.extend(
            [
                f"- Split artifact: `{split.get('path')}`",
                f"- Split name: `{split.get('split_name', 'unknown')}`",
                f"- Seed: `{split.get('seed', 'unknown')}`",
                f"- Group by: `{split.get('group_by', 'unknown')}`",
                "",
                "| Split | Runs | Groups |",
                "|---|---:|---:|",
            ]
        )
        counts = split.get("counts", {}) if isinstance(split.get("counts"), dict) else {}
        group_counts = split.get("group_counts", {}) if isinstance(split.get("group_counts"), dict) else {}
        for name in sorted(counts):
            lines.append(f"| `{name}` | {counts.get(name, 0)} | {group_counts.get(name, 0)} |")

    lines.extend(["", "## Known Gaps Sample", ""])
    gaps = summary.get("known_gaps_sample", [])
    if not gaps:
        lines.append("No missing coverage gaps detected in the sampled rows.")
    else:
        lines.extend(["| Run ID | Gaps |", "|---|---|"])
        for gap in gaps:
            gap_text = ", ".join(f"`{item}`" for item in gap.get("gaps", []))
            lines.append(f"| `{gap.get('run_id', '')}` | {gap_text} |")

    lines.extend(
        [
            "",
            "## Production Readiness Notes",
            "",
            "- Synthetic or smoke-only datasets should not be used to close G1-G3 acceptance gates.",
            "- Production acceptance requires real experimental videos, morphology labels, route/confinement metadata, split artifacts, and baseline/model evidence generated from this dataset version.",
            "",
        ]
    )
    return "\n".join(lines)


def main() -> int:
    args = parse_args()
    try:
        summary, markdown = build_dataset_card(
            dataset_root=args.dataset_root,
            split_path=args.split,
            title=args.title,
            max_gaps=args.max_gaps,
        )
    except Exception as exc:  # noqa: BLE001
        print(f"Failed to build dataset card: {exc}")
        return 1

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(markdown, encoding="utf-8")
    print(f"Wrote dataset card -> {args.output}")
    if args.json_output is not None:
        dump_json(args.json_output, summary)
        print(f"Wrote dataset card JSON -> {args.json_output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
