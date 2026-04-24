# INTERACT-Capsules
AI for Interfacial Matter through Multiscale Prediction of Liquid-Liquid Encapsulation and Release.

## What is implemented now
This repository now includes the **MVP foundation layer** for the first task set:
- MVP spec and scope (`docs/mvp/MVP_SPEC.md`)
- Data contracts and annotation protocol (`docs/data/`)
- Versioned schemas (`schemas/`)
- Data ingestion, validation, inventory, split generation, and dataset snapshot scripts (`scripts/`)
- Baseline dimensionless-number benchmark scaffold (`scripts/baseline_regime_map.py`)
- Axisymmetric simulation sweep planning + synthetic corpus generation (`scripts/plan_axisymmetric_sweep.py`, `scripts/generate_simulation_corpus.py`)
- Config-driven multimodal model training/evaluation baseline (`scripts/train_multimodal_model.py`)
- Uncertainty calibration workflow (`scripts/calibrate_multimodal_uncertainty.py`)
- Standardized model-card generation (`scripts/generate_model_card.py`, `templates/model_card.template.md`)
- Recommendation ranking workflow with objective/acquisition/guardrails (`scripts/recommend_next_experiments.py`)
- Experiment execution template generation from recommendations (`scripts/build_experiment_execution_template.py`)
- Prospective campaign preparation workflow for primary and held-out robustness arms (`scripts/prepare_prospective_campaign.py`)
- Prospective campaign comparison and reduction analysis (`scripts/analyze_campaign_outcomes.py`)
- Failure-mode taxonomy reporting from prediction artifacts (`scripts/build_failure_mode_analysis.py`)
- Lightweight recommendation review UI builder (`scripts/build_recommendation_ui.py`)
- Interface segmentation starter workflow (`scripts/train_interface_segmentation.py`)
- Contour-to-trajectory feature extraction workflow (`scripts/extract_contours_trajectories.py`)
- Derived-feature QA dashboard generation (`scripts/build_feature_qa_dashboard.py`)
- Active correction queue generation for label/error triage (`scripts/build_label_correction_queue.py`)
- Experimental fine-tuning path with pretrained model warm-start (`scripts/train_multimodal_model.py --init-model`)
- Reproducibility hardening helpers for lockfiles + deterministic checks (`scripts/export_environment_lockfile.py`, `scripts/check_deterministic_training.py`)
- Governance pack generation for handoff/go-no-go/roadmap (`scripts/build_mvp_governance_pack.py`)
- MVP operator documentation bundle (`docs/mvp/SETUP_GUIDE.md`, `docs/mvp/RUNBOOK.md`, `docs/mvp/OPERATOR_QUICKSTART.md`, `docs/mvp/TROUBLESHOOTING.md`)

## Project structure
```text
configs/
  baselines/
  validation/
  simulations/
  splits/
data/
  raw/
  canonical/
  manifests/
  simulation/
docs/
  data/
  modeling/
  mvp/
schemas/
scripts/
src/interact_capsules/
templates/
```

## Setup
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e .
# Optional full validation stack (jsonschema + yaml configs)
pip install -e ".[validation]"
```

## Unified CLI (MVP-028/029)
After installation, use `interact-capsules` for a single command surface over all current MVP scripts.

Show command groups:
```bash
interact-capsules --help
```

Run the canonical Family A data workflow end-to-end:
```bash
interact-capsules pipeline \
  --source-dir data/raw \
  --dataset-root data/canonical/family_a \
  --family A \
  --run-id-mode canonicalize \
  --snapshot-name family_a_v1
```

Run individual steps (example):
```bash
interact-capsules inventory \
  --source-dir data/raw \
  --output data/manifests/inventory_family_a.csv \
  --family A
```

## Quickstart (first pipeline pass)
1. Build raw inventory:
```bash
python3 scripts/build_inventory.py \
  --source-dir data/raw \
  --family A \
  --output data/manifests/inventory_family_a.csv
