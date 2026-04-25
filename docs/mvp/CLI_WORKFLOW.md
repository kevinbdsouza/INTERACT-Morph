# INTERACT-Capsules CLI Workflow (MVP-028/029)

## Purpose
Provide one stable command interface for the current MVP data and simulation workflow while keeping existing script implementations unchanged.

## Command Set

| CLI Command | Task ID | Backing Script |
|---|---|---|
| `interact-capsules inventory` | MVP-004 | `scripts/build_inventory.py` |
| `interact-capsules handoff-check` | MVP-004/005/006 | `scripts/check_data_handoff.py` |
| `interact-capsules ingest` | MVP-005 | `scripts/ingest_runs.py` |
| `interact-capsules validate` | MVP-006 | `scripts/validate_dataset.py` |
| `interact-capsules snapshot` | MVP-007 | `scripts/snapshot_dataset.py` |
| `interact-capsules split` | MVP-008 | `scripts/create_split.py` |
| `interact-capsules baseline` | MVP-009 | `scripts/baseline_regime_map.py` |
| `interact-capsules sim-plan` | MVP-015/016 | `scripts/plan_axisymmetric_sweep.py` |
| `interact-capsules sim-generate` | MVP-017 | `scripts/generate_simulation_corpus.py` |
| `interact-capsules sim-realism` | MVP-018 | `scripts/report_simulation_realism.py` |
| `interact-capsules model-train` | MVP-020 | `scripts/train_multimodal_model.py` |
| `interact-capsules model-finetune` | MVP-022 | `scripts/train_multimodal_model.py --init-model ...` |
| `interact-capsules model-calibrate` | MVP-023 | `scripts/calibrate_multimodal_uncertainty.py` |
| `interact-capsules model-card` | MVP-024 | `scripts/generate_model_card.py` |
| `interact-capsules recommend` | MVP-025/026/027 | `scripts/recommend_next_experiments.py` |
| `interact-capsules recommend-ui` | MVP-030 | `scripts/build_recommendation_ui.py` |
| `interact-capsules experiment-template` | MVP-031 | `scripts/build_experiment_execution_template.py` |
| `interact-capsules campaign-prepare` | MVP-032/033 | `scripts/prepare_prospective_campaign.py` |
| `interact-capsules campaign-analyze` | MVP-034 | `scripts/analyze_campaign_outcomes.py` |
| `interact-capsules failure-analysis` | MVP-035 | `scripts/build_failure_mode_analysis.py` |
| `interact-capsules repro-lock` | MVP-036 | `scripts/export_environment_lockfile.py` |
| `interact-capsules repro-check` | MVP-036 | `scripts/check_deterministic_training.py` |
| `interact-capsules smoke-check` | MVP-028/029/036/037 | `scripts/run_smoke_checks.py` |
| `interact-capsules mvp-governance` | MVP-038/039/040 | `scripts/build_mvp_governance_pack.py` |
| `interact-capsules segment-train` | MVP-011 | `scripts/train_interface_segmentation.py` |
| `interact-capsules extract-trajectories` | MVP-012 | `scripts/extract_contours_trajectories.py` |
| `interact-capsules feature-qa` | MVP-013 | `scripts/build_feature_qa_dashboard.py` |
| `interact-capsules label-correction` | MVP-014 | `scripts/build_label_correction_queue.py` |
| `interact-capsules pipeline` | MVP-029 | orchestrates `ingest -> validate -> split -> baseline -> snapshot` |

## Standard End-to-End Run
```bash
interact-capsules handoff-check \
  --source-dir data/raw \
  --family A \
  --output data/canonical/family_a/manifests/reports/data_handoff_check.json

interact-capsules smoke-check \
  --handoff-source-dir data/raw \
  --handoff-output data/canonical/family_a/manifests/reports/data_handoff_check.json

interact-capsules pipeline \
  --source-dir data/raw \
  --dataset-root data/canonical/family_a \
  --family A \
  --run-id-mode canonicalize \
  --snapshot-name family_a_v1
```

## Notes
- CLI entrypoint: `interact_capsules.cli:main` (declared in `pyproject.toml`).
- Commands return non-zero on first failing step to support automation and CI integration.
- Current scope includes data, simulation, segmentation starter pipeline, active correction queueing, multimodal training/fine-tuning, uncertainty calibration, model-card generation, recommendation ranking, recommendation-to-execution templating, prospective campaign preparation/comparison analysis, failure-mode taxonomy reporting, lightweight recommendation UI, reproducibility lock snapshots, deterministic training checks, local smoke-check reporting, governance pack generation (handoff + go/no-go + roadmap), and feature-QA paths.
- Run `handoff-check` before first production ingest. It reports missing metadata/videos, schema readiness, the recommended `--run-id-mode` (`canonicalize` when source IDs are missing, duplicate, or noncanonical), example affected run folders, and structured `next_actions`.
- When the handoff report is ready, use its first `next_actions` command as the production `pipeline` command so the selected run-ID mode and strictness flags match the preflight evidence.
- `smoke-check --handoff-source-dir ...` appends the same handoff preflight to the parser/test/syntax bundle, so governance evidence can show local code health and raw-handoff readiness from one command.
- Local no-install CLI help check: `python3 src/interact_capsules/cli.py --help`.
- Smoke tests for parser coverage and pipeline fail-fast behavior: `python3 -m unittest discover -s tests`.
- Bundled local verification report: `python3 src/interact_capsules/cli.py smoke-check --output data/canonical/family_a/manifests/reports/smoke_check_report.json`.
