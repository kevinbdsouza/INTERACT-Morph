# Experiment Execution Template (MVP-031)

- Campaign ID: `C3_SMOKE_20260418`
- Generated: `2026-04-18T04:48:17.220041+00:00`
- Source recommendation report: `data/simulation/family_a/corpus/smoke_model_train_v1/manifests/models/smoke_family_a_multimodal_v1_pretrain.recommendations.cli.json`
- Planned runs: `5`

## Objective

Execute model-guided Family A experiments against target shell-thickness and capsule-shape windows with standardized capture and safety controls.

## Pre-Run Checklist

- [ ] Confirm model artifact, calibration artifact, and recommendation report hashes are recorded.
- [ ] Confirm fluid preparation lot IDs and instrument calibration records are attached for this campaign.
- [ ] Confirm guardrail warnings in planned runs were reviewed and accepted by operator + reviewer.

## Planned Runs

| Rank | Planned Run ID | Candidate ID | Success Prob | Thickness (um) | Eccentricity | Guardrail |
|---:|---|---|---:|---:|---:|---|
| 1 | A_EXP_001 | SIM_A_000214 | 1 | 237.65 | 0.149 | accepted |
| 2 | A_EXP_002 | SIM_A_000457 | 1 | 237.76 | 0.149 | accepted |
| 3 | A_EXP_003 | SIM_A_000421 | 1 | 199.6 | 0.1488 | accepted |
| 4 | A_EXP_004 | SIM_A_000178 | 1 | 199.61 | 0.1488 | accepted |
| 5 | A_EXP_005 | SIM_A_000430 | 1 | 199.51 | 0.1482 | accepted |

## Per-Run Measurements

- [ ] Record final executed control parameters and any operator overrides.
- [ ] Record encapsulation success/failure and primary failure mode.
- [ ] Record shell_thickness_mean_um and capsule_eccentricity with method provenance.
- [ ] Record notable anomalies (drift, imaging occlusion, unstable jetting, delayed closure).

## Stop Conditions

- [ ] Pause if three consecutive severe safety/process anomalies occur.
- [ ] Pause if measured values repeatedly diverge from expected guardrail-safe envelope.
- [ ] Pause if instrumentation calibration check fails during campaign.
