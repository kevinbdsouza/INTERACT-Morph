# INTERACT-Morph MVP Progress Tracking

## 1) How To Use This Tracker

- Update this file at least once per week.
- Keep status values to: `Not Started`, `In Progress`, `At Risk`, `Blocked`, `Done`.
- Link every update to a [ToDo.md](ToDo.md) task ID.
- Do not mark a milestone `Done` unless its acceptance criteria are evidenced by production or prospective validation artifacts.

## 2) Current Snapshot

- Date: 2026-04-30
- Sprint/Week: W02 revision checkpoint
- Overall status: In Progress
- Confidence to hit MVP date (High/Medium/Low): Medium
- Biggest blocker: Real morphology-resolved experimental archive and production annotation/mask handoff are not yet ingested
- Next decision needed: Confirm first production raw data location, route/confinement metadata completeness, and whether canonical run IDs should be preserved or canonicalized after `handoff-check`

## 3) Milestone Status Board

| Milestone | Target Date | Status | Acceptance Criteria | Evidence Link/Note |
|---|---|---|---|---|
| G1 Data + Baseline Ready | TBD | Not Started | Morphology-resolved canonical dataset + schema validation + split artifact + dataset card/inventory + baseline benchmark | Smoke-only placeholder artifacts exist; production archive pending |
| G2 Model Usable | TBD | Not Started | >=10-20% improvement over thermodynamic/regime-map baselines; morphology regression vs tolerances; calibration/abstention report | Training/calibration scaffolds exist; production model evidence pending |
| G3 Planning Value | TBD | Not Started | >=30% fewer experiments vs grid/expert heuristic; top-3 recommendation success reported | Campaign scaffolds exist; prospective outcomes pending |
| G4 Tool Usable | TBD | In Progress | Lab user runs documented CLI/UI workflow and can inspect uncertainty, constraints, nearest evidence, and failure warnings | CLI/UI/governance scaffolds and smoke checks exist; independent operator evidence pending |

## 4) Task Progress

