# MVP-035: Failure-Mode Analysis Workflow

## Goal
Generate an error taxonomy from model prediction artifacts to identify:
- classification failure clusters
- regression targets with high absolute error
- low-margin confidence behavior
- highest-severity runs for correction/fine-tuning loops

## CLI Command
```bash
interact-morph failure-analysis \
  --predictions data/canonical/family_a/manifests/models/<model_id>.predictions.jsonl \
  --config configs/validation/family_a_failure_mode_analysis_v1.json \
  --output data/canonical/family_a/manifests/reports/<model_id>.failure_analysis.json \
  --markdown-output data/canonical/family_a/manifests/reports/<model_id>.failure_analysis.md
```

## Script Entry Point
```bash
python3 scripts/build_failure_mode_analysis.py \
  --predictions data/canonical/family_a/manifests/models/<model_id>.predictions.jsonl \
  --config configs/validation/family_a_failure_mode_analysis_v1.json \
  --output data/canonical/family_a/manifests/reports/<model_id>.failure_analysis.json \
  --markdown-output data/canonical/family_a/manifests/reports/<model_id>.failure_analysis.md
```

## Inputs
- prediction JSONL from `model-train` or `model-finetune`
- failure-analysis config with regression thresholds, margin warnings, and severity scoring

## Outputs
- JSON report with issue counts, split-level breakdowns, top failing runs, and recommended actions
- optional markdown summary for review meetings

## Notes
- Thresholds should be tuned with domain experts before prospective campaign decisions.
- Integrate top failing runs back into `label-correction` and fine-tuning queues.
