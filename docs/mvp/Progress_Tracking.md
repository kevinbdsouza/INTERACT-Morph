# INTERACT-Capsules MVP Progress Tracking

## 1) How to Use This Tracker

- Update this file at least once per week.
- Keep status values to: `Not Started`, `In Progress`, `At Risk`, `Blocked`, `Done`.
- Link every update to a `ToDo.md` task ID (`MVP-###`).
- Do not mark a milestone `Done` unless its acceptance criteria are evidenced.

## 2) Current Snapshot

- Date: 2026-04-25
- Sprint/Week: W02
- Overall status: In Progress
- Confidence to hit MVP date (High/Medium/Low): Medium
- Biggest blocker: No production Family A dataset ingested yet (raw handoff pending); placeholder production-path pass completed with synthetic Family A data
- Next decision needed: Confirm first production bulk run in `canonicalize` mode vs `preserve` mode after live `handoff-check`

## 3) Milestone Status Board

| Milestone | Target Date | Status | Acceptance Criteria | Evidence Link/Note |
|---|---|---|---|---|
| G1 Data + Baseline Ready | YYYY-MM-DD | Not Started | Curated Family A dataset + schema validation + baseline benchmark complete | |
| G2 Model Usable | YYYY-MM-DD | Not Started | Held-out Family A macro-F1 >= 0.80 + calibration report | |
| G3 Planning Value | YYYY-MM-DD | Not Started | >=30% fewer experiments vs grid search for target window discovery | |
| G4 Tool Usable | YYYY-MM-DD | Not Started | Lab user runs end-to-end workflow without developer help | |

## 4) Task Progress (From ToDo.md)