| Task ID | Owner | Status | Start Date | Due Date | Notes |
|---|---|---|---|---|---|
| MVP-001 | Codex | Done | 2026-04-17 | 2026-04-30 | Revised `docs/mvp/MVP_SPEC.md` now reflects INTERACT-Morph morphology-first inverse design scope |
| MVP-002 | Codex | Done | 2026-04-17 | 2026-04-30 | `schemas/run_metadata.schema.json` now covers route, confinement, loop geometry, host bath, core/shell/layer fluids, controls, outcomes, imaging, and quality flags |
| MVP-003 | Codex | Done | 2026-04-17 | 2026-04-30 | `schemas/derived_features.schema.json` and templates now expose penetration, cavity radius, closure timing, shell thickness, trapped air, crown, volume, core offset, and layer sequence fields |
| MVP-004 | Codex | In Progress | 2026-04-17 | TBD | Inventory tooling exists and smoke data passed; awaiting real conventional, loop-assisted, and selected multilayer archive |
| MVP-005 | Codex | In Progress | 2026-04-17 | TBD | Ingestion supports canonical/source ID mapping; production run pending |
| MVP-006 | Codex | In Progress | 2026-04-17 | TBD | Validation checks exist; production-specific route/confinement consistency checks still need real data |
| MVP-007 | Codex | In Progress | 2026-04-17 | TBD | Snapshot tooling and `dataset-card` generator exist; production dataset card evidence pending |
| MVP-008 | Codex | In Progress | 2026-04-17 | TBD | Split generation exists; revised held-out material/window/route policy needs production review |
| MVP-009 | Codex | In Progress | 2026-04-17 | TBD | Baseline benchmark scaffold exists; revised thermodynamic/regime-map comparison must be run on production data |
| MVP-010 | Codex | Done | 2026-04-17 | 2026-04-18 | Annotation guideline exists; revise as needed for crown, air, volume, loop failure, and layer sequence labels |
| MVP-011 | Codex | In Progress | 2026-04-18 | TBD | Segmentation starter model and QC artifact exist on smoke data; production masks needed |
| MVP-012 | Codex | In Progress | 2026-04-18 | TBD | Contour/trajectory extractor exists; production dynamic-observable QA pending |
| MVP-013 | Codex | In Progress | 2026-04-18 | TBD | Feature QA report scaffold exists; morphology proxy reliability needs real examples |
| MVP-014 | Codex | In Progress | 2026-04-18 | TBD | Correction-queue workflow exists; first real correction sprint pending |
| MVP-015 | Codex | In Progress | 2026-04-17 | TBD | Axisymmetric/DOE planning scaffold exists as supporting evidence |
| MVP-016 | Codex | In Progress | 2026-04-17 | TBD | DOE range config exists; revise for shell volume, loop geometry, and route constraints |
| MVP-017 | Codex | In Progress | 2026-04-17 | TBD | Synthetic/surrogate corpus generation exists and is smoke-validated |
| MVP-018 | Codex | In Progress | 2026-04-17 | TBD | Realism report scaffold exists; production comparison pending |
| MVP-019 | Codex | In Progress | 2026-04-18 | TBD | Multimodal architecture spec exists; revise language from Family A endpoint prediction to morphology-first multitask model |
| MVP-020 | Codex | In Progress | 2026-04-18 | TBD | Training pipeline exists and is smoke-validated |
| MVP-021 | Codex | In Progress | 2026-04-18 | TBD | Synthetic pretraining artifacts exist; should remain supporting evidence only |
| MVP-022 | Codex | In Progress | 2026-04-18 | TBD | Fine-tuning support exists; production experimental run pending |
| MVP-023 | Codex | In Progress | 2026-04-18 | TBD | Calibration artifacts now include placeholder abstention summaries and split-conformal probability-set diagnostics; production reliability evidence pending |
| MVP-024 | Codex | In Progress | 2026-04-18 | TBD | Model-card generation now renders output contract, morphology target heads, calibration/abstention/conformal summary, unsupported domains, and traceability |
| MVP-025 | Codex | In Progress | 2026-04-18 | TBD | Recommendation objective retuned in config for shell thickness, trapped air, crown, encapsulated volume, eccentricity, and uncertainty penalty |
| MVP-026 | Codex | In Progress | 2026-04-18 | TBD | EI/UCB acquisition scoring exists |
| MVP-027 | Codex | In Progress | 2026-04-18 | TBD | Guardrails now emit explicit route, confinement, circular-loop volume-window, shell-volume, multilayer-sequence, confidence, extrapolation, and nearest-evidence diagnostics |
| MVP-028 | Codex | Done | 2026-04-17 | 2026-04-30 | Stable CLI command surface is exposed as `interact-morph` across package metadata, parser help, docs, tests, and smoke workflows |
| MVP-029 | Codex | In Progress | 2026-04-17 | TBD | End-to-end CLI pipeline and smoke-check workflow exist |
| MVP-030 | Codex | In Progress | 2026-04-18 | TBD | HTML recommendation review UI rebuilt from placeholder recommendations after objective/guardrail update; production display review pending |
| MVP-031 | Codex | In Progress | 2026-04-18 | TBD | Experiment execution template scaffold exists |
| MVP-032 | Lab/Codex | Not Started | TBD | TBD | First low-air or shell-thickness prospective campaign pending production model |
| MVP-033 | Lab/Codex | Not Started | TBD | TBD | Crown-control or held-out robustness campaign pending first campaign |
| MVP-034 | Codex | In Progress | 2026-04-18 | TBD | Campaign analysis scaffold exists; production campaign data pending |
| MVP-035 | Codex | In Progress | 2026-04-18 | TBD | Failure analysis scaffold exists; production error taxonomy pending |
| MVP-036 | Codex | In Progress | 2026-04-18 | TBD | Repro lock, deterministic check, and smoke-check workflows exist |
| MVP-037 | Codex | In Progress | 2026-04-18 | TBD | Setup, runbook, quickstart, and troubleshooting docs exist with INTERACT-Morph command naming; independent operator walkthrough still pending |
| MVP-038 | Codex/Lab | In Progress | 2026-04-18 | TBD | Governance/handoff pack scaffold exists; independent lab walkthrough pending |
| MVP-039 | Codex/Lab | In Progress | 2026-04-18 | TBD | Go/no-go generation scaffold exists; expected NO_GO until G1-G4 evidence is real |
| MVP-040 | Codex/Lab | In Progress | 2026-04-18 | TBD | Follow-on roadmap scaffold exists |
| MVP-041 | Codex | Done | 2026-04-30 | 2026-04-30 | Moved project folder to `INTERACT-Morph` and updated README, MVP spec, todo, and progress tracker to revised proposal scope |
| MVP-042 | Codex | Done | 2026-04-30 | 2026-04-30 | Internal package/module/CLI renamed to `interact_morph`/`interact-morph`; compatibility artifacts updated in docs, scripts, tests, schemas, and smoke reports |

