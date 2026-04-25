from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path
from typing import Sequence

PROJECT_ROOT = Path(__file__).resolve().parents[2]
SCRIPTS_DIR = PROJECT_ROOT / "scripts"

DEFAULT_RUN_SCHEMA = PROJECT_ROOT / "schemas" / "run_metadata.schema.json"
DEFAULT_FEATURES_SCHEMA = PROJECT_ROOT / "schemas" / "derived_features.schema.json"
DEFAULT_SPLIT_CONFIG = PROJECT_ROOT / "configs" / "splits" / "family_a_split.json"
DEFAULT_BASELINE_CONFIG = PROJECT_ROOT / "configs" / "baselines" / "family_a_heuristic.json"
DEFAULT_SWEEP_CONFIG = PROJECT_ROOT / "configs" / "simulations" / "family_a_axisymmetric_doe.json"
DEFAULT_SURROGATE_CONFIG = PROJECT_ROOT / "configs" / "simulations" / "family_a_axisymmetric_surrogate.json"
DEFAULT_MODEL_CONFIG = PROJECT_ROOT / "configs" / "modeling" / "family_a_multimodal_v1.json"
DEFAULT_FINETUNE_CONFIG = PROJECT_ROOT / "configs" / "modeling" / "family_a_multimodal_v1_finetune.json"
DEFAULT_CALIBRATION_CONFIG = (
    PROJECT_ROOT / "configs" / "modeling" / "family_a_uncertainty_calibration_v1.json"
)
DEFAULT_RECOMMENDATION_CONFIG = (
    PROJECT_ROOT / "configs" / "modeling" / "family_a_recommendation_v1.json"
)
DEFAULT_EXPERIMENT_TEMPLATE_CONFIG = (
    PROJECT_ROOT / "configs" / "validation" / "family_a_experiment_execution_v1.json"
)
DEFAULT_CAMPAIGN_PREP_CONFIG = (
    PROJECT_ROOT / "configs" / "validation" / "family_a_prospective_campaign_v1.json"
)
DEFAULT_CAMPAIGN_ANALYSIS_CONFIG = (
    PROJECT_ROOT / "configs" / "validation" / "family_a_campaign_analysis_v1.json"
)
DEFAULT_FAILURE_ANALYSIS_CONFIG = (
    PROJECT_ROOT / "configs" / "validation" / "family_a_failure_mode_analysis_v1.json"
)
DEFAULT_GOVERNANCE_CONFIG = PROJECT_ROOT / "configs" / "mvp" / "family_a_mvp_governance_v1.json"
DEFAULT_RECOMMENDATION_UI_OUTPUT = (
    PROJECT_ROOT / "data" / "canonical" / "family_a" / "manifests" / "recommendations" / "recommendation_ui.html"
)
DEFAULT_EXPERIMENT_TEMPLATE_OUTPUT = (
    PROJECT_ROOT / "data" / "canonical" / "family_a" / "manifests" / "reports" / "experiment_execution_template.json"
)
DEFAULT_CAMPAIGN_PREP_OUTPUT = (
    PROJECT_ROOT / "data" / "canonical" / "family_a" / "manifests" / "reports" / "campaign_prepared.json"
)
DEFAULT_CAMPAIGN_ANALYSIS_OUTPUT = (
    PROJECT_ROOT / "data" / "canonical" / "family_a" / "manifests" / "reports" / "campaign_analysis.json"
)
DEFAULT_FAILURE_ANALYSIS_OUTPUT = (
    PROJECT_ROOT / "data" / "canonical" / "family_a" / "manifests" / "reports" / "failure_mode_analysis.json"
)
DEFAULT_GOVERNANCE_OUTPUT_DIR = (
    PROJECT_ROOT / "data" / "canonical" / "family_a" / "manifests" / "reports"
)
DEFAULT_SEGMENTATION_CONFIG = PROJECT_ROOT / "configs" / "modeling" / "family_a_segmentation_v1.json"
DEFAULT_CONTOUR_EXTRACTION_CONFIG = (
    PROJECT_ROOT / "configs" / "modeling" / "family_a_contour_extraction_v1.json"
)
DEFAULT_FEATURE_QA_CONFIG = PROJECT_ROOT / "configs" / "modeling" / "family_a_feature_qa_v1.json"
DEFAULT_LABEL_CORRECTION_CONFIG = (
    PROJECT_ROOT / "configs" / "modeling" / "family_a_label_correction_v1.json"
)
DEFAULT_SNAPSHOT_DIR = PROJECT_ROOT / "data" / "canonical" / "snapshots"
DEFAULT_MODEL_OUTPUT_DIR = PROJECT_ROOT / "data" / "canonical" / "family_a" / "manifests" / "models"
DEFAULT_MODEL_CARD_OUTPUT_DIR = (
    PROJECT_ROOT / "data" / "canonical" / "family_a" / "manifests" / "model_cards"
)
DEFAULT_SEGMENTATION_OUTPUT_DIR = (
    PROJECT_ROOT / "data" / "canonical" / "family_a" / "manifests" / "segmentation_models"
)
DEFAULT_CONTOUR_DERIVED_OUTPUT_DIR = (
    PROJECT_ROOT / "data" / "canonical" / "family_a" / "manifests" / "derived_features_from_contours"
)
DEFAULT_REPRO_LOCKFILE = PROJECT_ROOT / "locks" / "environment.lock.txt"
DEFAULT_REPRO_CHECK_REPORT = (
    PROJECT_ROOT / "data" / "canonical" / "family_a" / "manifests" / "reports" / "determinism_report.json"
)
DEFAULT_SMOKE_CHECK_REPORT = (
    PROJECT_ROOT / "data" / "canonical" / "family_a" / "manifests" / "reports" / "smoke_check_report.json"
)
DEFAULT_HANDOFF_CHECK_REPORT = (
    PROJECT_ROOT / "data" / "canonical" / "family_a" / "manifests" / "reports" / "data_handoff_check.json"
)


