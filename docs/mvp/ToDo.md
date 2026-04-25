# INTERACT-Capsules MVP ToDo

## 1) MVP Definition

### MVP objective
Deliver a lab-usable tool for **Family A (baseline + constrained interfacial layer encapsulation)** that can:
- Predict encapsulation outcome (success/failure + key failure mode)
- Predict key geometry targets (shell thickness band + capsule shape metrics)
- Rank next experimental conditions with uncertainty-aware recommendations
- Run through a reproducible CLI pipeline plus a lightweight UI for experimentalists

### In scope for MVP (must-have)
- Family A data only (single-shell + constrained-layer encapsulation)
- High-speed video ingestion, segmentation, trajectory extraction
- Baseline axisymmetric simulation data generation for pretraining support
- Multimodal predictive model (controls + fluid properties + early-time observables)
- Uncertainty calibration good enough for recommendation ranking
- Recommendation engine for next-best experiments
- Internal documentation and reproducible runbooks

### Out of scope for MVP (post-MVP)
- Full Family B/C production support (multilayer, ferrofluid, hydrogel release)
- Comprehensive 3D magnetic-coupled simulation coverage
- External/public release hardening

## 2) Delivery Gates and Success Criteria

- Gate G1 (Data + baseline ready): curated Family A dataset, schema-validated, baseline heuristic benchmark complete
- Gate G2 (Model usable): held-out Family A macro-F1 >= 0.80 with calibration report
- Gate G3 (Planning value): model-guided search reaches target operating window with >=30% fewer experiments vs grid search
- Gate G4 (Tool usable): lab user can run end-to-end workflow without developer intervention

## 3) Detailed Implementation Backlog

Legend: `P0` critical, `P1` important, `P2` optional for MVP. Status starts as unchecked.