## 5) KPI Dashboard

| KPI | Target | Current | Trend | Status | Last Updated |
|---|---|---|---|---|---|
| Morphology-resolved labeled runs | >=1200 target to confirm with lab | 0 production | Flat | Not Started | 2026-04-30 |
| Valid runs after QA (%) | >=95% | 0% production | Flat | Not Started | 2026-04-30 |
| Segmentation quality (IoU/F1) | Team-defined threshold | Smoke-only: starter synthetic metric exists | Flat | In Progress | 2026-04-30 |
| Mode prediction improvement vs baseline | >=10-20% | N/A production | Flat | Not Started | 2026-04-30 |
| Shell thickness error | Pre-registered tolerance | N/A production | Flat | Not Started | 2026-04-30 |
| Trapped-air/crown/volume error | Pre-registered tolerance | N/A production | Flat | Not Started | 2026-04-30 |
| Calibration quality | Reliable intervals and abstention behavior | N/A production | Flat | Not Started | 2026-04-30 |
| Recommendation top-3 success | Reported per campaign | N/A production | Flat | Not Started | 2026-04-30 |
| Experiment reduction vs grid/search | >=30% | N/A production | Flat | Not Started | 2026-04-30 |
| Independent operator workflow | No developer intervention | Smoke-only | Flat | In Progress | 2026-04-30 |

## 6) Experimental Campaign Tracker

| Campaign ID | Goal | Route/Domain | Planned Runs | Completed Runs | Status | Notes |
|---|---|---|---|---|---|---|
| C1 | Baseline morphology map | Conventional impact | TBD | 0 | Not Started | Production archive/handoff pending |
| C2 | Constrained-layer loop window | Circular-loop-assisted confinement | TBD | 0 | Not Started | Needs loop geometry and volume metadata |
| C3 | Low-air or shell-thickness inverse target | Model-guided versus baseline | TBD | 0 | Not Started | Depends on production model and recommendation output |
| C4 | Crown-control or held-out robustness target | Held-out material/window | TBD | 0 | Not Started | Depends on C3 |
| C5 | Limited layer-sequence feasibility | Selected multilayer route | TBD | 0 | Not Started | Optional; depends on labeled route/sequence data |

## 7) Model Registry Tracker

| Model ID | Data Version | Task | Key Metrics | Calibration | Deployed For Recommendations | Notes |
|---|---|---|---|---|---|---|
| smoke_family_a_segmentation_v1 | synthetic_smoke_model_train_v1 | Segmentation starter | Smoke-only IoU/F1 artifact exists | N/A | N | Not production representative |
| smoke_family_a_multimodal_v1_rerun | synthetic_smoke_model_train_v1 | Multimodal predictor prototype | Smoke-only classification/regression artifacts exist | Pending | N | Surrogate-only |
| interact_morph_multimodal_v1 | TBD production | Morphology-first multitask model | Pending | Pending | N | Target production model ID |