| Task ID | Owner | Status | Start Date | Due Date | Notes |
|---|---|---|---|---|---|
| MVP-001 | Codex | Done | 2026-04-17 | 2026-04-18 | `docs/mvp/MVP_SPEC.md` created |
| MVP-002 | Codex | Done | 2026-04-17 | 2026-04-18 | `schemas/run_metadata.schema.json` and data architecture doc created |
| MVP-003 | Codex | Done | 2026-04-17 | 2026-04-18 | `schemas/derived_features.schema.json` plus templates created |
| MVP-004 | Codex | In Progress | 2026-04-17 | 2026-04-19 | Inventory now emits `source_run_id` + deterministic `canonical_run_id`; placeholder strict `handoff-check` passed on 120/120 synthetic Family A runs (`data_handoff_check_placeholder_v1.json`, recommended `preserve`); awaiting real data run |
| MVP-005 | Codex | In Progress | 2026-04-17 | 2026-04-20 | Ingestion supports `--run-id-mode`, writes `manifests/run_id_map.jsonl`, hardens missing/partial `asset_paths`, and placeholder pipeline ingested 120/120 runs with `--run-id-mode preserve`; awaiting production raw data |
| MVP-006 | Codex | In Progress | 2026-04-17 | 2026-04-20 | Validation now checks canonical run-ID shape and run directory/metadata ID consistency; placeholder canonical dataset validated 120/120 runs with labels + derived features required |
| MVP-007 | Codex | In Progress | 2026-04-17 | 2026-04-21 | `scripts/snapshot_dataset.py` built and smoke-tested; placeholder snapshot generated at `data/canonical/snapshots/family_a_placeholder_v1.json` |
| MVP-008 | Codex | In Progress | 2026-04-17 | 2026-04-21 | Split script now enforces config fractions, respects `require_video`, validates `group_by_field`, records dataset-manifest fingerprint, and generated placeholder split counts train=83/val=18/test=19 |
| MVP-009 | Codex | In Progress | 2026-04-17 | 2026-04-21 | `scripts/baseline_regime_map.py` + heuristic config built; placeholder baseline report generated (`regime_macro_f1=1.0`, synthetic-only) |
| MVP-010 | Codex | Done | 2026-04-17 | 2026-04-18 | `docs/data/ANNOTATION_GUIDELINES.md` created |
| MVP-011 | Codex | In Progress | 2026-04-18 | 2026-04-30 | Added `scripts/train_interface_segmentation.py`, config `configs/modeling/family_a_segmentation_v1.json`, CLI `interact-capsules segment-train`, and smoke QC artifact `smoke_family_a_segmentation_v1.qc.json` |
| MVP-012 | Codex | In Progress | 2026-04-18 | 2026-05-01 | Added `scripts/extract_contours_trajectories.py`, config `configs/modeling/family_a_contour_extraction_v1.json`, CLI `interact-capsules extract-trajectories`, and smoke extraction report (`runs_written=3`) |
| MVP-013 | Codex | In Progress | 2026-04-18 | 2026-05-01 | Added `scripts/build_feature_qa_dashboard.py`, config `configs/modeling/family_a_feature_qa_v1.json`, CLI `interact-capsules feature-qa`, and smoke QA report (`runs_scanned=3`, `runs_with_issues=0`) |
| MVP-014 | Codex | In Progress | 2026-04-18 | 2026-05-03 | Added `scripts/build_label_correction_queue.py`, config `configs/modeling/family_a_label_correction_v1.json`, docs `docs/modeling/LABEL_CORRECTION_WORKFLOW.md`, and CLI `interact-capsules label-correction`; smoke queue artifact generated |
| MVP-015 | Codex | In Progress | 2026-04-17 | 2026-04-23 | Axisymmetric sweep planner now wired into executable corpus generation workflow (`scripts/plan_axisymmetric_sweep.py`) |
| MVP-016 | Codex | In Progress | 2026-04-17 | 2026-04-23 | DOE range config now exercised by planner plus surrogate execution path (`configs/simulations/family_a_axisymmetric_doe.json`) |
| MVP-017 | Codex | In Progress | 2026-04-17 | 2026-04-24 | `scripts/generate_simulation_corpus.py` + surrogate config added; 12-case smoke corpus generated and schema-validated |
| MVP-018 | Codex | In Progress | 2026-04-17 | 2026-04-25 | Added realism report scaffold `scripts/report_simulation_realism.py`; awaiting production experimental dataset for first full comparison |
| MVP-019 | Codex | In Progress | 2026-04-18 | 2026-04-29 | Added multimodal architecture spec `docs/modeling/MULTIMODAL_MODEL_ARCHITECTURE.md` and config `configs/modeling/family_a_multimodal_v1.json` |
| MVP-020 | Codex | In Progress | 2026-04-18 | 2026-04-30 | Added `scripts/train_multimodal_model.py`, wired `interact-capsules model-train`, smoke-validated on synthetic corpus (`smoke_model_train_v1`), and ran placeholder canonical model training (`family_a_placeholder_v1_multimodal`) |
| MVP-021 | Codex | In Progress | 2026-04-18 | 2026-05-01 | Produced synthetic pretraining rerun artifact set `smoke_family_a_multimodal_v1_pretrain.{model,eval,predictions}.json*` via `train_multimodal_model.py` |
| MVP-022 | Codex | In Progress | 2026-04-18 | 2026-05-02 | Added fine-tuning config `configs/modeling/family_a_multimodal_v1_finetune.json`, CLI `interact-capsules model-finetune`, transfer docs `docs/modeling/FINETUNING_WORKFLOW.md`, and `--init-model` warm-start support in `scripts/train_multimodal_model.py`; smoke fine-tune artifact generated |
| MVP-023 | Codex | In Progress | 2026-04-18 | 2026-05-02 | Added `scripts/calibrate_multimodal_uncertainty.py`, config `configs/modeling/family_a_uncertainty_calibration_v1.json`, and CLI `interact-capsules model-calibrate`; smoke and placeholder calibration artifacts generated |
| MVP-024 | Codex | In Progress | 2026-04-18 | 2026-05-02 | Added `templates/model_card.template.md`, `scripts/generate_model_card.py`, and CLI `interact-capsules model-card`; smoke and placeholder model cards generated |
| MVP-025 | Codex | In Progress | 2026-04-18 | 2026-05-05 | Added recommendation objective scaffold in `scripts/recommend_next_experiments.py` with weighted success/geometry/uncertainty scoring and config `configs/modeling/family_a_recommendation_v1.json`; placeholder recommendation report generated from 120 synthetic candidates |
| MVP-026 | Codex | In Progress | 2026-04-18 | 2026-05-05 | Added EI/UCB acquisition scoring and method selection (`acquisition.method`) in recommendation workflow; placeholder EI ranking returned top 10 accepted candidates |
| MVP-027 | Codex | In Progress | 2026-04-18 | 2026-05-06 | Added guardrail rejection logic for extrapolation and confidence thresholds; placeholder recommendation guardrails accepted 120/120 synthetic candidates |
| MVP-028 | Codex | In Progress | 2026-04-17 | 2026-04-26 | Added unified CLI entrypoint `interact-capsules` (`src/interact_capsules/cli.py`) with subcommands spanning active MVP workflows; local parser smoke test now covers command registration and `smoke-check` handoff preflight wiring; placeholder handoff + pipeline used the CLI path successfully |
| MVP-029 | Codex | In Progress | 2026-04-17 | 2026-04-27 | Added orchestrated `pipeline` command (ingest -> validate -> split -> baseline -> snapshot), CLI workflow doc `docs/mvp/CLI_WORKFLOW.md`, smoke tests for step order/fail-fast behavior, and bundled smoke-check report generation with optional handoff readiness check; placeholder pipeline completed end-to-end |
| MVP-030 | Codex | In Progress | 2026-04-18 | 2026-05-08 | Added lightweight recommendation UI prototype workflow (`scripts/build_recommendation_ui.py`), CLI `interact-capsules recommend-ui`, docs `docs/mvp/UI_PROTOTYPE_WORKFLOW.md`, smoke UI artifact `smoke_recommendations_ui.html`, and placeholder canonical recommendation UI (`family_a_placeholder_v1_recommendations_ui.html`) |
| MVP-031 | Codex | In Progress | 2026-04-18 | 2026-05-11 | Added `scripts/build_experiment_execution_template.py`, config `configs/validation/family_a_experiment_execution_v1.json`, docs `docs/modeling/EXPERIMENT_EXECUTION_WORKFLOW.md`, CLI `interact-capsules experiment-template`, and smoke artifacts `experiment_execution_template_smoke_v1.{json,md}` |
| MVP-032 | Codex | In Progress | 2026-04-18 | 2026-05-12 | Added `scripts/prepare_prospective_campaign.py`, config `configs/validation/family_a_prospective_campaign_v1.json`, docs `docs/modeling/CAMPAIGN_PREPARATION_WORKFLOW.md`, and CLI `interact-capsules campaign-prepare`; smoke primary-arm campaign plans/log templates generated |
| MVP-033 | Codex | In Progress | 2026-04-18 | 2026-05-13 | Added held-out robustness campaign profiles (`model_guided_robustness`, `baseline_robustness`) in `family_a_prospective_campaign_v1.json`; smoke held-out campaign plans/log templates generated via `campaign-prepare` |
| MVP-034 | Codex | In Progress | 2026-04-18 | 2026-05-14 | Added `scripts/analyze_campaign_outcomes.py`, config `configs/validation/family_a_campaign_analysis_v1.json`, docs `docs/modeling/PROSPECTIVE_VALIDATION_WORKFLOW.md`, CLI `interact-capsules campaign-analyze`, and smoke comparison report (`campaign_analysis_smoke_v1.{json,md}`) |
| MVP-035 | Codex | In Progress | 2026-04-18 | 2026-05-14 | Added `scripts/build_failure_mode_analysis.py`, config `configs/validation/family_a_failure_mode_analysis_v1.json`, docs `docs/modeling/FAILURE_MODE_ANALYSIS_WORKFLOW.md`, CLI `interact-capsules failure-analysis`, and smoke taxonomy report (`failure_mode_analysis_smoke_v1.{json,md}`) |
| MVP-036 | Codex | In Progress | 2026-04-18 | 2026-05-09 | Added reproducibility lock + deterministic eval checks (`scripts/export_environment_lockfile.py`, `scripts/check_deterministic_training.py`), CLI `interact-capsules repro-lock`/`repro-check`, lockfile output `locks/environment.lock.txt`, smoke determinism report (`passed=true`), local smoke tests for lockfile utilities, and placeholder `interact-capsules smoke-check` evidence with handoff preflight (`smoke_check_report_placeholder_v1.json`) |
| MVP-037 | Codex | In Progress | 2026-04-18 | 2026-05-10 | Added documentation bundle for setup/runbook/operator/troubleshooting (`docs/mvp/SETUP_GUIDE.md`, `RUNBOOK.md`, `OPERATOR_QUICKSTART.md`, `TROUBLESHOOTING.md`) plus smoke-check and combined handoff preflight instructions |
| MVP-038 | Codex | In Progress | 2026-04-18 | 2026-05-15 | Added internal handoff session pack generation in `scripts/build_mvp_governance_pack.py`, config `configs/mvp/family_a_mvp_governance_v1.json`, docs `docs/mvp/GOVERNANCE_WORKFLOW.md`, and CLI `interact-capsules mvp-governance`; handoff evidence now includes placeholder handoff, smoke-check, split, baseline, and snapshot artifacts |
| MVP-039 | Codex | In Progress | 2026-04-18 | 2026-05-16 | Added rule-based go/no-go memo generation (G1-G4 checks + blocker thresholds) through `build_mvp_governance_pack.py`; smoke go/no-go memo artifact generated |
| MVP-040 | Codex | In Progress | 2026-04-18 | 2026-05-18 | Added post-MVP roadmap draft generation (go/no-go-conditioned phase templates + carryover task extraction) through `build_mvp_governance_pack.py`; smoke roadmap artifact generated |

