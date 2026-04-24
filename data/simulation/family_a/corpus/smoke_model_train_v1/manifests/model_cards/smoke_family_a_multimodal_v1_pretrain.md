# Model Card: smoke_family_a_multimodal_v1_pretrain

## Scope
- Family: `A` (MVP scope)
- Created at (UTC): `2026-04-18T02:42:18.281050+00:00`
- Dataset root: `INTERACT-Capsules/data/simulation/family_a/corpus/smoke_model_train_v1`
- Split artifact: `INTERACT-Capsules/data/simulation/family_a/corpus/smoke_model_train_v1/manifests/splits/smoke_v1.json`

## Data Summary
- Total runs: `120`
- Train runs: `83`
- Val runs: `18`
- Test runs: `19`

## Feature Contract
- `impact_velocity_m_s`
- `droplet_diameter_mm`
- `shell_outer_diameter_mm`
- `interfacial_layer_thickness_mm`
- `core_density_kg_m3`
- `core_viscosity_pa_s`
- `interfacial_tension_n_m`
- `penetration_depth_max_mm`
- `neck_radius_min_mm`
- `closure_time_ms`
- `detachment_time_ms`

## Success Head Metrics
| Split | Count | Accuracy | F1 | Macro-F1 |
|---|---:|---:|---:|---:|
| train | 83 | 1.0000 | 1.0000 | N/A |
| val | 18 | 1.0000 | 1.0000 | N/A |
| test | 19 | 1.0000 | 1.0000 | N/A |

## Regime Head Metrics
| Split | Count | Accuracy | F1 | Macro-F1 |
|---|---:|---:|---:|---:|
| train | 83 | 1.0000 | N/A | 1.0000 |
| val | 18 | 1.0000 | N/A | 1.0000 |
| test | 19 | 1.0000 | N/A | 1.0000 |

## Regression Head Metrics
### capsule_eccentricity
| Split | Count | MAE | RMSE |
|---|---:|---:|---:|
| train | 83 | 0.0000 | 0.0000 |
| val | 18 | 0.0008 | 0.0010 |
| test | 19 | 0.0012 | 0.0015 |

### shell_thickness_mean_um
| Split | Count | MAE | RMSE |
|---|---:|---:|---:|
| train | 83 | 0.0000 | 0.0000 |
| val | 18 | 60.0327 | 66.8423 |
| test | 19 | 73.3472 | 90.7404 |

## Calibration Summary
- Success head calibration:
  temperature: `0.0500`
  log-loss (uncalibrated -> final): `0.0101` -> `0.0000`
  brier (uncalibrated -> final): `0.0012` -> `0.0000`
  ECE (uncalibrated -> final): `0.0094` -> `0.0000`

## Data Loading Notes
- No data-loading warnings were recorded.

## Traceability
- Config SHA256: `5d6d5dc3e6614e0498b7b6a45b9b41ae0aca5b146fb6632122bfac275d72bcd7`
- Split SHA256: `9bb9c75157b5637c475d5b02f17413be6494e9aa349f6f846edd4d278338c37a`
- Model artifact: `INTERACT-Capsules/data/simulation/family_a/corpus/smoke_model_train_v1/manifests/models/smoke_family_a_multimodal_v1_pretrain.model.json`
- Eval artifact: `INTERACT-Capsules/data/simulation/family_a/corpus/smoke_model_train_v1/manifests/models/smoke_family_a_multimodal_v1_pretrain.eval.json`
- Calibration artifact: `INTERACT-Capsules/data/simulation/family_a/corpus/smoke_model_train_v1/manifests/models/smoke_family_a_multimodal_v1_pretrain.calibration.json`

## Known Limitations
- This artifact is for internal Family A MVP usage only.
- Smoke/surrogate results are not representative of production lab performance.
- Recommendations should be guarded with validated-domain checks before lab execution.