## 8) Risk Register

| Risk ID | Description | Likelihood | Impact | Status | Mitigation | Owner |
|---|---|---|---|---|---|---|
| R1 | Morphology labels are noisy or expensive to measure | Medium | High | Open | Separate direct labels from image-derived proxies; use targeted fluorescence/microscopy calibration | Lab/Codex |
| R2 | Simulation/surrogate evidence overstates production model quality | Medium | High | Open | Treat simulation as support only; report experimental held-out and prospective metrics separately | Codex |
| R3 | Rare failure modes remain under-sampled | High | Medium | Open | Use active learning and targeted failure-mode campaigns | Lab/Codex |
| R4 | Recommendation over-extrapolates outside validated material/confinement domain | Medium | High | Open | Domain guardrails, uncertainty thresholds, abstention, and nearest-evidence reporting | Codex |
| R5 | Loop and multilayer constraints need production validation | Medium | Medium | Open | Schema fields now exist for route, loop geometry, and layer sequence; tighten required fields after first production handoff | Codex/Lab |
| R6 | Tooling remains developer-friendly but not lab-operator-friendly | Medium | High | Open | Operator walkthrough, quickstart cleanup, UI review, and governance evidence | Codex/Lab |

## 9) Blockers And Escalations

| Date | Blocker | Affected Tasks | Owner | Escalation Needed | Resolution ETA |
|---|---|---|---|---|---|
| 2026-04-30 | Production morphology-resolved raw data handoff not yet available for first canonical pipeline run | MVP-004 to MVP-014; MVP-018; MVP-022 to MVP-027; MVP-032 to MVP-040 | Schmidt Interact / lab data owner | Confirm raw data location, metadata completeness, label/mask availability, and first `handoff-check` window | TBD |

## 10) Decisions Log

| Date | Decision | Reason | Impacted Tasks | Owner |
|---|---|---|---|---|
| 2026-04-30 | Public project scope is INTERACT-Morph | Revised Schmidt Sciences proposal frames the project as morphology-first inverse design | MVP-001, MVP-041 | Codex |
| 2026-04-30 | Use `interact-morph` as the public package and CLI command | Align implementation with the revised INTERACT-Morph scope and README command surface | MVP-028, MVP-042 | Codex |

## 11) Weekly Update Log

### 2026-04-30 (Week 02 Revision Checkpoint)

- Completed: Updated README, MVP spec, todo, and progress tracking files to match the revised INTERACT-Morph proposal: morphology-first inverse design, shell metrics, trapped air, crown, volume, loop-assisted confinement, limited multilayer route support, calibrated uncertainty, and prospective target-morphology campaigns.
- Completed: Renamed the package and command surface to `interact_morph` / `interact-morph`.
- Completed: Extended the metadata and derived-feature schemas/templates for route, confinement, loop geometry, host bath, trapped air, crown, volume, core offset, and layer sequence fields.
- Completed: Advanced the next in-progress modeling/recommendation tasks with placeholder evidence: calibration now reports abstention and conformal diagnostics; model cards include output contract, unsupported domains, and calibration summaries; recommendation config/objective includes trapped air, crown, encapsulated volume, loop volume windows, and multilayer route guardrails.
- Completed: Regenerated smoke placeholder calibration, calibrated predictions, model card, recommendation report, and recommendation UI from the updated code/config.
- In progress: Existing implementation scaffolds remain intact for data ingestion, validation, segmentation, trajectory extraction, modeling, calibration, recommendation, campaign analysis, smoke checks, and governance.
- Blocked: Production experimental data, labels, masks, and prospective campaign outcomes are still required before G1-G4 can be closed.
- Next-week plan: run `handoff-check` on the real raw data folder once available, revise schemas for route/confinement/layer-sequence metadata gaps, then re-run pipeline/baseline/model/recommendation artifacts under an `interact_morph_v1` dataset version.