```

2. Ingest Family A runs into canonical structure:
```bash
python3 scripts/ingest_runs.py \
  --source-dir data/raw \
  --dest-root data/canonical/family_a \
  --family A \
  --run-id-mode canonicalize
```

3. Validate canonical dataset:
```bash
python3 scripts/validate_dataset.py \
  --dataset-root data/canonical/family_a
```

4. Create split artifact:
```bash
python3 scripts/create_split.py \
  --dataset-root data/canonical/family_a \
  --config configs/splits/family_a_split.json \
  --output data/canonical/family_a/manifests/splits/family_a_v1.json
```

5. Run baseline heuristic benchmark:
```bash
python3 scripts/baseline_regime_map.py \
  --dataset-root data/canonical/family_a \
  --split data/canonical/family_a/manifests/splits/family_a_v1.json \
  --output data/canonical/family_a/manifests/reports/baseline_family_a_v1.json
```

6. Snapshot dataset version:
```bash
python3 scripts/snapshot_dataset.py \
  --dataset-root data/canonical/family_a \
  --name family_a_v1
```

7. Plan the first Family A axisymmetric simulation sweep:
```bash
python3 scripts/plan_axisymmetric_sweep.py \
  --config configs/simulations/family_a_axisymmetric_doe.json \
  --output data/simulation/family_a/manifests/axisymmetric_sweep_v1.jsonl \
  --family A
```

8. Generate first synthetic simulation corpus from the sweep plan:
```bash
python3 scripts/generate_simulation_corpus.py \
  --plan-jsonl data/simulation/family_a/manifests/axisymmetric_sweep_v1.jsonl \
  --surrogate-config configs/simulations/family_a_axisymmetric_surrogate.json \
  --output-root data/simulation/family_a/corpus/family_a_axisymmetric_doe_v1 \
  --family A
```

9. (Optional) Compare simulation corpus against canonical experimental data:
```bash
python3 scripts/report_simulation_realism.py \
  --simulation-dataset-root data/simulation/family_a/corpus/family_a_axisymmetric_doe_v1 \
  --experimental-dataset-root data/canonical/family_a \
  --output data/simulation/family_a/manifests/reports/realism_family_a_v1.json
```

10. Train/evaluate multimodal v1 baseline model:
```bash
python3 scripts/train_multimodal_model.py \
  --dataset-root data/canonical/family_a \
  --split data/canonical/family_a/manifests/splits/family_a_v1.json \
  --config configs/modeling/family_a_multimodal_v1.json \
  --output-dir data/canonical/family_a/manifests/models
```

11. Calibrate uncertainty from prediction artifacts:
```bash
python3 scripts/calibrate_multimodal_uncertainty.py \
  --predictions data/canonical/family_a/manifests/models/<model_id>.predictions.jsonl \
  --config configs/modeling/family_a_uncertainty_calibration_v1.json \
  --output data/canonical/family_a/manifests/models/<model_id>.calibration.json
```

12. Generate model card:
```bash
python3 scripts/generate_model_card.py \
  --model-artifact data/canonical/family_a/manifests/models/<model_id>.model.json \
  --eval-artifact data/canonical/family_a/manifests/models/<model_id>.eval.json \
  --calibration-artifact data/canonical/family_a/manifests/models/<model_id>.calibration.json \
  --template templates/model_card.template.md \
  --output data/canonical/family_a/manifests/model_cards/<model_id>.md
```

13. Rank next experiments with acquisition + guardrails:
```bash
python3 scripts/recommend_next_experiments.py \
  --model-artifact data/canonical/family_a/manifests/models/<model_id>.model.json \
  --candidates data/simulation/family_a/manifests/axisymmetric_sweep_v1.jsonl \
  --config configs/modeling/family_a_recommendation_v1.json \
  --calibration-artifact data/canonical/family_a/manifests/models/<model_id>.calibration.json \
  --output data/canonical/family_a/manifests/recommendations/<model_id>.recommendations.json