## 5) KPI Dashboard

| KPI | Target | Current | Trend | Status | Last Updated |
|---|---|---|---|---|---|
| Family A labeled runs (count) | >= 1200 | 0 | Flat | Not Started | |
| Valid runs after QA (%) | >= 95% | 0% | Flat | Not Started | |
| Segmentation quality (IoU/F1) | Team-defined threshold | N/A | Flat | Not Started | |
| Held-out regime macro-F1 | >= 0.80 | N/A | Flat | Not Started | |
| Calibration quality (ECE/Brier) | Better than baseline and within threshold | N/A | Flat | Not Started | |
| Shell thickness relative error | >=25% better than baseline | N/A | Flat | Not Started | |
| Recommendation hit rate uplift | >=2x heuristic on new campaign | N/A | Flat | Not Started | |
| Experiment reduction vs grid search | >=30% | N/A | Flat | Not Started | |
| End-to-end run time per recommendation cycle | Team target | N/A | Flat | Not Started | |

## 6) Experimental Campaign Tracker

| Campaign ID | Goal | Family | Planned Runs | Completed Runs | Status | Notes |
|---|---|---|---|---|---|---|
| C1 | Baseline operating window map | A | | 0 | Not Started | |
| C2 | Constrained-layer robustness sweep | A | | 0 | Not Started | |
| C3 | Prospective validation (model-guided) | A | | 0 | In Progress | Smoke execution template + sample log added (`campaign_model_guided_smoke_v1.jsonl`); production run count still 0 |
| C4 | Prospective validation (heuristic/grid) | A | | 0 | In Progress | Smoke baseline comparison log added (`campaign_baseline_smoke_v1.jsonl`); production run count still 0 |