| ID | Priority | Task | Concrete Deliverable | Depends On |
|---|---|---|---|---|
| MVP-001 | P0 | Finalize MVP problem statement and target outputs | 1-page MVP spec with exact inputs/outputs and acceptance thresholds | - |
| MVP-002 | P0 | Define experiment metadata schema | Versioned `run_metadata` schema (JSON/YAML) for fluids, setup, outcomes | MVP-001 |
| MVP-003 | P0 | Define derived feature schema | Standardized fields for trajectories (penetration depth, neck radius, closure time, etc.) | MVP-002 |
| MVP-004 | P0 | Build raw data inventory | Catalog of existing Family A videos and associated records | MVP-002 |
| MVP-005 | P0 | Build ingestion pipeline | Scripted import from raw storage into canonical dataset layout | MVP-004 |
| MVP-006 | P0 | Implement data validation checks | Schema checks, missing-value checks, units consistency checks | MVP-005 |
| MVP-007 | P0 | Implement dataset versioning | Snapshot/version manifest for every training dataset | MVP-005 |
| MVP-008 | P0 | Define train/val/test policy | Random split + held-out fluid-combination split definitions | MVP-006 |
| MVP-009 | P0 | Build baseline heuristic benchmark | Reproducible baseline from empirical criteria/regime-map style rules | MVP-008 |
| MVP-010 | P0 | Annotation guideline for key events | Written protocol for labeling regime/failure modes/time landmarks | MVP-003 |
| MVP-011 | P0 | Train/validate interface segmentation model | First model with QC report on interface mask quality | MVP-010 |
| MVP-012 | P0 | Build contour and trajectory extractor | Deterministic feature extraction from masks and frames | MVP-011 |
| MVP-013 | P0 | Build feature QA dashboards | Automated plots for trajectory sanity checks and outlier detection | MVP-012 |
| MVP-014 | P1 | Active error-correction loop for labels | Workflow for correcting mis-segmentation/mislabels each sprint | MVP-013 |
| MVP-015 | P0 | Stand up axisymmetric simulation workflow | Configurable simulation pipeline for Family A parameter sweeps | MVP-001 |
| MVP-016 | P0 | Define simulation parameter ranges | Controlled DOE grid for velocity, thickness, viscosity/density/tension ratios | MVP-015 |
| MVP-017 | P0 | Generate first simulation corpus | Minimum viable synthetic dataset with metadata parity to experiment data | MVP-016 |
| MVP-018 | P1 | Validate simulation realism envelope | Comparison report: simulated vs experimental observable distributions | MVP-017, MVP-012 |
| MVP-019 | P0 | Design multimodal model architecture | Spec for inputs, encoder fusion, output heads (classification + regression) | MVP-008, MVP-012 |
| MVP-020 | P0 | Implement training pipeline | Reproducible training/eval with config-driven experiments | MVP-019 |
| MVP-021 | P0 | Simulation pretraining run | Best checkpoint from synthetic pretraining + logs | MVP-020, MVP-017 |
| MVP-022 | P0 | Experimental fine-tuning run | Fine-tuned model on Family A with held-out reporting | MVP-021, MVP-008 |
| MVP-023 | P0 | Build uncertainty calibration module | Ensemble/temperature/isotonic calibration and reliability report | MVP-022 |
| MVP-024 | P0 | Define model-card template | Standard model card with scope, limits, and known failure modes | MVP-023 |
| MVP-025 | P0 | Implement recommendation objective | Multi-objective ranking for success probability + geometry target + uncertainty | MVP-023 |
| MVP-026 | P0 | Implement acquisition functions | At least EI/UCB style criteria for next experiment selection | MVP-025 |
| MVP-027 | P0 | Add recommendation guardrails | Reject extrapolation-heavy suggestions outside validated domain | MVP-026 |
| MVP-028 | P0 | CLI command set design | Commands for ingest, train, evaluate, recommend, report | MVP-020, MVP-025 |
| MVP-029 | P0 | Implement CLI workflow | End-to-end CLI with config file support and run artifacts | MVP-028 |
| MVP-030 | P1 | Lightweight UI prototype | Upload inputs, inspect ranked recommendations, view uncertainty + nearest examples | MVP-029 |
| MVP-031 | P0 | Experiment execution template | Standard protocol for running model-recommended experiments in lab | MVP-026 |
| MVP-032 | P0 | Prospective validation campaign #1 | Compare model-guided vs grid/heuristic on one target behavior | MVP-031 |
| MVP-033 | P0 | Prospective validation campaign #2 | Repeat on held-out condition range for robustness | MVP-032 |
| MVP-034 | P0 | Analyze reduction in experimental load | Report on >=30% experiment reduction target | MVP-033 |
| MVP-035 | P0 | Build failure-mode analysis report | Error taxonomy: where/why model fails and confidence behavior | MVP-023, MVP-033 |
| MVP-036 | P0 | Reproducibility hardening | Seed control, environment lockfile, deterministic evaluation scripts | MVP-029 |
| MVP-037 | P0 | Documentation bundle | Setup guide, runbook, troubleshooting, operator quickstart | MVP-029, MVP-035 |
| MVP-038 | P1 | Internal handoff session | Recorded walkthrough + checklist for independent lab use | MVP-037 |
| MVP-039 | P0 | MVP go/no-go review | Decision memo against G1-G4 gates | MVP-034, MVP-037 |
| MVP-040 | P1 | Post-MVP roadmap draft | Prioritized plan for Family B/C extension | MVP-039 |

## 4) Execution Checklist by Workstream

### A. Data and labeling
Current status note (2026-04-25): MVP-004/005/006 now include a raw handoff preflight scaffold (`scripts/check_data_handoff.py`, `interact-capsules handoff-check`) to check metadata/video/schema readiness, recommend `canonicalize` vs `preserve`, show issue examples, and emit structured next actions before production ingest. A temporary placeholder production-path pass has been run from the synthetic Family A corpus: strict handoff readiness passed 120/120 runs, `pipeline` ingested/validated 120/120 runs into `data/canonical/family_a`, and placeholder split/baseline/snapshot artifacts were generated under `family_a_placeholder_v1`. MVP-011/012/013 are started with first executable segmentation/trajectory/QA scaffolds (`scripts/train_interface_segmentation.py`, `scripts/extract_contours_trajectories.py`, `scripts/build_feature_qa_dashboard.py`) plus CLI commands (`interact-capsules segment-train`, `extract-trajectories`, `feature-qa`) and smoke artifacts under `data/simulation/family_a/corpus/smoke_model_train_v1/manifests/{segmentation_models,segmentation_features,reports}`. MVP-014 is now started with an active correction queue scaffold (`scripts/build_label_correction_queue.py`, `configs/modeling/family_a_label_correction_v1.json`, `interact-capsules label-correction`). Keep checklist items open until production data/masks are used and first real Family A correction sprint is completed.
- [x] MVP-002
- [x] MVP-003
- [ ] MVP-004
- [ ] MVP-005
- [ ] MVP-006
- [ ] MVP-007
- [ ] MVP-008
- [x] MVP-010
- [ ] MVP-011
- [ ] MVP-012
- [ ] MVP-013
- [ ] MVP-014