```

14. Train segmentation baseline on frame-level pixel samples:
```bash
python3 scripts/train_interface_segmentation.py \
  --dataset-root data/simulation/family_a/corpus/smoke_model_train_v1 \
  --annotations data/simulation/family_a/corpus/smoke_model_train_v1/manifests/segmentation/smoke_pixel_samples.jsonl \
  --split data/simulation/family_a/corpus/smoke_model_train_v1/manifests/splits/smoke_v1.json \
  --config configs/modeling/family_a_segmentation_v1.json \
  --output-dir data/simulation/family_a/corpus/smoke_model_train_v1/manifests/segmentation_models
```

15. Extract contour-derived trajectories into derived-features artifacts:
```bash
python3 scripts/extract_contours_trajectories.py \
  --dataset-root data/simulation/family_a/corpus/smoke_model_train_v1 \
  --contours data/simulation/family_a/corpus/smoke_model_train_v1/manifests/segmentation/smoke_contour_observations.jsonl \
  --config configs/modeling/family_a_contour_extraction_v1.json \
  --output-dir data/simulation/family_a/corpus/smoke_model_train_v1/manifests/segmentation_features
```

16. Build feature QA dashboard:
```bash
python3 scripts/build_feature_qa_dashboard.py \
  --derived-features-index data/simulation/family_a/corpus/smoke_model_train_v1/manifests/segmentation_features/derived_features_index.jsonl \
  --config configs/modeling/family_a_feature_qa_v1.json \
  --output data/simulation/family_a/corpus/smoke_model_train_v1/manifests/reports/feature_qa_smoke_v1.json \
  --markdown-output data/simulation/family_a/corpus/smoke_model_train_v1/manifests/reports/feature_qa_smoke_v1.md
```

17. Build active correction queue:
```bash
python3 scripts/build_label_correction_queue.py \
  --segmentation-qc data/simulation/family_a/corpus/smoke_model_train_v1/manifests/segmentation_models/smoke_family_a_segmentation_v1.qc.json \
  --feature-qa data/simulation/family_a/corpus/smoke_model_train_v1/manifests/reports/feature_qa_smoke_v1.json \
  --extraction-report data/simulation/family_a/corpus/smoke_model_train_v1/manifests/segmentation_features/extraction_report.json \
  --config configs/modeling/family_a_label_correction_v1.json \
  --output data/simulation/family_a/corpus/smoke_model_train_v1/manifests/reports/label_correction_smoke_v1.json
```

18. Fine-tune multimodal model from synthetic pretraining:
```bash
python3 scripts/train_multimodal_model.py \
  --dataset-root data/canonical/family_a \
  --split data/canonical/family_a/manifests/splits/family_a_v1.json \
  --config configs/modeling/family_a_multimodal_v1_finetune.json \
  --init-model data/simulation/family_a/corpus/smoke_model_train_v1/manifests/models/smoke_family_a_multimodal_v1_pretrain.model.json \
  --output-dir data/canonical/family_a/manifests/models
```

19. Build lightweight HTML UI for recommendation review:
```bash
python3 scripts/build_recommendation_ui.py \
  --recommendation-report data/canonical/family_a/manifests/recommendations/<model_id>.recommendations.json \
  --output-html data/canonical/family_a/manifests/recommendations/<model_id>.recommendations.html
```

20. Export environment lockfile and run deterministic training check:
```bash
python3 scripts/export_environment_lockfile.py \
  --pyproject pyproject.toml \
  --include-optional validation \
  --output locks/environment.lock.txt

python3 scripts/check_deterministic_training.py \
  --dataset-root data/simulation/family_a/corpus/smoke_model_train_v1 \
  --split data/simulation/family_a/corpus/smoke_model_train_v1/manifests/splits/smoke_v1.json \
  --config configs/modeling/family_a_multimodal_v1.json \
  --output data/simulation/family_a/corpus/smoke_model_train_v1/manifests/reports/determinism_report.json
