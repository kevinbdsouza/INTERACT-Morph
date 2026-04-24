# MVP-022: Experimental Fine-Tuning Workflow (Family A)

## Goal
Start the experimental-transfer stage by warm-starting the multimodal predictor from a synthetic pretraining model artifact and adapting on experimental Family A splits.

## CLI Command
```bash
interact-capsules model-finetune \
  --dataset-root data/canonical/family_a \
  --split data/canonical/family_a/manifests/splits/family_a_v1.json \
  --init-model data/simulation/family_a/corpus/smoke_model_train_v1/manifests/models/smoke_family_a_multimodal_v1_pretrain.model.json \
  --config configs/modeling/family_a_multimodal_v1_finetune.json \
  --output-dir data/canonical/family_a/manifests/models
```

## Script Entry Point
```bash
python3 scripts/train_multimodal_model.py \
  --dataset-root <experimental_dataset_root> \
  --split <experimental_split.json> \
  --config configs/modeling/family_a_multimodal_v1_finetune.json \
  --init-model <synthetic_pretrain_model.json> \
  --output-dir <model_output_dir>
```

## Fine-Tuning Controls (`fine_tuning` config block)
- `reuse_pretrained_preprocessing`: reuses train-time normalization stats from the pretrained model artifact.
- `prior_class_weight`: pseudo-count weight used to blend pretrained and experimental classification centroids.
- `include_prior_regression_memory`: appends pretrained regression memory into k-NN regressors.
- `max_prior_regression_samples`: caps transferred regression memory per target.

## Outputs
- Standard model artifacts (`*.model.json`, `*.eval.json`, `*.predictions.jsonl`)
- `model.json` now includes a `fine_tuning` section with transfer provenance and settings.

## Notes
- Feature names must match between config and pretrained artifact.
- This workflow is intentionally simple and deterministic so transfer behavior can be audited before moving to heavier neural fine-tuning stacks.