def _run_script(script_name: str, script_args: list[str]) -> int:
    script_path = SCRIPTS_DIR / script_name
    if not script_path.exists():
        print(f"Script not found: {script_path}")
        return 2

    command = [sys.executable, str(script_path), *script_args]
    print("$ " + " ".join(command))
    completed = subprocess.run(command, check=False)
    return int(completed.returncode)


def _cmd_inventory(args: argparse.Namespace) -> int:
    return _run_script(
        "build_inventory.py",
        [
            "--source-dir",
            str(args.source_dir),
            "--output",
            str(args.output),
            "--family",
            args.family,
        ],
    )


def _cmd_handoff_check(args: argparse.Namespace) -> int:
    script_args = [
        "--source-dir",
        str(args.source_dir),
        "--output",
        str(args.output),
        "--schema",
        str(args.schema),
        "--family",
        args.family,
    ]
    if args.require_labels:
        script_args.append("--require-labels")
    if args.require_derived:
        script_args.append("--require-derived")
    return _run_script("check_data_handoff.py", script_args)


def _cmd_ingest(args: argparse.Namespace) -> int:
    script_args = [
        "--source-dir",
        str(args.source_dir),
        "--dest-root",
        str(args.dest_root),
        "--schema",
        str(args.schema),
        "--family",
        args.family,
        "--run-id-mode",
        args.run_id_mode,
    ]
    if args.overwrite:
        script_args.append("--overwrite")
    if args.dry_run:
        script_args.append("--dry-run")
    return _run_script("ingest_runs.py", script_args)


def _cmd_validate(args: argparse.Namespace) -> int:
    script_args = [
        "--dataset-root",
        str(args.dataset_root),
        "--run-schema",
        str(args.run_schema),
        "--features-schema",
        str(args.features_schema),
    ]
    if args.require_labels:
        script_args.append("--require-labels")
    if args.require_derived:
        script_args.append("--require-derived")
    if args.allow_noncanonical_run_id:
        script_args.append("--allow-noncanonical-run-id")
    return _run_script("validate_dataset.py", script_args)


def _cmd_split(args: argparse.Namespace) -> int:
    return _run_script(
        "create_split.py",
        [
            "--dataset-root",
            str(args.dataset_root),
            "--config",
            str(args.config),
            "--output",
            str(args.output),
        ],
    )


def _cmd_baseline(args: argparse.Namespace) -> int:
    script_args = [
        "--dataset-root",
        str(args.dataset_root),
        "--config",
        str(args.config),
        "--output",
        str(args.output),
    ]
    if args.split is not None:
        script_args.extend(["--split", str(args.split)])
    return _run_script("baseline_regime_map.py", script_args)


def _cmd_snapshot(args: argparse.Namespace) -> int:
    return _run_script(
        "snapshot_dataset.py",
        [
            "--dataset-root",
            str(args.dataset_root),
            "--name",
            args.name,
            "--output-dir",
            str(args.output_dir),
        ],
    )


def _cmd_sim_plan(args: argparse.Namespace) -> int:
    script_args = [
        "--config",
        str(args.config),
        "--output",
        str(args.output),
        "--family",
        args.family,
    ]
    if args.manifest_output is not None:
        script_args.extend(["--manifest-output", str(args.manifest_output)])
    return _run_script("plan_axisymmetric_sweep.py", script_args)


def _cmd_sim_generate(args: argparse.Namespace) -> int:
    script_args = [
        "--plan-jsonl",
        str(args.plan_jsonl),
        "--output-root",
        str(args.output_root),
        "--surrogate-config",
        str(args.surrogate_config),
        "--run-schema",
        str(args.run_schema),
        "--features-schema",
        str(args.features_schema),
        "--family",
        args.family,
    ]
    if args.max_cases is not None:
        script_args.extend(["--max-cases", str(args.max_cases)])
    if args.overwrite:
        script_args.append("--overwrite")
    if args.dry_run:
        script_args.append("--dry-run")
    return _run_script("generate_simulation_corpus.py", script_args)


def _cmd_sim_realism(args: argparse.Namespace) -> int:
    script_args = [
        "--simulation-dataset-root",
        str(args.simulation_dataset_root),
        "--output",
        str(args.output),
    ]
    if args.experimental_dataset_root is not None:
        script_args.extend(["--experimental-dataset-root", str(args.experimental_dataset_root)])
    if args.max_runs is not None:
        script_args.extend(["--max-runs", str(args.max_runs)])
    return _run_script("report_simulation_realism.py", script_args)


def _cmd_model_train(args: argparse.Namespace) -> int:
    script_args = [
        "--dataset-root",
        str(args.dataset_root),
        "--split",
        str(args.split),
        "--config",
        str(args.config),
        "--output-dir",
        str(args.output_dir),
    ]
    if args.model_id is not None:
        script_args.extend(["--model-id", args.model_id])
    return _run_script("train_multimodal_model.py", script_args)


