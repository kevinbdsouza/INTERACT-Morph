# MVP-020: Multimodal Training Pipeline (v1)

## Goal
Provide a config-driven, reproducible training/evaluation path for Family A multimodal prediction.

## CLI Command
```bash
interact-capsules model-train \
  --dataset-root data/canonical/family_a \
  --split data/canonical/family_a/manifests/splits/family_a_v1.json \
  --config configs/modeling/family_a_multimodal_v1.json \
  --output-dir data/canonical/family_a/manifests/models
```

## Script Entry Point
```bash
python3 scripts/train_multimodal_model.py \
  --dataset-root data/canonical/family_a \
  --split data/canonical/family_a/manifests/splits/family_a_v1.json \
  --config configs/modeling/family_a_multimodal_v1.json \
  --output-dir data/canonical/family_a/manifests/models
```

## Inputs
- Canonical dataset root with `runs/<run_id>/metadata.json`
- Optional `runs/<run_id>/derived_features.json`
- Split artifact produced by `create_split.py`
- Model config listing feature and target paths

## Outputs
- `*.model.json`: preprocessing stats and fitted head parameters
- `*.eval.json`: train/val/test metrics and loading diagnostics
- `*.predictions.jsonl`: per-run truth vs prediction records
- Optional downstream:
  - `scripts/calibrate_multimodal_uncertainty.py` for MVP-023 calibration artifacts
  - `scripts/generate_model_card.py` for MVP-024 model card output

## Current Metrics
- Success head: accuracy, precision, recall, F1
- Regime head: accuracy, macro-F1, class distributions
- Regression heads: MAE, RMSE

## Reproducibility Notes
- Feature preprocessing is fit only on train split.
- Split and config files are SHA256-hashed into the model artifact.
- All outputs are JSON/JSONL to simplify auditing and diffs.
- For transfer runs, `--init-model` enables MVP-022 warm-start blending (see `docs/modeling/FINETUNING_WORKFLOW.md`).
