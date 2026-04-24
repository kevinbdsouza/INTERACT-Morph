# Failure-Mode Analysis (MVP-035)

- Generated: `2026-04-18T04:48:27.027447+00:00`
- Predictions: `data/simulation/family_a/corpus/smoke_model_train_v1/manifests/models/smoke_family_a_multimodal_v1_pretrain.predictions.jsonl`
- Runs scanned: `120`
- Runs with failures: `27`

## Failure Taxonomy

| Failure Code | Count |
|---|---:|
| high_abs_error:shell_thickness_mean_um | 27 |

## Highest-Severity Runs

| Run ID | Split | Severity | Reasons |
|---|---|---:|---|
| A_SIM_A_000001 | val | 2 | high_abs_error:shell_thickness_mean_um |
| A_SIM_A_000003 | test | 2 | high_abs_error:shell_thickness_mean_um |
| A_SIM_A_000009 | test | 2 | high_abs_error:shell_thickness_mean_um |
| A_SIM_A_000010 | test | 2 | high_abs_error:shell_thickness_mean_um |
| A_SIM_A_000011 | val | 2 | high_abs_error:shell_thickness_mean_um |
| A_SIM_A_000014 | val | 2 | high_abs_error:shell_thickness_mean_um |
| A_SIM_A_000015 | val | 2 | high_abs_error:shell_thickness_mean_um |
| A_SIM_A_000016 | test | 2 | high_abs_error:shell_thickness_mean_um |
| A_SIM_A_000055 | val | 2 | high_abs_error:shell_thickness_mean_um |
| A_SIM_A_000057 | test | 2 | high_abs_error:shell_thickness_mean_um |
| A_SIM_A_000063 | test | 2 | high_abs_error:shell_thickness_mean_um |
| A_SIM_A_000064 | test | 2 | high_abs_error:shell_thickness_mean_um |
| A_SIM_A_000065 | val | 2 | high_abs_error:shell_thickness_mean_um |
| A_SIM_A_000068 | val | 2 | high_abs_error:shell_thickness_mean_um |
| A_SIM_A_000069 | val | 2 | high_abs_error:shell_thickness_mean_um |

## Recommended Actions

- Prioritize shell-thickness feature quality checks and retrain with updated regression weighting.
