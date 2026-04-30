# MVP-032/033: Prospective Campaign Preparation Workflow

## Goal
Prepare campaign-ready run sheets and append-ready campaign logs for:
- primary validation arm (`MVP-032`)
- held-out robustness arm (`MVP-033`)

## CLI Command
```bash
interact-morph campaign-prepare \
  --runs-input data/canonical/family_a/manifests/reports/campaign_model_guided.execution_template.json \
  --config configs/validation/family_a_prospective_campaign_v1.json \
  --analysis-config configs/validation/family_a_campaign_analysis_v1.json \
  --campaign-profile model_guided_primary \
  --output data/canonical/family_a/manifests/reports/campaign_prepared_model_guided_primary.json \
  --campaign-log-output data/canonical/family_a/manifests/reports/campaign_model_guided.jsonl \
  --markdown-output data/canonical/family_a/manifests/reports/campaign_prepared_model_guided_primary.md
```

## Script Entry Point
```bash
python3 scripts/prepare_prospective_campaign.py \
  --runs-input data/canonical/family_a/manifests/reports/campaign_model_guided.execution_template.json \
  --config configs/validation/family_a_prospective_campaign_v1.json \
  --analysis-config configs/validation/family_a_campaign_analysis_v1.json \
  --campaign-profile model_guided_primary \
  --output data/canonical/family_a/manifests/reports/campaign_prepared_model_guided_primary.json \
  --campaign-log-output data/canonical/family_a/manifests/reports/campaign_model_guided.jsonl
```

## Supported Campaign Profiles
Configured in `configs/validation/family_a_prospective_campaign_v1.json`:
- `model_guided_primary`
- `baseline_primary`
- `model_guided_robustness`
- `baseline_robustness`

## Outputs
- campaign plan JSON with selected runs, filters, and target-window acceptance metadata
- campaign log template JSONL with required analysis fields (`run_id`, `encapsulation_success`, `regime_label`, geometry metrics)
- optional markdown summary for operator review

## Notes
- `model_guided_*` profiles use ranked top-k selection.
- `baseline_*` profiles use evenly spaced rank sampling for baseline/grid-style comparison.
- Robustness profiles apply holdout filters before run selection.