def _cmd_model_finetune(args: argparse.Namespace) -> int:
    script_args = [
        "--dataset-root",
        str(args.dataset_root),
        "--split",
        str(args.split),
        "--config",
        str(args.config),
        "--output-dir",
        str(args.output_dir),
        "--init-model",
        str(args.init_model),
    ]
    if args.model_id is not None:
        script_args.extend(["--model-id", args.model_id])
    return _run_script("train_multimodal_model.py", script_args)


def _cmd_model_calibrate(args: argparse.Namespace) -> int:
    script_args = [
        "--predictions",
        str(args.predictions),
        "--config",
        str(args.config),
        "--output",
        str(args.output),
    ]
    if args.calibrated_predictions_output is not None:
        script_args.extend(
            [
                "--calibrated-predictions-output",
                str(args.calibrated_predictions_output),
            ]
        )
    return _run_script("calibrate_multimodal_uncertainty.py", script_args)


def _cmd_model_card(args: argparse.Namespace) -> int:
    script_args = [
        "--model-artifact",
        str(args.model_artifact),
        "--eval-artifact",
        str(args.eval_artifact),
        "--output",
        str(args.output),
        "--template",
        str(args.template),
    ]
    if args.calibration_artifact is not None:
        script_args.extend(["--calibration-artifact", str(args.calibration_artifact)])
    return _run_script("generate_model_card.py", script_args)


def _cmd_recommend(args: argparse.Namespace) -> int:
    script_args = [
        "--model-artifact",
        str(args.model_artifact),
        "--candidates",
        str(args.candidates),
        "--config",
        str(args.config),
        "--output",
        str(args.output),
    ]
    if args.calibration_artifact is not None:
        script_args.extend(["--calibration-artifact", str(args.calibration_artifact)])
    if args.top_k is not None:
        script_args.extend(["--top-k", str(args.top_k)])
    return _run_script("recommend_next_experiments.py", script_args)


def _cmd_recommend_ui(args: argparse.Namespace) -> int:
    script_args = [
        "--recommendation-report",
        str(args.recommendation_report),
        "--output-html",
        str(args.output_html),
        "--title",
        args.title,
        "--max-rejected",
        str(args.max_rejected),
    ]
    return _run_script("build_recommendation_ui.py", script_args)


def _cmd_experiment_template(args: argparse.Namespace) -> int:
    script_args = [
        "--recommendation-report",
        str(args.recommendation_report),
        "--config",
        str(args.config),
        "--output",
        str(args.output),
    ]
    if args.markdown_output is not None:
        script_args.extend(["--markdown-output", str(args.markdown_output)])
    if args.top_k is not None:
        script_args.extend(["--top-k", str(args.top_k)])
    if args.campaign_id is not None:
        script_args.extend(["--campaign-id", args.campaign_id])
    return _run_script("build_experiment_execution_template.py", script_args)


def _cmd_campaign_prepare(args: argparse.Namespace) -> int:
    script_args = [
        "--runs-input",
        str(args.runs_input),
        "--config",
        str(args.config),
        "--analysis-config",
        str(args.analysis_config),
        "--campaign-profile",
        args.campaign_profile,
        "--output",
        str(args.output),
    ]
    if args.campaign_log_output is not None:
        script_args.extend(["--campaign-log-output", str(args.campaign_log_output)])
    if args.markdown_output is not None:
        script_args.extend(["--markdown-output", str(args.markdown_output)])
    if args.max_runs is not None:
        script_args.extend(["--max-runs", str(args.max_runs)])
    return _run_script("prepare_prospective_campaign.py", script_args)


def _cmd_campaign_analyze(args: argparse.Namespace) -> int:
    script_args = [
        "--model-guided-log",
        str(args.model_guided_log),
        "--baseline-log",
        str(args.baseline_log),
        "--config",
        str(args.config),
        "--output",
        str(args.output),
    ]
    if args.markdown_output is not None:
        script_args.extend(["--markdown-output", str(args.markdown_output)])
    return _run_script("analyze_campaign_outcomes.py", script_args)


def _cmd_failure_analysis(args: argparse.Namespace) -> int:
    script_args = [
        "--predictions",
        str(args.predictions),
        "--config",
        str(args.config),
        "--output",
        str(args.output),
    ]
    if args.markdown_output is not None:
        script_args.extend(["--markdown-output", str(args.markdown_output)])
    if args.max_runs is not None:
        script_args.extend(["--max-runs", str(args.max_runs)])
    return _run_script("build_failure_mode_analysis.py", script_args)


def _cmd_mvp_governance(args: argparse.Namespace) -> int:
    script_args = [
        "--progress-tracker",
        str(args.progress_tracker),
        "--todo",
        str(args.todo),
        "--config",
        str(args.config),
        "--output-dir",
        str(args.output_dir),
        "--prefix",
        args.prefix,
    ]
    return _run_script("build_mvp_governance_pack.py", script_args)


def _cmd_repro_lock(args: argparse.Namespace) -> int:
    script_args = [
        "--pyproject",
        str(args.pyproject),
        "--output",
        str(args.output),
    ]
    for group in args.include_optional:
        script_args.extend(["--include-optional", group])
    if args.skip_project_deps:
        script_args.append("--skip-project-deps")
    if args.strict:
        script_args.append("--strict")
    return _run_script("export_environment_lockfile.py", script_args)


