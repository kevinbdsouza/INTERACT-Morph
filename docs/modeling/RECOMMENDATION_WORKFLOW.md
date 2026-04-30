# MVP-025/026/027: Recommendation Workflow (v1)

## Goal
Rank next Family A experiments using:
- Multi-objective ranking (success probability + geometry targets + uncertainty penalty)
- Acquisition functions (EI and UCB style)
- Guardrails to reject extrapolation-heavy suggestions

## CLI Command
```bash
interact-morph recommend \
  --model-artifact data/canonical/family_a/manifests/models/<model_id>.model.json \
  --candidates data/simulation/family_a/manifests/axisymmetric_sweep_v1.jsonl \
  --config configs/modeling/family_a_recommendation_v1.json \
  --calibration-artifact data/canonical/family_a/manifests/models/<model_id>.calibration.json \
  --output data/canonical/family_a/manifests/recommendations/<model_id>.recommendations.json
```

## Script Entry Point
```bash
python3 scripts/recommend_next_experiments.py \
  --model-artifact data/canonical/family_a/manifests/models/<model_id>.model.json \
  --candidates data/simulation/family_a/manifests/axisymmetric_sweep_v1.jsonl \
  --config configs/modeling/family_a_recommendation_v1.json \
  --calibration-artifact data/canonical/family_a/manifests/models/<model_id>.calibration.json \
  --output data/canonical/family_a/manifests/recommendations/<model_id>.recommendations.json
```

## Inputs
- `*.model.json` from `model-train`
- Candidate JSONL (typically from `sim-plan`)
- Recommendation config (`objective`, `acquisition`, `guardrails`)
- Optional `*.calibration.json` from `model-calibrate`

## Outputs
- `*.recommendations.json` report with:
  - ranked accepted candidates (`top_k`)
  - objective component breakdown
  - EI and UCB acquisition scores
  - uncertainty proxy details
  - guardrail diagnostics and rejected candidate reasons
- Optional MVP-030 UI rendering:
  - `interact-morph recommend-ui --recommendation-report ... --output-html ...`
  - standalone HTML for operator review and filtering

## Notes
- `acquisition.method` selects ranking by EI or UCB, while both scores are always computed.
- Guardrails run on standardized feature-space distance and extrapolation checks relative to training vectors.
- Optional calibration artifact is used to convert margin-based confidence into calibrated probability fields before ranking.
