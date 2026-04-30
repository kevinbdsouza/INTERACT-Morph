# INTERACT-Morph Family A Placeholder Dataset Card

- Generated at UTC: `2026-04-30T17:50:58.411409+00:00`
- Dataset root: `data/canonical/family_a`
- Family: `A`
- Run count: `120`
- Fluid combinations: `27`
- Run ID mode: `preserve`
- Source directory: `data/simulation/family_a/corpus/smoke_model_train_v1/runs`

## Scope And Intended Use

This dataset card summarizes canonical INTERACT-Morph runs for morphology-first inverse design. It is intended to support dataset review, split traceability, baseline/model training, recommendation guardrails, and MVP go/no-go evidence.

## Distributions

### Regime Labels

| Value | Count |
|---|---:|
| `stable_wrapping` | 40 |
| `trapping` | 80 |

### Encapsulation Success

| Value | Count |
|---|---:|
| `False` | 80 |
| `True` | 40 |

### Route Types

No values found.

### Confinement Types

No values found.

## Morphology Label Coverage

| Field | Present | Missing |
|---|---:|---:|
| `shell_thickness_mean_um` | 120 | 0 |
| `shell_thickness_nonuniformity` | 0 | 120 |
| `crown_index` | 0 | 120 |
| `trapped_air_fraction` | 0 | 120 |
| `encapsulated_volume_ul` | 0 | 120 |
| `core_offset` | 0 | 120 |
| `layer_sequence` | 0 | 120 |

## Quality Flags

| Flag | True | False | Missing |
|---|---:|---:|---:|
| `video_complete` | 120 | 0 | 0 |
| `annotation_complete` | 120 | 0 | 0 |
| `sensors_calibrated` | 120 | 0 | 0 |

## Split Traceability

- Split artifact: `data/canonical/family_a/manifests/splits/family_a_placeholder_v1.json`
- Split name: `family_a_v1`
- Seed: `42`
- Group by: `fluid_combination_id`

| Split | Runs | Groups |
|---|---:|---:|
| `test` | 19 | 4 |
| `train` | 83 | 19 |
| `val` | 18 | 4 |

## Known Gaps Sample

| Run ID | Gaps |
|---|---|
| `A_SIM_A_000001` | `missing_outcome:shell_thickness_nonuniformity`, `missing_outcome:crown_index`, `missing_outcome:trapped_air_fraction`, `missing_outcome:encapsulated_volume_ul`, `missing_outcome:core_offset`, `missing_outcome:layer_sequence`, `missing_control_parameters.route_type`, `missing_control_parameters.confinement_type` |
| `A_SIM_A_000002` | `missing_outcome:shell_thickness_nonuniformity`, `missing_outcome:crown_index`, `missing_outcome:trapped_air_fraction`, `missing_outcome:encapsulated_volume_ul`, `missing_outcome:core_offset`, `missing_outcome:layer_sequence`, `missing_control_parameters.route_type`, `missing_control_parameters.confinement_type` |
| `A_SIM_A_000003` | `missing_outcome:shell_thickness_nonuniformity`, `missing_outcome:crown_index`, `missing_outcome:trapped_air_fraction`, `missing_outcome:encapsulated_volume_ul`, `missing_outcome:core_offset`, `missing_outcome:layer_sequence`, `missing_control_parameters.route_type`, `missing_control_parameters.confinement_type` |
| `A_SIM_A_000004` | `missing_outcome:shell_thickness_nonuniformity`, `missing_outcome:crown_index`, `missing_outcome:trapped_air_fraction`, `missing_outcome:encapsulated_volume_ul`, `missing_outcome:core_offset`, `missing_outcome:layer_sequence`, `missing_control_parameters.route_type`, `missing_control_parameters.confinement_type` |
| `A_SIM_A_000005` | `missing_outcome:shell_thickness_nonuniformity`, `missing_outcome:crown_index`, `missing_outcome:trapped_air_fraction`, `missing_outcome:encapsulated_volume_ul`, `missing_outcome:core_offset`, `missing_outcome:layer_sequence`, `missing_control_parameters.route_type`, `missing_control_parameters.confinement_type` |
| `A_SIM_A_000006` | `missing_outcome:shell_thickness_nonuniformity`, `missing_outcome:crown_index`, `missing_outcome:trapped_air_fraction`, `missing_outcome:encapsulated_volume_ul`, `missing_outcome:core_offset`, `missing_outcome:layer_sequence`, `missing_control_parameters.route_type`, `missing_control_parameters.confinement_type` |
| `A_SIM_A_000007` | `missing_outcome:shell_thickness_nonuniformity`, `missing_outcome:crown_index`, `missing_outcome:trapped_air_fraction`, `missing_outcome:encapsulated_volume_ul`, `missing_outcome:core_offset`, `missing_outcome:layer_sequence`, `missing_control_parameters.route_type`, `missing_control_parameters.confinement_type` |
| `A_SIM_A_000008` | `missing_outcome:shell_thickness_nonuniformity`, `missing_outcome:crown_index`, `missing_outcome:trapped_air_fraction`, `missing_outcome:encapsulated_volume_ul`, `missing_outcome:core_offset`, `missing_outcome:layer_sequence`, `missing_control_parameters.route_type`, `missing_control_parameters.confinement_type` |
| `A_SIM_A_000009` | `missing_outcome:shell_thickness_nonuniformity`, `missing_outcome:crown_index`, `missing_outcome:trapped_air_fraction`, `missing_outcome:encapsulated_volume_ul`, `missing_outcome:core_offset`, `missing_outcome:layer_sequence`, `missing_control_parameters.route_type`, `missing_control_parameters.confinement_type` |
| `A_SIM_A_000010` | `missing_outcome:shell_thickness_nonuniformity`, `missing_outcome:crown_index`, `missing_outcome:trapped_air_fraction`, `missing_outcome:encapsulated_volume_ul`, `missing_outcome:core_offset`, `missing_outcome:layer_sequence`, `missing_control_parameters.route_type`, `missing_control_parameters.confinement_type` |
| `A_SIM_A_000011` | `missing_outcome:shell_thickness_nonuniformity`, `missing_outcome:crown_index`, `missing_outcome:trapped_air_fraction`, `missing_outcome:encapsulated_volume_ul`, `missing_outcome:core_offset`, `missing_outcome:layer_sequence`, `missing_control_parameters.route_type`, `missing_control_parameters.confinement_type` |
| `A_SIM_A_000012` | `missing_outcome:shell_thickness_nonuniformity`, `missing_outcome:crown_index`, `missing_outcome:trapped_air_fraction`, `missing_outcome:encapsulated_volume_ul`, `missing_outcome:core_offset`, `missing_outcome:layer_sequence`, `missing_control_parameters.route_type`, `missing_control_parameters.confinement_type` |

## Production Readiness Notes

- Synthetic or smoke-only datasets should not be used to close G1-G3 acceptance gates.
- Production acceptance requires real experimental videos, morphology labels, route/confinement metadata, split artifacts, and baseline/model evidence generated from this dataset version.