### B. Simulation
Current status note (2026-04-17): MVP-017 synthetic corpus adapter is implemented and smoke-validated; MVP-018 realism report scaffold is started. Keep checklist items open until production-sized corpus and first simulation-vs-experiment comparison report are generated.
- [ ] MVP-015
- [ ] MVP-016
- [ ] MVP-017
- [ ] MVP-018

### C. Modeling and uncertainty
Current status note (2026-04-25): MVP-019/020 are started and smoke-validated (`docs/modeling/MULTIMODAL_MODEL_ARCHITECTURE.md`, `scripts/train_multimodal_model.py`, `configs/modeling/family_a_multimodal_v1.json`, `interact-capsules model-train`), with an additional placeholder canonical model artifact generated from `family_a_placeholder_v1` (`family_a_placeholder_v1_multimodal.*`). MVP-021 now has a synthetic pretraining artifact (`smoke_family_a_multimodal_v1_pretrain.*`). MVP-022 is now started with fine-tuning scaffolding (`configs/modeling/family_a_multimodal_v1_finetune.json`, `docs/modeling/FINETUNING_WORKFLOW.md`, `interact-capsules model-finetune`, and `train_multimodal_model.py --init-model`). MVP-023 calibration scaffolding is added (`scripts/calibrate_multimodal_uncertainty.py`, `configs/modeling/family_a_uncertainty_calibration_v1.json`, `interact-capsules model-calibrate`) and now has a placeholder canonical calibration artifact. MVP-024 model-card scaffolding is added (`templates/model_card.template.md`, `scripts/generate_model_card.py`, `interact-capsules model-card`) and now has a placeholder canonical model card. Keep checklist items open until production Family A runs are used for held-out reporting.
- [ ] MVP-019
- [ ] MVP-020
- [ ] MVP-021
- [ ] MVP-022
- [ ] MVP-023
- [ ] MVP-024

### D. Recommendation engine
Current status note (2026-04-25): MVP-025/026/027 are started with a first recommendation workflow scaffold (`scripts/recommend_next_experiments.py`, `configs/modeling/family_a_recommendation_v1.json`, `interact-capsules recommend`). EI/UCB scoring and guardrail rejection are wired; a placeholder canonical recommendation report has been generated from 120 synthetic candidates with 120 accepted and top 10 returned. Keep checklist items open until first production recommendation report is generated on experimental Family A data and reviewed with lab operators.
- [ ] MVP-025
- [ ] MVP-026
- [ ] MVP-027

