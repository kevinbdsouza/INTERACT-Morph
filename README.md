# INTERACT-Morph

INTERACT-Morph is a data, video-processing, modeling, and inverse-recommendation toolkit for impact-driven liquid-liquid encapsulation. The revised scope is morphology-first: given a target liquid-shell morphology, the tool should recommend experimentally controllable operating conditions with uncertainty, nearby prior evidence, and failure-mode warnings.

We are building a lab-facing software stack for AI-guided inverse morphology design in non-equilibrium four-fluid encapsulation systems.

Implementation status, open work, and sprint notes live in [docs/mvp/Progress_Tracking.md](docs/mvp/Progress_Tracking.md), [docs/mvp/ToDo.md](docs/mvp/ToDo.md), and [docs/mvp/MVP_SPEC.md](docs/mvp/MVP_SPEC.md).

## Scope

INTERACT-Morph focuses on the material state created by a core drop, shell-forming interfacial layer, host bath, and surrounding air during impact-driven wrapping. It treats morphology as the actionable design target rather than treating wrapped/unwrapped outcome as the endpoint.

Primary morphology outputs:

- Wrapped/unwrapped outcome and penetration/trapping/confinement-failure mode
- Mean shell thickness and shell-thickness nonuniformity
- Crown index, trapped-air fraction, encapsulated volume, and core offset
- Layer sequence for selected multilayer routes
- Calibrated uncertainty, abstention, out-of-domain score, and failure-mode warnings

Primary controllable inputs:

- Impact height or velocity
- Shell volume and effective interfacial-layer thickness
- Material descriptors and nondimensional groups
- Conventional versus circular-loop-assisted confinement
- Limited single-layer versus multilayer route choice

## Core Workflow

1. Curate existing and new high-speed encapsulation experiments into canonical datasets.
2. Validate metadata, labels, derived features, units, and run identifiers.
3. Segment videos and extract dynamic interfacial observables from early-time motion.
4. Benchmark thermodynamic, regime-map, and tabular baselines.
5. Train physics-aware video-to-morphology models.
6. Calibrate uncertainty and document supported operating domains.
7. Rank inverse-design candidates with constraints, uncertainty, nearest examples, and failure warnings.
8. Prepare prospective target-morphology campaigns and compare against grid or expert heuristic search.
9. Publish dataset card, model card, validation report, failure-mode map, and operator workflows.

## Implemented Capabilities

The current codebase already contains executable scaffolding for the full lab workflow:

- Raw handoff checks, inventory, ingestion, validation, split generation, dataset snapshots, and baseline benchmarking
- Interface segmentation starter model, contour/trajectory extraction, feature QA, and label-correction queues
- Axisymmetric DOE planning, surrogate synthetic corpus generation, and simulation-realism reporting
- Multimodal model training, synthetic pretraining, warm-start fine-tuning, calibration, and model-card generation
- Recommendation scoring with acquisition functions, guardrails, and static HTML review UI
- Experiment execution templates, prospective campaign preparation, campaign analysis, and failure-mode analysis
- Environment lockfiles, deterministic training checks, smoke-check bundles, and governance pack generation

Most workflows have been smoke-tested on synthetic placeholder data. Production acceptance still depends on ingesting the real experimental archive and prospective campaign outcomes.

## Command Surface

Data and validation:

```bash
interact-morph handoff-check
interact-morph inventory
interact-morph ingest
interact-morph validate
interact-morph split
interact-morph snapshot
interact-morph dataset-card
interact-morph pipeline
```

Video observables and labeling:

```bash
interact-morph segment-train
interact-morph extract-trajectories
interact-morph feature-qa
interact-morph label-correction
```

Modeling and inverse design:

```bash
interact-morph baseline
interact-morph model-train
interact-morph model-finetune
interact-morph model-calibrate
interact-morph model-card
interact-morph recommend
interact-morph recommend-ui
```

Campaigns and governance:

```bash
interact-morph experiment-template
interact-morph campaign-prepare
interact-morph campaign-analyze
interact-morph failure-analysis
interact-morph repro-lock
interact-morph repro-check
interact-morph smoke-check
interact-morph mvp-governance
```

## Repository Layout

```text
configs/
  baselines/      Baseline benchmark settings
  modeling/       Model, segmentation, calibration, and recommendation configs
  mvp/            Governance pack config
  simulations/    DOE and surrogate configs
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

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e .
pip install -e ".[validation]"
interact-morph --help
```

If the package is not installed yet:

```bash
python3 src/interact_morph/cli.py --help
```

## Typical End-To-End Flow

Check a raw experimental handoff:

