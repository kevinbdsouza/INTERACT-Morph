# Segmentation + Trajectory Workflow (MVP-011/012/013)

## Purpose
Start the Family A segmentation/tracking workstream with reproducible CLI steps that are compatible with the current repository (no heavy ML/image dependencies required for the first scaffold).

## Artifacts
- `scripts/train_interface_segmentation.py` (MVP-011): trains a lightweight threshold-based interface segmentation baseline from frame-level pixel samples and emits QC metrics.
- `scripts/extract_contours_trajectories.py` (MVP-012): converts contour observations into `derived_features`-schema trajectory artifacts.
- `scripts/build_feature_qa_dashboard.py` (MVP-013): checks trajectory consistency/outliers and emits QA dashboard outputs.
- `scripts/build_label_correction_queue.py` (MVP-014): merges QC/QA/extraction findings into a prioritized correction queue for annotation sprints.

## Input Formats

### 1) Pixel sample annotations (MVP-011)
JSONL rows with:
- `run_id` (string)
- `frame_index` (int, optional)
- `split` (`train|val|test`, optional)
- `pixel_samples` (list of objects):
  - `intensity` (number)
  - `is_interface` (bool)

### 2) Contour observations (MVP-012)
JSONL rows with:
- `run_id` (string)
- `frame_index` (int, optional if `t_ms` present)
- `t_ms` (number, optional if `frame_index` present)
- `penetration_depth_px` (number)
- `neck_radius_px` (number)
- `shell_outer_radius_px` (number)
- `shell_inner_radius_px` (number)
- `capsule_major_axis_px` (number)
- `capsule_minor_axis_px` (number)

## Default Configs
- `configs/modeling/family_a_segmentation_v1.json`
- `configs/modeling/family_a_contour_extraction_v1.json`
- `configs/modeling/family_a_feature_qa_v1.json`

## Smoke Run (Synthetic Corpus)

1. Train segmentation baseline + QC report:
```bash
python3 scripts/train_interface_segmentation.py \
  --dataset-root data/simulation/family_a/corpus/smoke_model_train_v1 \
  --annotations data/simulation/family_a/corpus/smoke_model_train_v1/manifests/segmentation/smoke_pixel_samples.jsonl \
  --split data/simulation/family_a/corpus/smoke_model_train_v1/manifests/splits/smoke_v1.json \
  --config configs/modeling/family_a_segmentation_v1.json \
  --output-dir data/simulation/family_a/corpus/smoke_model_train_v1/manifests/segmentation_models \
  --model-id smoke_family_a_segmentation_v1
```

2. Extract trajectories from contour observations:
```bash
python3 scripts/extract_contours_trajectories.py \
  --dataset-root data/simulation/family_a/corpus/smoke_model_train_v1 \
  --contours data/simulation/family_a/corpus/smoke_model_train_v1/manifests/segmentation/smoke_contour_observations.jsonl \
  --config configs/modeling/family_a_contour_extraction_v1.json \
  --output-dir data/simulation/family_a/corpus/smoke_model_train_v1/manifests/segmentation_features \
  --model-version smoke_family_a_segmentation_v1
```

3. Build QA dashboard from extracted features:
```bash
python3 scripts/build_feature_qa_dashboard.py \
  --derived-features-index data/simulation/family_a/corpus/smoke_model_train_v1/manifests/segmentation_features/derived_features_index.jsonl \
  --config configs/modeling/family_a_feature_qa_v1.json \
  --output data/simulation/family_a/corpus/smoke_model_train_v1/manifests/reports/feature_qa_smoke_v1.json \
  --markdown-output data/simulation/family_a/corpus/smoke_model_train_v1/manifests/reports/feature_qa_smoke_v1.md
```

4. Build active correction queue from segmentation + feature QA:
```bash
python3 scripts/build_label_correction_queue.py \
  --segmentation-qc data/simulation/family_a/corpus/smoke_model_train_v1/manifests/segmentation_models/smoke_family_a_segmentation_v1.qc.json \
  --feature-qa data/simulation/family_a/corpus/smoke_model_train_v1/manifests/reports/feature_qa_smoke_v1.json \
  --extraction-report data/simulation/family_a/corpus/smoke_model_train_v1/manifests/segmentation_features/extraction_report.json \
  --config configs/modeling/family_a_label_correction_v1.json \
  --output data/simulation/family_a/corpus/smoke_model_train_v1/manifests/reports/label_correction_smoke_v1.json \
  --markdown-output data/simulation/family_a/corpus/smoke_model_train_v1/manifests/reports/label_correction_smoke_v1.md
```

## Notes
- This is intentionally a lightweight starter pipeline so the team can run end-to-end checks immediately.
- When production mask data lands, keep CLI contracts stable and swap in stronger segmentation models under the same artifact/report interfaces.
- Use the correction queue artifact as the weekly source of truth for annotation relabel priorities (MVP-014).
