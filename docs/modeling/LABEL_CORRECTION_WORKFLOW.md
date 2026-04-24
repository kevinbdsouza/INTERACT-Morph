# MVP-014: Active Label/Error-Correction Loop Workflow

## Goal
Create a reproducible triage queue that merges segmentation QC, contour extraction failures, and trajectory feature QA findings into prioritized correction tasks.

## CLI Command
```bash
interact-capsules label-correction \
  --segmentation-qc data/simulation/family_a/corpus/smoke_model_train_v1/manifests/segmentation_models/smoke_family_a_segmentation_v1.qc.json \
  --feature-qa data/simulation/family_a/corpus/smoke_model_train_v1/manifests/reports/feature_qa_smoke_v1.json \
  --extraction-report data/simulation/family_a/corpus/smoke_model_train_v1/manifests/segmentation_features/extraction_report.json \
  --config configs/modeling/family_a_label_correction_v1.json \
  --output data/simulation/family_a/corpus/smoke_model_train_v1/manifests/reports/label_correction_smoke_v1.json \
  --markdown-output data/simulation/family_a/corpus/smoke_model_train_v1/manifests/reports/label_correction_smoke_v1.md
```

## Script Entry Point
```bash
python3 scripts/build_label_correction_queue.py \
  --segmentation-qc <segmentation_qc.json> \
  --feature-qa <feature_qa.json> \
  --extraction-report <extraction_report.json> \
  --config configs/modeling/family_a_label_correction_v1.json \
  --output <label_correction_queue.json>
```

## Inputs
- Segmentation QC artifact from `scripts/train_interface_segmentation.py`
- Feature QA artifact from `scripts/build_feature_qa_dashboard.py`
- Optional extraction failures from `scripts/extract_contours_trajectories.py`

## Outputs
- `label_correction_*.json`: queue entries with per-run priority, score, reasons, and recommended actions
- Optional markdown summary for sprint planning/review

## Notes
- Scoring, thresholds, and priority bands are config-driven.
- Queue entries stay intentionally simple (`status: pending`) so they can be version-controlled and updated during weekly triage.
- This closes the first executable loop for MVP-014 while still allowing later integration with richer annotation tools.