```bash
interact-morph handoff-check \
  --source-dir data/raw \
  --family A \
  --output data/canonical/family_a/manifests/reports/data_handoff_check.json \
  --require-labels \
  --require-derived
```

Run the canonical data pipeline:

```bash
interact-morph pipeline \
  --source-dir data/raw \
  --dataset-root data/canonical/family_a \
  --family A \
  --run-id-mode canonicalize \
  --snapshot-name interact_morph_v1 \
  --require-labels \
  --require-derived
```

Train, calibrate, and document a model:

```bash
interact-morph model-train \
  --dataset-root data/canonical/family_a \
  --split data/canonical/family_a/manifests/splits/interact_morph_v1.json \
  --output-dir data/canonical/family_a/manifests/models \
  --model-id interact_morph_multimodal_v1

interact-morph model-calibrate \
  --predictions data/canonical/family_a/manifests/models/interact_morph_multimodal_v1.predictions.jsonl \
  --output data/canonical/family_a/manifests/models/interact_morph_multimodal_v1.calibration.json \
  --calibrated-predictions-output data/canonical/family_a/manifests/models/interact_morph_multimodal_v1.calibrated_predictions.jsonl

interact-morph model-card \
  --model-artifact data/canonical/family_a/manifests/models/interact_morph_multimodal_v1.model.json \
  --eval-artifact data/canonical/family_a/manifests/models/interact_morph_multimodal_v1.eval.json \
  --calibration-artifact data/canonical/family_a/manifests/models/interact_morph_multimodal_v1.calibration.json \
  --output data/canonical/family_a/manifests/model_cards/interact_morph_multimodal_v1.md
```

Rank target-morphology candidates:

```bash
interact-morph recommend \
  --model-artifact data/canonical/family_a/manifests/models/interact_morph_multimodal_v1.model.json \
  --calibration-artifact data/canonical/family_a/manifests/models/interact_morph_multimodal_v1.calibration.json \
  --candidates data/simulation/family_a/manifests/axisymmetric_sweep_v1.jsonl \
  --output data/canonical/family_a/manifests/recommendations/interact_morph_multimodal_v1.recommendations.json

interact-morph recommend-ui \
  --recommendation-report data/canonical/family_a/manifests/recommendations/interact_morph_multimodal_v1.recommendations.json \
  --output-html data/canonical/family_a/manifests/recommendations/interact_morph_multimodal_v1.recommendations.html
```

Prepare and analyze prospective campaigns:

```bash
interact-morph experiment-template \
  --recommendation-report data/canonical/family_a/manifests/recommendations/interact_morph_multimodal_v1.recommendations.json \
  --output data/canonical/family_a/manifests/reports/experiment_execution_template.json \
  --markdown-output data/canonical/family_a/manifests/reports/experiment_execution_template.md

interact-morph campaign-prepare \
  --runs-input data/canonical/family_a/manifests/reports/experiment_execution_template.json \
  --campaign-profile model_guided_primary \
  --output data/canonical/family_a/manifests/reports/campaign_prepared_model_guided_primary.json \
  --campaign-log-output data/canonical/family_a/manifests/reports/campaign_model_guided_primary.jsonl

interact-morph campaign-analyze \
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

The metadata schema captures experiment setup, fluid properties, controls, outcomes, asset paths, and quality flags. The derived-feature schema captures trajectory summaries, event timings, dynamic observables, and morphology metrics.

Template files:

- [run_metadata.template.json](templates/run_metadata.template.json)
- [labels.template.json](templates/labels.template.json)

## Local Verification

```bash
python3 -m unittest discover -s tests
python3 -m compileall src scripts tests
interact-morph smoke-check \
  --output data/canonical/family_a/manifests/reports/smoke_check_report.json
```

## Documentation Index

Operator docs:

- [Setup guide](docs/mvp/SETUP_GUIDE.md)
- [Runbook](docs/mvp/RUNBOOK.md)
- [Operator quickstart](docs/mvp/OPERATOR_QUICKSTART.md)
- [Troubleshooting](docs/mvp/TROUBLESHOOTING.md)
- [CLI workflow](docs/mvp/CLI_WORKFLOW.md)

Technical docs:

- [MVP spec](docs/mvp/MVP_SPEC.md)
- [Data architecture](docs/data/DATA_ARCHITECTURE.md)
- [Model training workflow](docs/modeling/MODEL_TRAINING_WORKFLOW.md)
- [Recommendation workflow](docs/modeling/RECOMMENDATION_WORKFLOW.md)
- [Prospective validation workflow](docs/modeling/PROSPECTIVE_VALIDATION_WORKFLOW.md)

Tracking:

- [Progress tracking](docs/mvp/Progress_Tracking.md)
- [ToDo backlog](docs/mvp/ToDo.md)