## 7) Model Registry Tracker

| Model ID | Data Version | Task | Key Metrics | Calibration | Deployed for Recommendations (Y/N) | Notes |
|---|---|---|---|---|---|---|
| | | Baseline heuristic | | N/A | N | |
| smoke_family_a_segmentation_v1 | synthetic_smoke_model_train_v1 | Segmentation v1 (starter) | Train IoU 1.00/F1 1.00; Val/Test IoU 0.889, F1 0.941 | N/A | N | Pixel-sample threshold baseline; smoke-only, not production representative |
| smoke_family_a_multimodal_v1_rerun | synthetic_smoke_model_train_v1 | Multimodal predictor v1 (prototype) | Test: regime macro-F1 1.00; success F1 1.00; shell thickness MAE 73.35 um; eccentricity MAE 0.00125 | Pending | N | Surrogate-only smoke run; not representative of production performance |
| | | Multimodal predictor v1 | | Pending | N | |
| | | Multimodal predictor v2 | | Pending | N | |

## 8) Risk Register

| Risk ID | Description | Likelihood | Impact | Status | Mitigation | Owner |
|---|---|---|---|---|---|---|
| R1 | Simulation-to-experiment mismatch hurts transfer | Medium | High | Open | Calibration-first transfer + realism envelope checks | |
| R2 | Label inconsistency across annotators/time | Medium | High | Open | Annotation protocol + periodic relabel audits | |
| R3 | Rare failure modes remain under-sampled | High | Medium | Open | Active learning + targeted failure-mode campaigns | |
| R4 | Recommendation over-extrapolates beyond validated domain | Medium | High | Open | Domain guardrails + uncertainty thresholding | |
| R5 | Tool usability gap despite acceptable model metrics | Medium | High | Open | Operator testing loop + CLI/UI simplification | |

## 9) Blockers and Escalations

| Date | Blocker | Affected Tasks | Owner | Escalation Needed | Resolution ETA |
|---|---|---|---|---|---|
| 2026-04-24 | Production Family A raw data handoff not yet available for first canonical pipeline run | MVP-004 to MVP-009; MVP-011 to MVP-014; MVP-018; MVP-022 to MVP-027; MVP-032 to MVP-040 | Schmidt Interact / lab data owner | Confirm raw data location, schema completeness, and first `handoff-check` run window | TBD |

## 10) Decisions Log

| Date | Decision | Reason | Impacted Tasks | Owner |
|---|---|---|---|---|
| | | | | |

## 11) Weekly Update Log

### 2026-04-17 (Week 01)
- Completed: MVP-001, MVP-002, MVP-003, MVP-010 deliverables authored; foundational repository scaffold created.
- In progress: MVP-004 to MVP-009 tooling implemented and smoke-tested on synthetic data.
- At risk: none currently in code; main risk is schema mismatch with historical lab records.
- Blocked: production ingestion pending raw dataset handoff and canonical ID confirmation.
- KPI movement: no production KPI changes yet (tooling readiness improved from 0 to baseline-ready).
- Next-week plan: run inventory + ingestion on actual Family A data, generate first real split artifact, run baseline benchmark report.

### 2026-04-17 (Week 01, Update 2)
- Completed: Canonical run-ID convention documented (`docs/data/RUN_ID_CONVENTIONS.md`) and integrated into inventory/ingestion/validation paths.
- In progress: MVP-004 to MVP-006 now include source-to-canonical ID traceability; still waiting on production raw data.
- At risk: none currently in code.
- Blocked: raw dataset handoff is still required for first production ingestion pass.
- KPI movement: no production KPI movement yet; ingestion readiness for historical IDs improved.
- Next-week plan: execute first production inventory and ingestion run, then freeze `family_a_v1` split and baseline report artifacts.

### 2026-04-17 (Week 01, Update 3)
- Completed: Added simulation planning starter artifacts for MVP-015/016 (`scripts/plan_axisymmetric_sweep.py`, `configs/simulations/family_a_axisymmetric_doe.json`, `docs/modeling/AXISYMMETRIC_SIM_WORKFLOW.md`).
- In progress: MVP-005 ingestion hardened for metadata with missing/partial `asset_paths`; MVP-008 split generation now validates fractions and required grouping fields.
- At risk: simulation plan is currently a DOE planner only; solver execution and synthetic corpus generation (MVP-017) still pending.
- Blocked: first production data pass remains blocked on raw Family A handoff.
- KPI movement: no production KPI movement; readiness improved for first simulation sweep planning and for robust split artifact generation.
- Next-week plan: run first production canonical ingestion + validation, then execute baseline and split artifacts from production data; begin MVP-017 simulation execution adapter.

