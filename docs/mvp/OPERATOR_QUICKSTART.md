# INTERACT-Capsules Operator Quickstart (MVP-037)

## Purpose
Run one full recommendation cycle from prepared artifacts with minimal manual decisions.

## Fast Path
1. Generate recommendations:
```bash
interact-capsules recommend \
  --model-artifact data/canonical/family_a/manifests/models/<model_id>.model.json \
  --candidates data/simulation/family_a/manifests/axisymmetric_sweep_v1.jsonl \
  --config configs/modeling/family_a_recommendation_v1.json \
  --calibration-artifact data/canonical/family_a/manifests/models/<model_id>.calibration.json \
  --output data/canonical/family_a/manifests/recommendations/<model_id>.recommendations.json
```

2. Build review UI:
```bash
interact-capsules recommend-ui \
  --recommendation-report data/canonical/family_a/manifests/recommendations/<model_id>.recommendations.json \
  --output-html data/canonical/family_a/manifests/recommendations/<model_id>.recommendations.html
```

3. Open the HTML file in a browser and review:
- Ranked accepted candidates
- Rejected candidates with guardrail reasons
- Filters for success probability, uncertainty, and candidate ID

## If Training Is Needed First
```bash
interact-capsules model-train \
  --dataset-root data/canonical/family_a \
  --split data/canonical/family_a/manifests/splits/family_a_v1.json \
  --config configs/modeling/family_a_multimodal_v1.json \
  --output-dir data/canonical/family_a/manifests/models
```

## Reproducibility Check Before Lab Review
```bash
interact-capsules repro-check \
  --dataset-root data/simulation/family_a/corpus/smoke_model_train_v1 \
  --split data/simulation/family_a/corpus/smoke_model_train_v1/manifests/splits/smoke_v1.json \
  --config configs/modeling/family_a_multimodal_v1.json \
  --output data/simulation/family_a/corpus/smoke_model_train_v1/manifests/reports/determinism_report.json
```

Proceed only when report field `passed` is `true`.