### E. Productization
Current status note (2026-04-25): MVP-028/029 remain in progress and have now exercised the production-path CLI on placeholder Family A data (`handoff-check` -> `pipeline` -> split/baseline/snapshot). MVP-030 is now started with a lightweight recommendation review UI generator (`scripts/build_recommendation_ui.py`, `interact-capsules recommend-ui`, `docs/mvp/UI_PROTOTYPE_WORKFLOW.md`) and has a placeholder canonical recommendation UI generated from `family_a_placeholder_v1_multimodal.recommendations.json`. MVP-036 reproducibility hardening is now started with lockfile + deterministic check workflows (`scripts/export_environment_lockfile.py`, `scripts/check_deterministic_training.py`, `interact-capsules repro-lock`, `interact-capsules repro-check`, `docs/mvp/REPRODUCIBILITY_WORKFLOW.md`), smoke determinism evidence (`determinism_report_smoke_v1.json`), local smoke tests (`tests/`) for CLI orchestration and lockfile utilities, and placeholder smoke-check evidence with handoff preflight (`smoke_check_report_placeholder_v1.json`). MVP-037 documentation bundle is now started with setup/runbook/quickstart/troubleshooting docs under `docs/mvp/`, now including smoke-check instructions and handoff next-action usage. Local verification is bundled behind `scripts/run_smoke_checks.py` and `interact-capsules smoke-check`, which writes a smoke evidence report for parser/test/syntax checks and can optionally append raw handoff preflight evidence with `--handoff-source-dir`. MVP-038 is now started with a governance/handoff pack scaffold (`scripts/build_mvp_governance_pack.py`, `configs/mvp/family_a_mvp_governance_v1.json`, `interact-capsules mvp-governance`, `docs/mvp/GOVERNANCE_WORKFLOW.md`) and evidence snapshots now include placeholder handoff, smoke-check, split, baseline, snapshot, model, calibration, model-card, recommendation, and UI artifacts. Keep checklist items open until production Family A operator validation and handoff evidence are captured.
- [ ] MVP-028
- [ ] MVP-029
- [ ] MVP-030
- [ ] MVP-036
- [ ] MVP-037
- [ ] MVP-038

### F. Prospective validation
Current status note (2026-04-18): MVP-031 is now started with an execution-template generator (`scripts/build_experiment_execution_template.py`, `configs/validation/family_a_experiment_execution_v1.json`, `interact-capsules experiment-template`, `docs/modeling/EXPERIMENT_EXECUTION_WORKFLOW.md`) and smoke artifacts (`experiment_execution_template_smoke_v1.{json,md}`). MVP-032/033 are now started with campaign-preparation scaffolding (`scripts/prepare_prospective_campaign.py`, `configs/validation/family_a_prospective_campaign_v1.json`, `interact-capsules campaign-prepare`, `docs/modeling/CAMPAIGN_PREPARATION_WORKFLOW.md`) and smoke campaign plans/log templates for primary + held-out profiles. MVP-034 is now started with campaign comparison tooling (`scripts/analyze_campaign_outcomes.py`, `configs/validation/family_a_campaign_analysis_v1.json`, `interact-capsules campaign-analyze`, `docs/modeling/PROSPECTIVE_VALIDATION_WORKFLOW.md`) and smoke logs/report (`campaign_{model_guided,baseline}_smoke_v1.jsonl`, `campaign_analysis_smoke_v1.{json,md}`). MVP-035 is now started with failure taxonomy reporting (`scripts/build_failure_mode_analysis.py`, `configs/validation/family_a_failure_mode_analysis_v1.json`, `interact-capsules failure-analysis`, `docs/modeling/FAILURE_MODE_ANALYSIS_WORKFLOW.md`) and smoke artifacts (`failure_mode_analysis_smoke_v1.{json,md}`). MVP-039/040 are now started with governance memo/roadmap generation scaffolds (`scripts/build_mvp_governance_pack.py`, `configs/mvp/family_a_mvp_governance_v1.json`, `interact-capsules mvp-governance`) and smoke memo outputs. Keep checklist items open until first production Family A campaign data is analyzed and governance review is run against production evidence.
- [ ] MVP-031
- [ ] MVP-032
- [ ] MVP-033
- [ ] MVP-034
- [ ] MVP-035
- [ ] MVP-039
- [ ] MVP-040

## 5) Suggested 24-Week MVP Timeline

- Weeks 1-4: MVP-001 to MVP-010
- Weeks 5-8: MVP-011 to MVP-018
- Weeks 9-12: MVP-019 to MVP-024
- Weeks 13-16: MVP-025 to MVP-030
- Weeks 17-22: MVP-031 to MVP-035
- Weeks 23-24: MVP-036 to MVP-040

## 6) Critical Risks to Watch During MVP

- Simulation-to-experiment mismatch undermines transfer performance
- Label quality drift across annotators/time
- Data imbalance for rare but important failure modes
- Recommendation engine over-explores outside validated parameter envelope
- Tooling friction prevents independent lab use even if model quality is acceptable
