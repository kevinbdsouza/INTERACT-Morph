# MVP-032/033/034: Prospective Validation and Campaign Analysis Workflow

## Goal
Track campaign outcomes for model-guided and baseline search arms, then quantify reduction in experimental load to first target-window hit.

## Campaign Preparation (MVP-032/033)
Prepare campaign plans and log templates before campaign execution:
```bash
interact-capsules campaign-prepare \
  --runs-input data/canonical/family_a/manifests/reports/campaign_model_guided.execution_template.json \
  --config configs/validation/family_a_prospective_campaign_v1.json \
  --analysis-config configs/validation/family_a_campaign_analysis_v1.json \
  --campaign-profile model_guided_primary \
  --output data/canonical/family_a/manifests/reports/campaign_prepared_model_guided_primary.json \
  --campaign-log-output data/canonical/family_a/manifests/reports/campaign_model_guided.jsonl
```

## Campaign Log Format
Each log row should contain at least:
- `run_id`
- `completed` (or `status`)
- `encapsulation_success`
- `regime_label`
- `shell_thickness_mean_um`
- `capsule_eccentricity`

JSONL is recommended for append-only logging.

## CLI Command
```bash
interact-capsules campaign-analyze \
  --model-guided-log data/canonical/family_a/manifests/reports/campaign_model_guided.jsonl \
  --baseline-log data/canonical/family_a/manifests/reports/campaign_baseline.jsonl \
  --config configs/validation/family_a_campaign_analysis_v1.json \
  --output data/canonical/family_a/manifests/reports/campaign_analysis_v1.json \
  --markdown-output data/canonical/family_a/manifests/reports/campaign_analysis_v1.md
```

## Script Entry Point
```bash
python3 scripts/analyze_campaign_outcomes.py \
  --model-guided-log data/canonical/family_a/manifests/reports/campaign_model_guided.jsonl \
  --baseline-log data/canonical/family_a/manifests/reports/campaign_baseline.jsonl \
  --config configs/validation/family_a_campaign_analysis_v1.json \
  --output data/canonical/family_a/manifests/reports/campaign_analysis_v1.json \
  --markdown-output data/canonical/family_a/manifests/reports/campaign_analysis_v1.md
```

## Outputs
- campaign-level success/target-hit summaries
- runs-to-first-target-hit comparison
- reduction percentage vs baseline and pass/fail against configured threshold

## Notes
- Default acceptance target is `>=30%` reduction.
- If one campaign never reaches the target window, reduction is reported as non-computable rather than forced to zero.
- Use robustness profiles from `family_a_prospective_campaign_v1.json` to generate held-out campaign plans for MVP-033.