### 2026-04-17 (Week 01, Update 4)
- Completed: Implemented MVP-017 bootstrap simulation execution path with `scripts/generate_simulation_corpus.py`, `configs/simulations/family_a_axisymmetric_surrogate.json`, and workflow docs updates.
- In progress: MVP-015/016 now tied to executable corpus generation; MVP-018 realism reporting scaffold started via `scripts/report_simulation_realism.py`.
- At risk: generated corpus currently uses surrogate-derived placeholder videos; realism validation quality depends on incoming production experimental data.
- Blocked: production ingestion remains blocked on raw Family A handoff; simulation realism checks depend on that baseline comparison data.
- KPI movement: no production KPI movement; synthetic corpus readiness improved from planner-only to executable smoke-tested pipeline.
- Next-week plan: run full sweep corpus generation, summarize distribution stats for MVP-018 setup, and execute first production ingestion pass once raw data lands.

### 2026-04-17 (Week 01, Update 5)
- Completed: Started MVP-028/029 productization track by adding package CLI entrypoint (`interact-capsules`) and command spec/runbook (`docs/mvp/CLI_WORKFLOW.md`).
- In progress: Pipeline orchestration now available as a single command path (`pipeline` subcommand), pending production run validation against real Family A data.
- At risk: CLI flow can only be validated end-to-end once raw dataset handoff arrives.
- Blocked: production ingest source remains unavailable; cannot yet evidence G4 usability with lab users.
- KPI movement: no production KPI movement; operator workflow readiness improved from script-by-script to unified command surface.
- Next-week plan: execute first real `interact-capsules pipeline` run on Family A handoff, then capture artifacts and turn MVP-028/029 from in-progress to done.

### 2026-04-18 (Week 01, Update 6)
- Completed: Started MVP-019/020 by adding multimodal architecture spec (`docs/modeling/MULTIMODAL_MODEL_ARCHITECTURE.md`), config (`configs/modeling/family_a_multimodal_v1.json`), training pipeline script (`scripts/train_multimodal_model.py`), and CLI command (`interact-capsules model-train`).
- In progress: Model training path now runs on split artifacts and emits model/evaluation/prediction artifacts; awaiting experimental Family A dataset for first production-quality reporting.
- At risk: current smoke validation uses surrogate simulation corpus and will likely overestimate held-out quality relative to real data.
- Blocked: production data handoff is still required for meaningful KPI movement and G2 evidence.
- KPI movement: no production KPI movement; modeling workflow readiness improved from not-started to executable baseline pipeline.
- Next-week plan: run first canonical experimental training/eval pass, produce held-out metrics report, and tighten feature selection against real missingness patterns.

### 2026-04-18 (Week 01, Update 7)
- Completed: Started MVP-021 with synthetic pretraining rerun artifacts (`smoke_family_a_multimodal_v1_pretrain.model.json`, `.eval.json`, `.predictions.jsonl`).
- In progress: Started MVP-023 and MVP-024 by adding uncertainty calibration + model-card generation workflows (`scripts/calibrate_multimodal_uncertainty.py`, `scripts/generate_model_card.py`, `templates/model_card.template.md`) and exposing them through CLI (`model-calibrate`, `model-card`).
- At risk: calibration fit on smoke corpus required fallback from `val` to `train` due limited validation split size; results are not representative of production uncertainty quality.
- Blocked: production Family A handoff is still required to produce meaningful calibration and model-card evidence for G2.
- KPI movement: no production KPI movement; post-training workflow readiness improved from train-only to train+calibrate+card artifact chain.
- Next-week plan: run first production model training pass, generate calibration report/model card from experimental data, and start MVP-025 recommendation objective integration.

### 2026-04-18 (Week 01, Update 8)
- Completed: Started MVP-025/026/027 with recommendation workflow scaffold (`scripts/recommend_next_experiments.py`, `configs/modeling/family_a_recommendation_v1.json`, `docs/modeling/RECOMMENDATION_WORKFLOW.md`) and CLI command `interact-capsules recommend`.
- In progress: Objective composition (success + geometry + uncertainty penalty), EI/UCB acquisition scoring, and guardrail rejection are wired and smoke-ready; awaiting production data for first lab-usable recommendation evidence.
- At risk: current recommendation ranking is calibrated and smoke-validated on synthetic corpus only; may shift materially on production Family A distributions.
- Blocked: production Family A handoff is still required for meaningful prospective recommendation validation.
- KPI movement: no production KPI movement; recommendation engine readiness improved from not-started to executable scaffold.
- Next-week plan: run recommendation reports on first production-trained model, review rejected-candidate guardrails with domain experts, and tune objective/acquisition weights before campaign execution.

