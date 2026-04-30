# MVP-031: Experiment Execution Template Workflow

## Goal
Convert recommendation artifacts into an operator-ready execution template that standardizes:
- pre-run checks
- ranked run sheet with predicted outcomes
- per-run measurement capture
- stop conditions and signoff fields

## CLI Command
```bash
interact-morph experiment-template \
  --recommendation-report data/canonical/family_a/manifests/recommendations/<model_id>.recommendations.json \
  --config configs/validation/family_a_experiment_execution_v1.json \
  --output data/canonical/family_a/manifests/reports/<campaign_id>.execution_template.json \
  --markdown-output data/canonical/family_a/manifests/reports/<campaign_id>.execution_template.md
```

## Script Entry Point
```bash
python3 scripts/build_experiment_execution_template.py \
  --recommendation-report data/canonical/family_a/manifests/recommendations/<model_id>.recommendations.json \
  --config configs/validation/family_a_experiment_execution_v1.json \
  --output data/canonical/family_a/manifests/reports/<campaign_id>.execution_template.json \
  --markdown-output data/canonical/family_a/manifests/reports/<campaign_id>.execution_template.md
```

## Inputs
- recommendation report JSON (`recommend`)
- execution-template config (`configs/validation/family_a_experiment_execution_v1.json`)

## Outputs
- execution template JSON with campaign metadata, protocol checklist, and planned run rows
- optional markdown checklist for operator handoff

## Notes
- `--top-k` can override config defaults per campaign.
- Planned run IDs are generated deterministically from configured run prefix + rank.
- Guardrail status from recommendations is embedded directly for operator review.