def _cmd_repro_check(args: argparse.Namespace) -> int:
    script_args = [
        "--dataset-root",
        str(args.dataset_root),
        "--split",
        str(args.split),
        "--config",
        str(args.config),
        "--output",
        str(args.output),
        "--model-id-prefix",
        args.model_id_prefix,
    ]
    if args.init_model is not None:
        script_args.extend(["--init-model", str(args.init_model)])
    if args.artifact_dir is not None:
        script_args.extend(["--artifact-dir", str(args.artifact_dir)])
    if args.keep_artifacts:
        script_args.append("--keep-artifacts")
    return _run_script("check_deterministic_training.py", script_args)


def _cmd_smoke_check(args: argparse.Namespace) -> int:
    script_args = ["--output", str(args.output)]
    if args.skip_compile:
        script_args.append("--skip-compile")
    if args.handoff_source_dir is not None:
        script_args.extend(
            [
                "--handoff-source-dir",
                str(args.handoff_source_dir),
                "--handoff-output",
                str(args.handoff_output),
                "--handoff-schema",
                str(args.handoff_schema),
                "--handoff-family",
                args.handoff_family,
            ]
        )
        if args.handoff_require_labels:
            script_args.append("--handoff-require-labels")
        if args.handoff_require_derived:
            script_args.append("--handoff-require-derived")
    return _run_script("run_smoke_checks.py", script_args)


def _cmd_segment_train(args: argparse.Namespace) -> int:
    script_args = [
        "--dataset-root",
        str(args.dataset_root),
        "--annotations",
        str(args.annotations),
        "--config",
        str(args.config),
        "--output-dir",
        str(args.output_dir),
    ]
    if args.split is not None:
        script_args.extend(["--split", str(args.split)])
    if args.model_id is not None:
        script_args.extend(["--model-id", args.model_id])
    return _run_script("train_interface_segmentation.py", script_args)


def _cmd_extract_trajectories(args: argparse.Namespace) -> int:
    script_args = [
        "--dataset-root",
        str(args.dataset_root),
        "--contours",
        str(args.contours),
        "--config",
        str(args.config),
        "--output-dir",
        str(args.output_dir),
    ]
    if args.model_version is not None:
        script_args.extend(["--model-version", args.model_version])
    if args.max_runs is not None:
        script_args.extend(["--max-runs", str(args.max_runs)])
    return _run_script("extract_contours_trajectories.py", script_args)


def _cmd_feature_qa(args: argparse.Namespace) -> int:
    if args.dataset_root is None and args.derived_features_index is None:
        print("feature-qa requires either --dataset-root or --derived-features-index")
        return 2

    script_args = [
        "--config",
        str(args.config),
        "--output",
        str(args.output),
        "--features-glob",
        args.features_glob,
    ]
    if args.dataset_root is not None:
        script_args.extend(["--dataset-root", str(args.dataset_root)])
    if args.derived_features_index is not None:
        script_args.extend(["--derived-features-index", str(args.derived_features_index)])
    if args.markdown_output is not None:
        script_args.extend(["--markdown-output", str(args.markdown_output)])
    if args.max_runs is not None:
        script_args.extend(["--max-runs", str(args.max_runs)])
    return _run_script("build_feature_qa_dashboard.py", script_args)


def _cmd_label_correction(args: argparse.Namespace) -> int:
    script_args = [
        "--segmentation-qc",
        str(args.segmentation_qc),
        "--feature-qa",
        str(args.feature_qa),
        "--config",
        str(args.config),
        "--output",
        str(args.output),
    ]
    if args.extraction_report is not None:
        script_args.extend(["--extraction-report", str(args.extraction_report)])
    if args.markdown_output is not None:
        script_args.extend(["--markdown-output", str(args.markdown_output)])
    if args.max_runs is not None:
        script_args.extend(["--max-runs", str(args.max_runs)])
    return _run_script("build_label_correction_queue.py", script_args)