### 2026-04-18 (Week 01, Update 9)
- Completed: Started MVP-011/012/013 by adding segmentation training, contour trajectory extraction, and feature QA workflows (`scripts/train_interface_segmentation.py`, `scripts/extract_contours_trajectories.py`, `scripts/build_feature_qa_dashboard.py`) with new configs and CLI commands (`segment-train`, `extract-trajectories`, `feature-qa`).
- In progress: Smoke chain is now executable end-to-end on synthetic corpus with artifacts for segmentation QC (`smoke_family_a_segmentation_v1.qc.json`), contour extraction (`segmentation_features/extraction_report.json`), and QA dashboard (`reports/feature_qa_smoke_v1.{json,md}`); awaiting production masks/contours for meaningful generalization checks.
- At risk: segmentation model is currently a lightweight threshold baseline over pixel samples and is expected to underperform on real camera variability until richer mask supervision and stronger models are integrated.
- Blocked: production Family A mask/contour annotations are not yet available, limiting MVP-011/012/013 evidence to smoke validation.
- KPI movement: segmentation KPI moved from N/A to smoke baseline (Val/Test IoU 0.889, F1 0.941 on starter set), but still not production-representative.
- Next-week plan: run first production mask ingestion pass, execute segmentation/trajectory QA on real runs, and triage top failure modes for MVP-014 correction-loop setup.

### 2026-04-18 (Week 01, Update 10)
- Completed: Started MVP-014 with active correction queue tooling (`scripts/build_label_correction_queue.py`, `configs/modeling/family_a_label_correction_v1.json`, `docs/modeling/LABEL_CORRECTION_WORKFLOW.md`) and CLI command `interact-capsules label-correction`.
- In progress: Started MVP-022 with warm-start fine-tuning support in `scripts/train_multimodal_model.py` (`--init-model`), config `configs/modeling/family_a_multimodal_v1_finetune.json`, docs `docs/modeling/FINETUNING_WORKFLOW.md`, and CLI command `interact-capsules model-finetune`.
- At risk: transfer behavior still validated on synthetic smoke artifacts only; real experimental split characteristics may require tuning `prior_class_weight` and transferred regression-memory caps.
- Blocked: first production experimental Family A split is still required to generate meaningful MVP-022 held-out evidence.
- KPI movement: no production KPI movement; readiness improved from train-only to train+fine-tune and from QA reporting to executable correction-queue planning.
- Next-week plan: run first production fine-tune pass from synthetic pretrain into canonical experimental split and execute first real correction sprint from the generated queue.

### 2026-04-18 (Week 01, Update 11)
- Completed: Started MVP-030 with recommendation review UI prototype (`scripts/build_recommendation_ui.py`, CLI `interact-capsules recommend-ui`, docs `docs/mvp/UI_PROTOTYPE_WORKFLOW.md`) and generated smoke HTML artifact (`smoke_recommendations_ui.html`).
- In progress: Started MVP-036 reproducibility hardening with lockfile and deterministic verification workflows (`interact-capsules repro-lock`, `interact-capsules repro-check`) plus smoke determinism evidence (`determinism_report_smoke_v1.json`, `passed=true`).
- In progress: Started MVP-037 documentation bundle by adding setup guide, runbook, operator quickstart, and troubleshooting docs under `docs/mvp/`.
- At risk: `repro-lock` currently reports missing optional validation dependencies in this local environment (`jsonschema`, `PyYAML`), so strict lock checks will fail until validation extras are installed.
- Blocked: no new external blocker for UI/repro/docs scaffolding; production Family A data handoff remains the main blocker for proving G2/G3/G4 outcomes.
- KPI movement: no production KPI change; tool usability and reproducibility readiness moved from not-started to executable scaffolds with smoke evidence.
- Next-week plan: run first operator walkthrough on production recommendation artifact, install validation extras in the primary runtime for strict lock snapshots, and capture first usability/troubleshooting feedback loop.

### 2026-04-18 (Week 01, Update 12)
- Completed: Started MVP-031 by adding execution-template generation (`scripts/build_experiment_execution_template.py`, `configs/validation/family_a_experiment_execution_v1.json`, docs `docs/modeling/EXPERIMENT_EXECUTION_WORKFLOW.md`, CLI `interact-capsules experiment-template`) and smoke artifacts (`experiment_execution_template_smoke_v1.{json,md}`).
- In progress: Started MVP-034 by adding campaign comparison analysis (`scripts/analyze_campaign_outcomes.py`, `configs/validation/family_a_campaign_analysis_v1.json`, docs `docs/modeling/PROSPECTIVE_VALIDATION_WORKFLOW.md`, CLI `interact-capsules campaign-analyze`) and smoke report (`campaign_analysis_smoke_v1.{json,md}`) from paired model-guided/baseline logs.
- In progress: Started MVP-035 by adding failure taxonomy reporting (`scripts/build_failure_mode_analysis.py`, `configs/validation/family_a_failure_mode_analysis_v1.json`, docs `docs/modeling/FAILURE_MODE_ANALYSIS_WORKFLOW.md`, CLI `interact-capsules failure-analysis`) and smoke report (`failure_mode_analysis_smoke_v1.{json,md}`).
- At risk: prospective analysis outputs are currently based on smoke logs and synthetic predictions; thresholds and decision gates still need calibration on real Family A campaigns.
- Blocked: production campaign execution data is still required to evidence MVP-032/033 and finalize MVP-034/035 acceptance criteria.
- KPI movement: experiment-reduction KPI moved from N/A to smoke-evaluable status (synthetic comparison artifact available), but production KPI remains unchanged.
- Next-week plan: run first production campaign logging pass using execution templates, evaluate model-guided vs baseline reduction on real runs, and feed top failure clusters into correction/fine-tuning backlog.