```

21. Convert ranked recommendations into an execution template:
```bash
python3 scripts/build_experiment_execution_template.py \
  --recommendation-report data/simulation/family_a/corpus/smoke_model_train_v1/manifests/models/smoke_family_a_multimodal_v1_pretrain.recommendations.cli.json \
  --config configs/validation/family_a_experiment_execution_v1.json \
  --output data/simulation/family_a/corpus/smoke_model_train_v1/manifests/reports/experiment_execution_template_smoke_v1.json \
  --markdown-output data/simulation/family_a/corpus/smoke_model_train_v1/manifests/reports/experiment_execution_template_smoke_v1.md
```

22. Compare model-guided vs baseline campaign logs:
```bash
python3 scripts/analyze_campaign_outcomes.py \
  --model-guided-log data/simulation/family_a/corpus/smoke_model_train_v1/manifests/reports/campaign_model_guided_smoke_v1.jsonl \
  --baseline-log data/simulation/family_a/corpus/smoke_model_train_v1/manifests/reports/campaign_baseline_smoke_v1.jsonl \
  --config configs/validation/family_a_campaign_analysis_v1.json \
  --output data/simulation/family_a/corpus/smoke_model_train_v1/manifests/reports/campaign_analysis_smoke_v1.json
```

23. Build failure-mode analysis report:
```bash
python3 scripts/build_failure_mode_analysis.py \
  --predictions data/simulation/family_a/corpus/smoke_model_train_v1/manifests/models/smoke_family_a_multimodal_v1_pretrain.predictions.jsonl \
  --config configs/validation/family_a_failure_mode_analysis_v1.json \
  --output data/simulation/family_a/corpus/smoke_model_train_v1/manifests/reports/failure_mode_analysis_smoke_v1.json
```

24. Prepare prospective campaign plans/log templates for primary or robustness profiles:
```bash
python3 scripts/prepare_prospective_campaign.py \
  --runs-input data/simulation/family_a/corpus/smoke_model_train_v1/manifests/reports/experiment_execution_template_smoke_v1.json \
  --config configs/validation/family_a_prospective_campaign_v1.json \
  --analysis-config configs/validation/family_a_campaign_analysis_v1.json \
  --campaign-profile model_guided_primary \
  --output data/simulation/family_a/corpus/smoke_model_train_v1/manifests/reports/campaign_prepared_model_guided_primary_smoke_v1.json \
  --campaign-log-output data/simulation/family_a/corpus/smoke_model_train_v1/manifests/reports/campaign_model_guided_primary_smoke_v1.jsonl
```

25. Build governance pack (handoff + go/no-go + roadmap):
```bash
python3 scripts/build_mvp_governance_pack.py \
  --progress-tracker ../Progress_Tracking.md \
  --todo ../ToDo.md \
  --config configs/mvp/family_a_mvp_governance_v1.json \
  --output-dir data/simulation/family_a/corpus/smoke_model_train_v1/manifests/reports \
  --prefix family_a_mvp_smoke_v1
```

## Data templates
- `templates/run_metadata.template.json`
- `templates/labels.template.json`

## Run ID policy
- Canonicalization rules and traceability details: `docs/data/RUN_ID_CONVENTIONS.md`

## Next build phase
Prospective campaign execution on production Family A data and governance closure (handoff + go/no-go) are the immediate next focus areas once real run logs are available.

## Operator docs
- `docs/mvp/SETUP_GUIDE.md`
- `docs/mvp/RUNBOOK.md`
- `docs/mvp/OPERATOR_QUICKSTART.md`
- `docs/mvp/TROUBLESHOOTING.md`
- `docs/mvp/REPRODUCIBILITY_WORKFLOW.md`
- `docs/mvp/UI_PROTOTYPE_WORKFLOW.md`
- `docs/mvp/GOVERNANCE_WORKFLOW.md`
