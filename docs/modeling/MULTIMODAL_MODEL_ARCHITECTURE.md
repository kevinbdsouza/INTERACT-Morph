# MVP-019: Multimodal Model Architecture (Family A v1)

## Purpose
Define a concrete, reproducible architecture for Family A prediction that fuses:
- Experiment controls
- Fluid properties
- Early-time observables (derived features)

This v1 architecture is intentionally lightweight so it can be trained/evaluated with the current repository dependencies and later swapped for neural encoders without changing artifact contracts.

## Input Blocks

### 1) Metadata controls and fluid properties
From `metadata.json`:
- `control_parameters.impact_velocity_m_s`
- `control_parameters.droplet_diameter_mm`
- `control_parameters.shell_outer_diameter_mm`
- `fluid_system.interfacial_layer.thickness_mm` (optional)
- `fluid_system.core.density_kg_m3`
- `fluid_system.core.viscosity_pa_s`
- `fluid_system.interfacial_tension_n_m`

### 2) Early-time observables
From `derived_features.json` (if present):
- `summary.penetration_depth_max_mm`
- `summary.neck_radius_min_mm`
- `events_ms.closure_time_ms`
- `events_ms.detachment_time_ms`

## Fusion Strategy
- Concatenate all configured numeric features into one vector.
- Apply deterministic preprocessing:
  - Mean imputation from training split statistics.
  - Per-feature standardization (z-score) from training split.

This produces one fused latent vector per run.

## Output Heads

### Classification heads
- `encapsulation_success` (binary)
  - Model: nearest-centroid classifier in standardized feature space.
- `regime_label` (multiclass)
  - Model: nearest-centroid classifier in standardized feature space.

### Regression heads
- `shell_thickness_mean_um`
- `capsule_eccentricity`
  - Model: inverse-distance weighted k-NN regressor in standardized feature space.

## Training and Evaluation Contract
- Training script: `scripts/train_multimodal_model.py`
- Configuration: `configs/modeling/family_a_multimodal_v1.json`
- Split artifact input: output of `scripts/create_split.py`
- Outputs:
  - `<model_id>.model.json`
  - `<model_id>.eval.json`
  - `<model_id>.predictions.jsonl`

## Why This Meets MVP-019
- Exact input schema and field-level contract is defined.
- Fusion mechanism is explicit and reproducible.
- Output heads cover required classification and regression targets.
- Design leaves a clean upgrade path to neural encoders while preserving CLI/artifact interfaces.