### 2026-04-18 (Week 01, Update 13)
- Completed: Started MVP-032/033 by adding campaign-preparation tooling (`scripts/prepare_prospective_campaign.py`, `configs/validation/family_a_prospective_campaign_v1.json`, CLI `interact-capsules campaign-prepare`) plus workflow docs (`docs/modeling/CAMPAIGN_PREPARATION_WORKFLOW.md`) and smoke plan/log artifacts for primary + held-out profiles.
- Completed: Started MVP-038/039/040 by adding governance-pack tooling (`scripts/build_mvp_governance_pack.py`, `configs/mvp/family_a_mvp_governance_v1.json`, CLI `interact-capsules mvp-governance`) with generated handoff, go/no-go, and roadmap smoke artifacts.
- In progress: CLI and docs coverage now include campaign preparation + governance workflows (`docs/mvp/CLI_WORKFLOW.md`, `docs/mvp/RUNBOOK.md`, `docs/mvp/GOVERNANCE_WORKFLOW.md`).
- At risk: go/no-go output is currently expected to resolve to `NO_GO` until G1-G4 evidence is produced from production Family A runs.
- Blocked: production Family A campaign data and independent operator execution evidence are still required to close MVP-032/033 and finalize MVP-038/039/040 acceptance criteria.
- KPI movement: no production KPI movement; campaign/governance readiness advanced from not-started to executable scaffold state with smoke artifacts.
- Next-week plan: run `campaign-prepare` against production recommendation outputs, capture first real campaign logs, then regenerate governance pack for live go/no-go review.

### 2026-04-24 (Week 02, Update 1)
- Completed: Added local smoke tests under `tests/` covering CLI command registration, `pipeline` orchestration order/fail-fast behavior, `feature-qa` input validation, and reproducibility lockfile dependency parsing.
- In progress: MVP-028/029 and MVP-036/037 now have rerunnable local verification evidence (`python3 -m unittest discover -s tests`, `python3 -m compileall src scripts tests`, `python3 src/interact_capsules/cli.py --help`).
- At risk: no new code risk identified; strict installed-entrypoint checks still require `pip install -e .` or `PYTHONPATH=src`.
- Blocked: production Family A data handoff remains required for G1-G4 evidence and for closing production acceptance criteria.
- KPI movement: no production KPI movement; productization/reproducibility readiness improved through automated smoke coverage.
- Next-week plan: run the same smoke checks after the first production data handoff, then execute `pipeline` and regenerate split/baseline/snapshot artifacts from real Family A runs.

### 2026-04-24 (Week 02, Update 2)
- Completed: Added `scripts/run_smoke_checks.py` and CLI command `interact-capsules smoke-check` to run unit tests, syntax compilation, and CLI help verification as one operator-facing smoke bundle.
- In progress: MVP-028/029 and MVP-036/037 now produce a JSON smoke evidence report at `data/canonical/family_a/manifests/reports/smoke_check_report.json` in addition to raw terminal checks.
- At risk: no new code risk identified; smoke-check validates local code health, not production Family A acceptance criteria.
- Blocked: production Family A data handoff remains required for G1-G4 evidence and for closing production acceptance criteria.
- KPI movement: no production KPI movement; tool usability readiness improved by reducing local verification to one CLI command.
- Next-week plan: run `interact-capsules smoke-check` before and after the first production data handoff, then attach the generated report to the governance pack evidence list.

### 2026-04-24 (Week 02, Update 3)
- Completed: Added raw handoff preflight tooling (`scripts/check_data_handoff.py`, `interact-capsules handoff-check`) with tests for readiness blocking and `canonicalize` vs `preserve` recommendation behavior; generated smoke evidence at `data_handoff_check_smoke_v1.json` (`ready_run_count=120`, recommended mode `preserve` for the synthetic corpus).
- In progress: MVP-004/005/006 now have a non-mutating production handoff readiness report path before inventory/ingest/pipeline execution.
- At risk: no new code risk identified; readiness still cannot be proven on production Family A data until the raw handoff arrives.
- Blocked: production Family A data handoff remains required for G1-G4 evidence and for closing production acceptance criteria.
- KPI movement: no production KPI movement; ingestion readiness improved by making the current run-ID mode decision explicit and reportable.
- Next-week plan: run `interact-capsules handoff-check` on the first production raw folder, resolve reported source issues, then run `pipeline` with the recommended `--run-id-mode`.