def _cmd_pipeline(args: argparse.Namespace) -> int:
    split_output = args.split_output or (
        args.dataset_root / "manifests" / "splits" / f"{args.snapshot_name}.json"
    )
    baseline_output = args.baseline_output or (
        args.dataset_root / "manifests" / "reports" / f"baseline_{args.snapshot_name}.json"
    )

    ingest_args = [
        "--source-dir",
        str(args.source_dir),
        "--dest-root",
        str(args.dataset_root),
        "--schema",
        str(args.run_schema),
        "--family",
        args.family,
        "--run-id-mode",
        args.run_id_mode,
    ]
    if args.overwrite:
        ingest_args.append("--overwrite")

    validate_args = [
        "--dataset-root",
        str(args.dataset_root),
        "--run-schema",
        str(args.run_schema),
        "--features-schema",
        str(args.features_schema),
    ]
    if args.require_labels:
        validate_args.append("--require-labels")
    if args.require_derived:
        validate_args.append("--require-derived")

    steps: list[tuple[str, str, list[str]]] = [
        ("ingest", "ingest_runs.py", ingest_args),
        ("validate", "validate_dataset.py", validate_args),
        (
            "split",
            "create_split.py",
            [
                "--dataset-root",
                str(args.dataset_root),
                "--config",
                str(args.split_config),
                "--output",
                str(split_output),
            ],
        ),
        (
            "baseline",
            "baseline_regime_map.py",
            [
                "--dataset-root",
                str(args.dataset_root),
                "--config",
                str(args.baseline_config),
                "--split",
                str(split_output),
                "--output",
                str(baseline_output),
            ],
        ),
        (
            "snapshot",
            "snapshot_dataset.py",
            [
                "--dataset-root",
                str(args.dataset_root),
                "--name",
                args.snapshot_name,
                "--output-dir",
                str(args.snapshot_output_dir),
            ],
        ),
    ]

    for step_name, script_name, script_args in steps:
        print(f"\n==> {step_name}")
        return_code = _run_script(script_name, script_args)
        if return_code != 0:
            print(f"Pipeline failed at step '{step_name}' with exit code {return_code}.")
            return return_code

    print("\nPipeline completed successfully.")
    print(f"Split artifact: {split_output}")
    print(f"Baseline report: {baseline_output}")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="interact-capsules",
        description="Unified CLI for INTERACT-Capsules MVP data/simulation workflows.",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    inventory = subparsers.add_parser("inventory", help="MVP-004: Build raw-run inventory CSV.")
    inventory.add_argument("--source-dir", required=True, type=Path)
    inventory.add_argument("--output", required=True, type=Path)
    inventory.add_argument("--family", default="A", choices=["A", "B", "C"])
    inventory.set_defaults(func=_cmd_inventory)

    handoff_check = subparsers.add_parser(
        "handoff-check",
        help="MVP-004/005/006: Check raw handoff readiness before canonical ingest.",
    )
    handoff_check.add_argument("--source-dir", required=True, type=Path)
    handoff_check.add_argument("--output", default=DEFAULT_HANDOFF_CHECK_REPORT, type=Path)
    handoff_check.add_argument("--schema", default=DEFAULT_RUN_SCHEMA, type=Path)
    handoff_check.add_argument("--family", default="A", choices=["A", "B", "C"])
    handoff_check.add_argument("--require-labels", action="store_true")
    handoff_check.add_argument("--require-derived", action="store_true")
    handoff_check.set_defaults(func=_cmd_handoff_check)

    ingest = subparsers.add_parser("ingest", help="MVP-005: Ingest raw runs into canonical layout.")
    ingest.add_argument("--source-dir", required=True, type=Path)
    ingest.add_argument("--dest-root", required=True, type=Path)
    ingest.add_argument("--schema", default=DEFAULT_RUN_SCHEMA, type=Path)
    ingest.add_argument("--family", default="A", choices=["A", "B", "C"])
    ingest.add_argument("--run-id-mode", choices=["canonicalize", "preserve"], default="canonicalize")
    ingest.add_argument("--overwrite", action="store_true")
    ingest.add_argument("--dry-run", action="store_true")
    ingest.set_defaults(func=_cmd_ingest)

    validate = subparsers.add_parser("validate", help="MVP-006: Validate canonical dataset artifacts.")
    validate.add_argument("--dataset-root", required=True, type=Path)
    validate.add_argument("--run-schema", default=DEFAULT_RUN_SCHEMA, type=Path)
    validate.add_argument("--features-schema", default=DEFAULT_FEATURES_SCHEMA, type=Path)
    validate.add_argument("--require-labels", action="store_true")
    validate.add_argument("--require-derived", action="store_true")
    validate.add_argument("--allow-noncanonical-run-id", action="store_true")
    validate.set_defaults(func=_cmd_validate)

    split = subparsers.add_parser("split", help="MVP-008: Create train/val/test split artifact.")
    split.add_argument("--dataset-root", required=True, type=Path)
    split.add_argument("--config", default=DEFAULT_SPLIT_CONFIG, type=Path)
    split.add_argument("--output", required=True, type=Path)
    split.set_defaults(func=_cmd_split)

    baseline = subparsers.add_parser("baseline", help="MVP-009: Run baseline regime-map benchmark.")
    baseline.add_argument("--dataset-root", required=True, type=Path)
    baseline.add_argument("--config", default=DEFAULT_BASELINE_CONFIG, type=Path)
    baseline.add_argument("--split", type=Path, default=None)
    baseline.add_argument("--output", required=True, type=Path)
    baseline.set_defaults(func=_cmd_baseline)

    snapshot = subparsers.add_parser("snapshot", help="MVP-007: Snapshot dataset manifest/index.")
    snapshot.add_argument("--dataset-root", required=True, type=Path)
    snapshot.add_argument("--name", required=True)
    snapshot.add_argument("--output-dir", default=DEFAULT_SNAPSHOT_DIR, type=Path)
    snapshot.set_defaults(func=_cmd_snapshot)

    sim_plan = subparsers.add_parser("sim-plan", help="MVP-015/016: Plan axisymmetric simulation sweep.")
    sim_plan.add_argument("--config", default=DEFAULT_SWEEP_CONFIG, type=Path)
    sim_plan.add_argument("--output", required=True, type=Path)
    sim_plan.add_argument("--manifest-output", type=Path, default=None)
    sim_plan.add_argument("--family", default="A", choices=["A", "B", "C"])
    sim_plan.set_defaults(func=_cmd_sim_plan)

    sim_generate = subparsers.add_parser("sim-generate", help="MVP-017: Generate synthetic simulation corpus.")
    sim_generate.add_argument("--plan-jsonl", required=True, type=Path)
    sim_generate.add_argument("--output-root", required=True, type=Path)
    sim_generate.add_argument("--surrogate-config", default=DEFAULT_SURROGATE_CONFIG, type=Path)
    sim_generate.add_argument("--run-schema", default=DEFAULT_RUN_SCHEMA, type=Path)
    sim_generate.add_argument("--features-schema", default=DEFAULT_FEATURES_SCHEMA, type=Path)
    sim_generate.add_argument("--family", default="A", choices=["A", "B", "C"])
    sim_generate.add_argument("--max-cases", type=int, default=None)
    sim_generate.add_argument("--overwrite", action="store_true")
    sim_generate.add_argument("--dry-run", action="store_true")
    sim_generate.set_defaults(func=_cmd_sim_generate)

    sim_realism = subparsers.add_parser("sim-realism", help="MVP-018: Build simulation realism report.")
    sim_realism.add_argument("--simulation-dataset-root", required=True, type=Path)
    sim_realism.add_argument("--experimental-dataset-root", type=Path, default=None)
    sim_realism.add_argument("--output", required=True, type=Path)
    sim_realism.add_argument("--max-runs", type=int, default=None)
    sim_realism.set_defaults(func=_cmd_sim_realism)

    model_train = subparsers.add_parser(
        "model-train",
        help="MVP-020: Train/evaluate config-driven multimodal model baseline.",
    )
    model_train.add_argument("--dataset-root", required=True, type=Path)
    model_train.add_argument("--split", required=True, type=Path)
    model_train.add_argument("--config", default=DEFAULT_MODEL_CONFIG, type=Path)
    model_train.add_argument("--output-dir", default=DEFAULT_MODEL_OUTPUT_DIR, type=Path)
    model_train.add_argument("--model-id", default=None)
    model_train.set_defaults(func=_cmd_model_train)

    model_finetune = subparsers.add_parser(
        "model-finetune",
        help="MVP-022: Fine-tune multimodal model on experimental Family A data from a pretrained checkpoint artifact.",
    )
    model_finetune.add_argument("--dataset-root", required=True, type=Path)
    model_finetune.add_argument("--split", required=True, type=Path)
    model_finetune.add_argument("--init-model", required=True, type=Path)
    model_finetune.add_argument("--config", default=DEFAULT_FINETUNE_CONFIG, type=Path)
    model_finetune.add_argument("--output-dir", default=DEFAULT_MODEL_OUTPUT_DIR, type=Path)
    model_finetune.add_argument("--model-id", default=None)
    model_finetune.set_defaults(func=_cmd_model_finetune)

    model_calibrate = subparsers.add_parser(
        "model-calibrate",
        help="MVP-023: Calibrate model uncertainty from prediction artifacts.",
    )
    model_calibrate.add_argument("--predictions", required=True, type=Path)
    model_calibrate.add_argument("--config", default=DEFAULT_CALIBRATION_CONFIG, type=Path)
    model_calibrate.add_argument("--output", required=True, type=Path)
    model_calibrate.add_argument("--calibrated-predictions-output", default=None, type=Path)
    model_calibrate.set_defaults(func=_cmd_model_calibrate)

    model_card = subparsers.add_parser(
        "model-card",
        help="MVP-024: Generate standardized model card markdown.",
    )
    model_card.add_argument("--model-artifact", required=True, type=Path)
    model_card.add_argument("--eval-artifact", required=True, type=Path)
    model_card.add_argument("--calibration-artifact", default=None, type=Path)
    model_card.add_argument("--template", default=PROJECT_ROOT / "templates" / "model_card.template.md", type=Path)
    model_card.add_argument("--output", default=DEFAULT_MODEL_CARD_OUTPUT_DIR / "model_card.md", type=Path)
    model_card.set_defaults(func=_cmd_model_card)

    recommend = subparsers.add_parser(
        "recommend",
        help="MVP-025/026/027: Rank next experiments with objective + acquisition + guardrails.",
    )
    recommend.add_argument("--model-artifact", required=True, type=Path)
    recommend.add_argument("--candidates", required=True, type=Path)
    recommend.add_argument("--config", default=DEFAULT_RECOMMENDATION_CONFIG, type=Path)
    recommend.add_argument("--output", required=True, type=Path)
    recommend.add_argument("--calibration-artifact", default=None, type=Path)
    recommend.add_argument("--top-k", default=None, type=int)
    recommend.set_defaults(func=_cmd_recommend)

    recommend_ui = subparsers.add_parser(
        "recommend-ui",
        help="MVP-030: Build standalone HTML UI from recommendation report artifacts.",
    )
    recommend_ui.add_argument("--recommendation-report", required=True, type=Path)
    recommend_ui.add_argument("--output-html", default=DEFAULT_RECOMMENDATION_UI_OUTPUT, type=Path)
    recommend_ui.add_argument("--title", default="INTERACT-Capsules Recommendation Review")
    recommend_ui.add_argument("--max-rejected", default=250, type=int)
    recommend_ui.set_defaults(func=_cmd_recommend_ui)

    experiment_template = subparsers.add_parser(
        "experiment-template",
        help="MVP-031: Convert recommendation report into operator execution template.",
    )
    experiment_template.add_argument("--recommendation-report", required=True, type=Path)
    experiment_template.add_argument("--config", default=DEFAULT_EXPERIMENT_TEMPLATE_CONFIG, type=Path)
    experiment_template.add_argument("--output", default=DEFAULT_EXPERIMENT_TEMPLATE_OUTPUT, type=Path)
    experiment_template.add_argument("--markdown-output", default=None, type=Path)
    experiment_template.add_argument("--top-k", default=None, type=int)
    experiment_template.add_argument("--campaign-id", default=None)
    experiment_template.set_defaults(func=_cmd_experiment_template)

    campaign_prepare = subparsers.add_parser(
        "campaign-prepare",
        help="MVP-032/033: Prepare primary/robustness campaign plan + append-ready run log template.",
    )
    campaign_prepare.add_argument("--runs-input", required=True, type=Path)
    campaign_prepare.add_argument("--config", default=DEFAULT_CAMPAIGN_PREP_CONFIG, type=Path)
    campaign_prepare.add_argument("--analysis-config", default=DEFAULT_CAMPAIGN_ANALYSIS_CONFIG, type=Path)
    campaign_prepare.add_argument("--campaign-profile", required=True)
    campaign_prepare.add_argument("--output", default=DEFAULT_CAMPAIGN_PREP_OUTPUT, type=Path)
    campaign_prepare.add_argument("--campaign-log-output", default=None, type=Path)
    campaign_prepare.add_argument("--markdown-output", default=None, type=Path)
    campaign_prepare.add_argument("--max-runs", default=None, type=int)
    campaign_prepare.set_defaults(func=_cmd_campaign_prepare)

    campaign_analyze = subparsers.add_parser(
        "campaign-analyze",
        help="MVP-034: Compare model-guided vs baseline campaign outcomes and reduction.",
    )
    campaign_analyze.add_argument("--model-guided-log", required=True, type=Path)
    campaign_analyze.add_argument("--baseline-log", required=True, type=Path)
    campaign_analyze.add_argument("--config", default=DEFAULT_CAMPAIGN_ANALYSIS_CONFIG, type=Path)
    campaign_analyze.add_argument("--output", default=DEFAULT_CAMPAIGN_ANALYSIS_OUTPUT, type=Path)
    campaign_analyze.add_argument("--markdown-output", default=None, type=Path)
    campaign_analyze.set_defaults(func=_cmd_campaign_analyze)

    failure_analysis = subparsers.add_parser(
        "failure-analysis",
        help="MVP-035: Build failure-mode taxonomy report from prediction artifacts.",
    )
    failure_analysis.add_argument("--predictions", required=True, type=Path)
    failure_analysis.add_argument("--config", default=DEFAULT_FAILURE_ANALYSIS_CONFIG, type=Path)
    failure_analysis.add_argument("--output", default=DEFAULT_FAILURE_ANALYSIS_OUTPUT, type=Path)
    failure_analysis.add_argument("--markdown-output", default=None, type=Path)
    failure_analysis.add_argument("--max-runs", default=None, type=int)
    failure_analysis.set_defaults(func=_cmd_failure_analysis)

    mvp_governance = subparsers.add_parser(
        "mvp-governance",
        help="MVP-038/039/040: Build internal handoff pack, go/no-go memo, and post-MVP roadmap draft.",
    )
    mvp_governance.add_argument(
        "--progress-tracker",
        default=PROJECT_ROOT / "docs" / "mvp" / "Progress_Tracking.md",
        type=Path,
    )
    mvp_governance.add_argument("--todo", default=PROJECT_ROOT / "docs" / "mvp" / "ToDo.md", type=Path)
    mvp_governance.add_argument("--config", default=DEFAULT_GOVERNANCE_CONFIG, type=Path)
    mvp_governance.add_argument("--output-dir", default=DEFAULT_GOVERNANCE_OUTPUT_DIR, type=Path)
    mvp_governance.add_argument("--prefix", default="family_a_mvp")
    mvp_governance.set_defaults(func=_cmd_mvp_governance)

    repro_lock = subparsers.add_parser(
        "repro-lock",
        help="MVP-036: Export pinned environment lockfile from pyproject dependency groups.",
    )
    repro_lock.add_argument("--pyproject", default=PROJECT_ROOT / "pyproject.toml", type=Path)
    repro_lock.add_argument("--output", default=DEFAULT_REPRO_LOCKFILE, type=Path)
    repro_lock.add_argument("--include-optional", action="append", default=["validation"])
    repro_lock.add_argument("--skip-project-deps", action="store_true")
    repro_lock.add_argument("--strict", action="store_true")
    repro_lock.set_defaults(func=_cmd_repro_lock)

    repro_check = subparsers.add_parser(
        "repro-check",
        help="MVP-036: Verify deterministic model train/eval outputs under repeated identical runs.",
    )
    repro_check.add_argument("--dataset-root", required=True, type=Path)
    repro_check.add_argument("--split", required=True, type=Path)
    repro_check.add_argument("--config", default=DEFAULT_MODEL_CONFIG, type=Path)
    repro_check.add_argument("--output", default=DEFAULT_REPRO_CHECK_REPORT, type=Path)
    repro_check.add_argument("--init-model", default=None, type=Path)
    repro_check.add_argument("--model-id-prefix", default="determinism_probe")
    repro_check.add_argument("--artifact-dir", default=None, type=Path)
    repro_check.add_argument("--keep-artifacts", action="store_true")
    repro_check.set_defaults(func=_cmd_repro_check)

    smoke_check = subparsers.add_parser(
        "smoke-check",
        help="MVP-028/029/036/037: Run local parser, syntax, and smoke-test verification bundle.",
    )
    smoke_check.add_argument("--output", default=DEFAULT_SMOKE_CHECK_REPORT, type=Path)
    smoke_check.add_argument("--skip-compile", action="store_true")
    smoke_check.add_argument("--handoff-source-dir", default=None, type=Path)
    smoke_check.add_argument("--handoff-output", default=DEFAULT_HANDOFF_CHECK_REPORT, type=Path)
    smoke_check.add_argument("--handoff-schema", default=DEFAULT_RUN_SCHEMA, type=Path)
    smoke_check.add_argument("--handoff-family", default="A", choices=["A", "B", "C"])
    smoke_check.add_argument("--handoff-require-labels", action="store_true")
    smoke_check.add_argument("--handoff-require-derived", action="store_true")
    smoke_check.set_defaults(func=_cmd_smoke_check)

    segment_train = subparsers.add_parser(
        "segment-train",
        help="MVP-011: Train/validate lightweight interface segmentation baseline and QC report.",
    )
    segment_train.add_argument("--dataset-root", required=True, type=Path)
    segment_train.add_argument("--annotations", required=True, type=Path)
    segment_train.add_argument("--config", default=DEFAULT_SEGMENTATION_CONFIG, type=Path)
    segment_train.add_argument("--split", default=None, type=Path)
    segment_train.add_argument("--output-dir", default=DEFAULT_SEGMENTATION_OUTPUT_DIR, type=Path)
    segment_train.add_argument("--model-id", default=None)
    segment_train.set_defaults(func=_cmd_segment_train)

    extract_trajectories = subparsers.add_parser(
        "extract-trajectories",
        help="MVP-012: Extract contour-derived trajectories into derived-features artifacts.",
    )
    extract_trajectories.add_argument("--dataset-root", required=True, type=Path)
    extract_trajectories.add_argument("--contours", required=True, type=Path)
    extract_trajectories.add_argument("--config", default=DEFAULT_CONTOUR_EXTRACTION_CONFIG, type=Path)
    extract_trajectories.add_argument("--output-dir", default=DEFAULT_CONTOUR_DERIVED_OUTPUT_DIR, type=Path)
    extract_trajectories.add_argument("--model-version", default=None)
    extract_trajectories.add_argument("--max-runs", default=None, type=int)
    extract_trajectories.set_defaults(func=_cmd_extract_trajectories)

    feature_qa = subparsers.add_parser(
        "feature-qa",
        help="MVP-013: Build derived-feature QA dashboard with sanity/outlier checks.",
    )
    feature_qa.add_argument("--dataset-root", default=None, type=Path)
    feature_qa.add_argument("--derived-features-index", default=None, type=Path)
    feature_qa.add_argument("--features-glob", default="runs/*/derived_features.json")
    feature_qa.add_argument("--config", default=DEFAULT_FEATURE_QA_CONFIG, type=Path)
    feature_qa.add_argument("--output", required=True, type=Path)
    feature_qa.add_argument("--markdown-output", default=None, type=Path)
    feature_qa.add_argument("--max-runs", default=None, type=int)
    feature_qa.set_defaults(func=_cmd_feature_qa)

    label_correction = subparsers.add_parser(
        "label-correction",
        help="MVP-014: Build prioritized active label/error-correction queue from QC and QA artifacts.",
    )
    label_correction.add_argument("--segmentation-qc", required=True, type=Path)
    label_correction.add_argument("--feature-qa", required=True, type=Path)
    label_correction.add_argument("--extraction-report", default=None, type=Path)
    label_correction.add_argument("--config", default=DEFAULT_LABEL_CORRECTION_CONFIG, type=Path)
    label_correction.add_argument("--output", required=True, type=Path)
    label_correction.add_argument("--markdown-output", default=None, type=Path)
    label_correction.add_argument("--max-runs", default=None, type=int)
    label_correction.set_defaults(func=_cmd_label_correction)

    pipeline = subparsers.add_parser(
        "pipeline",
        help="MVP-029: Run canonical Family A workflow (ingest -> validate -> split -> baseline -> snapshot).",
    )
    pipeline.add_argument("--source-dir", required=True, type=Path)
    pipeline.add_argument("--dataset-root", required=True, type=Path)
    pipeline.add_argument("--family", default="A", choices=["A", "B", "C"])
    pipeline.add_argument("--run-id-mode", choices=["canonicalize", "preserve"], default="canonicalize")
    pipeline.add_argument("--run-schema", default=DEFAULT_RUN_SCHEMA, type=Path)
    pipeline.add_argument("--features-schema", default=DEFAULT_FEATURES_SCHEMA, type=Path)
    pipeline.add_argument("--split-config", default=DEFAULT_SPLIT_CONFIG, type=Path)
    pipeline.add_argument("--split-output", type=Path, default=None)
    pipeline.add_argument("--baseline-config", default=DEFAULT_BASELINE_CONFIG, type=Path)
    pipeline.add_argument("--baseline-output", type=Path, default=None)
    pipeline.add_argument("--snapshot-name", default="family_a_v1")
    pipeline.add_argument("--snapshot-output-dir", default=DEFAULT_SNAPSHOT_DIR, type=Path)
    pipeline.add_argument("--require-labels", action="store_true")
    pipeline.add_argument("--require-derived", action="store_true")
    pipeline.add_argument("--overwrite", action="store_true")
    pipeline.set_defaults(func=_cmd_pipeline)

    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return int(args.func(args))


if __name__ == "__main__":
    raise SystemExit(main())
