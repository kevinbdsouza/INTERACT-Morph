# INTERACT-Capsules

INTERACT-Capsules is a data, simulation, modeling, and recommendation toolkit for liquid-liquid encapsulation experiments. The initial project scope is Family A encapsulation: baseline single-shell behavior and constrained interfacial-layer encapsulation.

Project website: [interactcapsuleswebsite.pages.dev](https://interactcapsuleswebsite.pages.dev/)

The repository is organized around a reproducible lab workflow:

1. Curate raw high-speed-video experiments into a canonical dataset.
2. Validate metadata, labels, derived features, units, and run identifiers.
3. Generate or compare axisymmetric simulation corpora.
4. Train multimodal predictors from controls, fluid properties, and early-time observables.
5. Calibrate uncertainty and publish model cards.
6. Rank next experiments with acquisition scoring and domain guardrails.
7. Produce operator-facing execution templates, campaign analysis, failure analysis, and handoff reports.

Implementation status, open work, and sprint notes live in [docs/mvp/Progress_Tracking.md](docs/mvp/Progress_Tracking.md) and [docs/mvp/ToDo.md](docs/mvp/ToDo.md). This README is intended as the functional overview and entry point.

## Core Functionality

### Data Ingestion And Validation

The data layer turns raw run folders into canonical Family A datasets.

- Raw handoff preflight checks for metadata, video files, label files, derived-feature files, schema readiness, and run-ID mode recommendations.
- Raw inventory generation for run discovery and source traceability.
- Canonical ingestion with `source_run_id` preservation and deterministic run-ID canonicalization when needed.
- Dataset validation against versioned run metadata and derived-feature schemas.
- Train/validation/test split generation with grouped held-out fluid-combination policies.
- Dataset snapshot manifests for reproducible model and analysis runs.

Primary commands:

```bash
interact-capsules handoff-check
interact-capsules inventory
interact-capsules ingest
interact-capsules validate
interact-capsules split
interact-capsules snapshot
interact-capsules pipeline
```

Key references:

- [Data architecture](docs/data/DATA_ARCHITECTURE.md)
- [Run ID conventions](docs/data/RUN_ID_CONVENTIONS.md)
- [Split policy](docs/data/SPLIT_POLICY.md)
- [Run metadata schema](schemas/run_metadata.schema.json)
- [Derived features schema](schemas/derived_features.schema.json)

### Segmentation, Trajectories, And Label QA

The segmentation and QA workflows convert interface observations into structured time-series features and correction queues.

- Lightweight interface segmentation baseline from frame-level pixel samples.
- Contour and trajectory extraction from mask or contour observations.
- Derived-feature QA reports for sanity checks, missingness, and outlier detection.
- Active correction queue generation for label, mask, and feature triage.
- Annotation guidance for regime labels, failure modes, and key event landmarks.

Primary commands:

```bash
interact-capsules segment-train
interact-capsules extract-trajectories
interact-capsules feature-qa
interact-capsules label-correction
```

Key references:

- [Annotation guidelines](docs/data/ANNOTATION_GUIDELINES.md)
- [Segmentation and trajectory workflow](docs/modeling/SEGMENTATION_TRAJECTORY_WORKFLOW.md)
- [Label correction workflow](docs/modeling/LABEL_CORRECTION_WORKFLOW.md)

### Simulation Workflows

The simulation layer supports Family A design-of-experiments planning, synthetic corpus generation, and realism comparison.

- Axisymmetric sweep planning over impact velocity, geometry, density, viscosity, interfacial tension, and layer thickness.
- Synthetic corpus generation with metadata parity to experimental runs.
- Simulation-vs-experiment realism reports for observable distribution comparison.
- Config-driven simulation ranges and surrogate generation settings.

Primary commands:

```bash
interact-capsules sim-plan
interact-capsules sim-generate
interact-capsules sim-realism
```

Key references:

- [Axisymmetric simulation workflow](docs/modeling/AXISYMMETRIC_SIM_WORKFLOW.md)
- [Simulation DOE config](configs/simulations/family_a_axisymmetric_doe.json)
- [Surrogate config](configs/simulations/family_a_axisymmetric_surrogate.json)

### Baseline And Multimodal Modeling

The modeling layer trains and evaluates predictors for encapsulation outcomes, failure modes, and geometry targets.

- Dimensionless-number baseline benchmark for regime and success prediction.
- Config-driven multimodal model training from run metadata and derived features.
- Warm-start fine-tuning from synthetic pretraining artifacts into experimental Family A data.
- Held-out evaluation with classification and regression metrics.
- Standardized model-card generation for scope, data, metrics, calibration, and limitations.

Primary commands:

```bash
interact-capsules baseline
interact-capsules model-train
interact-capsules model-finetune
interact-capsules model-card
```

Key references:

- [Baseline benchmark](docs/modeling/BASELINE_BENCHMARK.md)
- [Multimodal model architecture](docs/modeling/MULTIMODAL_MODEL_ARCHITECTURE.md)
- [Model training workflow](docs/modeling/MODEL_TRAINING_WORKFLOW.md)
- [Fine-tuning workflow](docs/modeling/FINETUNING_WORKFLOW.md)
- [Model card workflow](docs/modeling/MODEL_CARD_WORKFLOW.md)
- [Model card template](templates/model_card.template.md)

### Uncertainty Calibration

The calibration workflow converts model scores into reviewable confidence evidence.

- Temperature scaling for success probability and regime top-1 correctness.
- Optional isotonic calibration when enough fit rows are available.
- Reliability metrics and calibrated prediction artifacts.
- Calibration outputs that feed recommendations and model cards.

Primary command:

```bash
interact-capsules model-calibrate
```

Key reference:

- [Uncertainty calibration workflow](docs/modeling/UNCERTAINTY_CALIBRATION_WORKFLOW.md)

### Recommendation Engine

The recommendation workflow ranks candidate experiments for lab review.

- Multi-objective scoring over success probability, geometry targets, and uncertainty penalties.
- Expected-improvement and upper-confidence-bound acquisition options.
- Guardrails for extrapolation, distance from training support, and minimum success probability.
- Accepted and rejected candidate reporting with nearest-support diagnostics.
- Standalone HTML recommendation review UI for operators.

Primary commands:

```bash
interact-capsules recommend
interact-capsules recommend-ui
```

Key references:

- [Recommendation workflow](docs/modeling/RECOMMENDATION_WORKFLOW.md)
- [Recommendation config](configs/modeling/family_a_recommendation_v1.json)
- [UI prototype workflow](docs/mvp/UI_PROTOTYPE_WORKFLOW.md)

### Experiment Execution And Prospective Validation

The validation layer turns ranked recommendations into campaign plans and post-run analysis.

- Experiment execution templates with run conditions, operator checklist fields, and logging structure.
- Prospective campaign preparation for model-guided and baseline arms.
- Campaign comparison for hit rate, target-window discovery, and experimental-load reduction.
- Failure-mode analysis for prediction errors, confidence behavior, and recurring issue clusters.

Primary commands:

```bash
interact-capsules experiment-template
interact-capsules campaign-prepare
interact-capsules campaign-analyze
interact-capsules failure-analysis
```

Key references:

- [Experiment execution workflow](docs/modeling/EXPERIMENT_EXECUTION_WORKFLOW.md)
- [Campaign preparation workflow](docs/modeling/CAMPAIGN_PREPARATION_WORKFLOW.md)
- [Prospective validation workflow](docs/modeling/PROSPECTIVE_VALIDATION_WORKFLOW.md)
- [Failure-mode analysis workflow](docs/modeling/FAILURE_MODE_ANALYSIS_WORKFLOW.md)

### Reproducibility And Governance

The operational layer is designed for repeatable runs and internal handoff.

- Environment lockfile export from project dependencies and optional validation extras.
- Deterministic training checks for repeated model runs.
- Smoke-check bundles for tests, syntax compilation, CLI help, and optional raw handoff preflight.
- Internal governance pack generation for handoff materials, go/no-go memos, and roadmap drafts.

Primary commands:

```bash
interact-capsules repro-lock
interact-capsules repro-check
interact-capsules smoke-check
interact-capsules mvp-governance
```

Key references:

- [Reproducibility workflow](docs/mvp/REPRODUCIBILITY_WORKFLOW.md)
- [Governance workflow](docs/mvp/GOVERNANCE_WORKFLOW.md)
- [Runbook](docs/mvp/RUNBOOK.md)
- [Operator quickstart](docs/mvp/OPERATOR_QUICKSTART.md)
- [Troubleshooting guide](docs/mvp/TROUBLESHOOTING.md)

## Repository Layout

```text
configs/
  baselines/      Baseline benchmark settings
  modeling/       Model, segmentation, calibration, and recommendation configs
  mvp/            Governance pack config
  simulations/    Axisymmetric DOE and surrogate configs
  splits/         Dataset split policy configs
  validation/     Campaign, execution-template, and failure-analysis configs
data/
  raw/            Local raw data handoff location
  canonical/      Canonical datasets, manifests, reports, and model artifacts
  simulation/     Simulation corpora and smoke artifacts
docs/
  data/           Data contracts, annotation policy, and run-ID guidance
  modeling/       Modeling, simulation, recommendation, and validation workflows
  mvp/            Operator docs, runbooks, tracking, and governance workflow
schemas/          JSON schemas for canonical records
scripts/          Workflow scripts used by the CLI
src/              Python package and CLI entrypoint
templates/        Metadata, label, and model-card templates
tests/            Local smoke and workflow tests
```

## Setup

Create a local environment and install the CLI:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e .
```

Install optional schema and YAML validation dependencies:

```bash
pip install -e ".[validation]"
```

Show the available command surface:

```bash
interact-capsules --help
```

If the package is not installed yet, the CLI can also be invoked directly:

```bash
python3 src/interact_capsules/cli.py --help
```

## Typical End-To-End Flow

### 1. Check A Raw Handoff

```bash
interact-capsules handoff-check \
  --source-dir data/raw \
  --family A \
  --output data/canonical/family_a/manifests/reports/data_handoff_check.json \
  --require-labels \
  --require-derived
```

Review the generated report before ingesting. It includes readiness counts, example issues, a recommended run-ID mode, and the exact next command to run when the handoff is ready.

### 2. Run The Canonical Data Pipeline

```bash
interact-capsules pipeline \
  --source-dir data/raw \
  --dataset-root data/canonical/family_a \
  --family A \
  --run-id-mode canonicalize \
  --snapshot-name family_a_v1 \
  --require-labels \
  --require-derived
```

The pipeline runs ingestion, validation, split generation, baseline benchmarking, and dataset snapshotting.

### 3. Train, Calibrate, And Document A Model

```bash
interact-capsules model-train \
  --dataset-root data/canonical/family_a \
  --split data/canonical/family_a/manifests/splits/family_a_v1.json \
  --output-dir data/canonical/family_a/manifests/models \
  --model-id family_a_multimodal_v1

interact-capsules model-calibrate \
  --predictions data/canonical/family_a/manifests/models/family_a_multimodal_v1.predictions.jsonl \
  --output data/canonical/family_a/manifests/models/family_a_multimodal_v1.calibration.json \
  --calibrated-predictions-output data/canonical/family_a/manifests/models/family_a_multimodal_v1.calibrated_predictions.jsonl

interact-capsules model-card \
  --model-artifact data/canonical/family_a/manifests/models/family_a_multimodal_v1.model.json \
  --eval-artifact data/canonical/family_a/manifests/models/family_a_multimodal_v1.eval.json \
  --calibration-artifact data/canonical/family_a/manifests/models/family_a_multimodal_v1.calibration.json \
  --output data/canonical/family_a/manifests/model_cards/family_a_multimodal_v1.md
```

### 4. Rank Candidate Experiments

```bash
interact-capsules recommend \
  --model-artifact data/canonical/family_a/manifests/models/family_a_multimodal_v1.model.json \
  --calibration-artifact data/canonical/family_a/manifests/models/family_a_multimodal_v1.calibration.json \
  --candidates data/simulation/family_a/manifests/axisymmetric_sweep_v1.jsonl \
  --output data/canonical/family_a/manifests/recommendations/family_a_multimodal_v1.recommendations.json

interact-capsules recommend-ui \
  --recommendation-report data/canonical/family_a/manifests/recommendations/family_a_multimodal_v1.recommendations.json \
  --output-html data/canonical/family_a/manifests/recommendations/family_a_multimodal_v1.recommendations.html
```

### 5. Prepare And Analyze Validation Campaigns

```bash
interact-capsules experiment-template \
  --recommendation-report data/canonical/family_a/manifests/recommendations/family_a_multimodal_v1.recommendations.json \
  --output data/canonical/family_a/manifests/reports/experiment_execution_template.json \
  --markdown-output data/canonical/family_a/manifests/reports/experiment_execution_template.md

interact-capsules campaign-prepare \
  --runs-input data/canonical/family_a/manifests/reports/experiment_execution_template.json \
  --campaign-profile model_guided_primary \
  --output data/canonical/family_a/manifests/reports/campaign_prepared_model_guided_primary.json \
  --campaign-log-output data/canonical/family_a/manifests/reports/campaign_model_guided_primary.jsonl

interact-capsules campaign-analyze \
  --model-guided-log data/canonical/family_a/manifests/reports/campaign_model_guided_primary.jsonl \
  --baseline-log data/canonical/family_a/manifests/reports/campaign_baseline_primary.jsonl \
  --output data/canonical/family_a/manifests/reports/campaign_analysis.json \
  --markdown-output data/canonical/family_a/manifests/reports/campaign_analysis.md
```

## Data Contracts

Canonical run folders are expected to contain:

```text
runs/<run_id>/
  metadata.json
  labels.json
  derived_features.json
  video.mp4
```

The metadata schema captures experiment setup, fluid properties, controls, outcomes, asset paths, and quality flags. The derived-feature schema captures trajectory summaries, geometry metrics, and event timings.

Template files:

- [run_metadata.template.json](templates/run_metadata.template.json)
- [labels.template.json](templates/labels.template.json)

## Local Verification

Run unit tests and syntax checks:

```bash
python3 -m unittest discover -s tests
python3 -m compileall src scripts tests
```

Generate a single smoke-check report:

```bash
interact-capsules smoke-check \
  --output data/canonical/family_a/manifests/reports/smoke_check_report.json
```

Include handoff readiness in the smoke bundle when raw data is available:

```bash
interact-capsules smoke-check \
  --output data/canonical/family_a/manifests/reports/smoke_check_report.json \
  --handoff-source-dir data/raw \
  --handoff-output data/canonical/family_a/manifests/reports/data_handoff_check.json \
  --handoff-require-labels \
  --handoff-require-derived
```

## Documentation Index

Start here for operators:

- [Setup guide](docs/mvp/SETUP_GUIDE.md)
- [Runbook](docs/mvp/RUNBOOK.md)
- [Operator quickstart](docs/mvp/OPERATOR_QUICKSTART.md)
- [Troubleshooting](docs/mvp/TROUBLESHOOTING.md)
- [CLI workflow](docs/mvp/CLI_WORKFLOW.md)

Use these for technical details:

- [MVP spec](docs/mvp/MVP_SPEC.md)
- [Data architecture](docs/data/DATA_ARCHITECTURE.md)
- [Model training workflow](docs/modeling/MODEL_TRAINING_WORKFLOW.md)
- [Recommendation workflow](docs/modeling/RECOMMENDATION_WORKFLOW.md)
- [Prospective validation workflow](docs/modeling/PROSPECTIVE_VALIDATION_WORKFLOW.md)

Use these for tracking only:

- [Progress tracking](docs/mvp/Progress_Tracking.md)
- [ToDo backlog](docs/mvp/ToDo.md)
