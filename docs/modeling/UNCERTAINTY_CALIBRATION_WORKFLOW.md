# MVP-023: Uncertainty Calibration Workflow (v1)

## Goal
Produce calibrated uncertainty artifacts for classification heads from model prediction outputs.

## CLI Command
```bash
interact-capsules model-calibrate \
  --predictions data/canonical/family_a/manifests/models/<model_id>.predictions.jsonl \
  --config configs/modeling/family_a_uncertainty_calibration_v1.json \
  --output data/canonical/family_a/manifests/models/<model_id>.calibration.json
```

## Script Entry Point
```bash
python3 scripts/calibrate_multimodal_uncertainty.py \
  --predictions data/canonical/family_a/manifests/models/<model_id>.predictions.jsonl \
  --config configs/modeling/family_a_uncertainty_calibration_v1.json \
  --output data/canonical/family_a/manifests/models/<model_id>.calibration.json
```

## Inputs
- `*.predictions.jsonl` from `model-train`
- Calibration config (`fit_split`, temperature grid, bin count, isotonic options)

## Outputs
- `*.calibration.json`: per-head calibration report with:
  - temperature scaling parameters
  - optional isotonic post-calibration model
  - log-loss / Brier / ECE before and after calibration
  - reliability bins by split
- `*.calibrated_predictions.jsonl`: predictions with calibrated probability fields

## Current Scope
- `encapsulation_success_probability` calibrated from signed margin proxy.
- `regime_top1_correctness_probability` calibrated for top-1 correctness confidence.

## Notes
- Preferred fit split is `val`, with fallback when class coverage is insufficient.
- This workflow is a scaffold for MVP-023 and should be revalidated on production Family A data.