### 2026-04-25 (Week 02, Update 4)
- Completed: Ran a temporary placeholder production-path pass using the synthetic Family A corpus as raw handoff input: strict `handoff-check` passed 120/120 runs with labels + derived features required and recommended `preserve` mode (`data_handoff_check_placeholder_v1.json`).
- Completed: Ran `interact-capsules pipeline` on the placeholder handoff into `data/canonical/family_a` with snapshot `family_a_placeholder_v1`; ingest/validate passed 120/120 runs, split counts were train=83/val=18/test=19, baseline report was generated, and snapshot was written.
- Completed: Ran placeholder modeling/recommendation chain from the canonical placeholder split: `model-train`, `model-calibrate`, `model-card`, `recommend`, and `recommend-ui` produced artifacts for `family_a_placeholder_v1_multimodal`.
- Completed: Ran local verification via `python3 -m unittest discover -s tests` and `interact-capsules smoke-check` with handoff preflight; generated `smoke_check_report_placeholder_v1.json`.
- In progress: Governance evidence config now includes placeholder handoff, smoke-check, split, baseline, snapshot, model, calibration, model-card, recommendation, and UI artifacts so the handoff pack can show the production path exercised without claiming production data acceptance.
- At risk: placeholder baseline metrics are synthetic-only and not representative of Family A production performance.
- Blocked: production Family A data handoff remains required for G1-G4 acceptance evidence and for closing production criteria.
- KPI movement: no production KPI movement; operational readiness improved by proving the handoff-to-snapshot path on a production-shaped placeholder dataset.
- Next-week plan: repeat the same `handoff-check` and `pipeline` flow on the first production raw folder, then regenerate governance outputs from live evidence.

### 2026-04-24 (Week 02, Update 4)
- Completed: Added governance evidence snapshots to `scripts/build_mvp_governance_pack.py`, config `configs/mvp/family_a_mvp_governance_v1.json`, and `docs/mvp/GOVERNANCE_WORKFLOW.md`, with unit coverage in `tests/test_mvp_governance.py`.
- In progress: MVP-038 handoff output now summarizes whether configured smoke-check, handoff readiness, and deterministic training evidence artifacts exist and reports key pass/readiness fields.
- At risk: no new code risk identified; evidence snapshots currently point to local/smoke artifacts until production Family A evidence is generated.
- Blocked: production Family A data handoff remains required for G1-G4 evidence and for closing production acceptance criteria.
- KPI movement: no production KPI movement; governance readiness improved by making local verification evidence visible inside the handoff pack.
- Next-week plan: replace smoke evidence paths with production run artifacts after the first handoff-check/pipeline/model/recommendation cycle, then regenerate the governance pack for operator review.

### 2026-04-24 (Week 02, Update 5)
- Completed: Extended `scripts/run_smoke_checks.py` and `interact-capsules smoke-check` with optional `--handoff-source-dir` support so parser/test/syntax checks and raw handoff readiness can be captured in one evidence bundle.
- In progress: MVP-028/029 and MVP-036/037 now have unit coverage for the combined smoke + handoff preflight command path, plus updated README/CLI/runbook instructions.
- At risk: no new code risk identified; the combined handoff check will still return non-zero until the supplied raw source is production-ready.
- Blocked: production Family A data handoff remains required for G1-G4 evidence and for closing production acceptance criteria.
- KPI movement: no production KPI movement; operator preflight readiness improved by reducing code-health and data-handoff verification to one rerunnable command.
- Next-week plan: run `interact-capsules smoke-check --handoff-source-dir <production_raw>` once the raw folder is available, then attach both generated JSON reports to the governance pack.

### 2026-04-24 (Week 02, Update 6)
- Completed: Extended `scripts/check_data_handoff.py` reports with blocking issue examples and structured `next_actions`, including the exact recommended `interact-capsules pipeline` command when the handoff is ready.
- In progress: MVP-004/005/006 and MVP-038 now have clearer operator handoff evidence: governance snapshots summarize handoff issue counts and the first next-action types from readiness reports.
- At risk: no new code risk identified; generated next actions are still only production-useful after the raw Family A source folder is available.
- Blocked: production Family A data handoff remains required for G1-G4 evidence and for closing production acceptance criteria.
- KPI movement: no production KPI movement; pre-ingest decision readiness improved by turning readiness reports into executable or corrective operator actions.
- Next-week plan: run the combined smoke + handoff preflight on production raw data, follow the report's first `next_actions` command or remediation action, then regenerate the governance pack from production evidence.

### YYYY-MM-DD (Week ##)
- Completed:
- In progress:
- At risk:
- Blocked:
- KPI movement:
- Next-week plan:

### YYYY-MM-DD (Week ##)
- Completed:
- In progress:
- At risk:
- Blocked:
- KPI movement:
- Next-week plan:
