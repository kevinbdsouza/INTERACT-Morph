# INTERACT-Morph MVP ToDo

## 1) MVP Definition

### MVP Objective

Deliver a lab-usable inverse morphology design tool for impact-driven liquid-liquid encapsulation. The MVP should:

- Predict wrapped/unwrapped outcome and penetration/trapping/confinement failure mode
- Predict morphology targets: shell thickness, thickness nonuniformity, crown index, trapped air, encapsulated volume, core offset, and selected layer sequence labels
- Rank top-k experimental conditions for a target morphology with calibrated uncertainty
- Explain recommendations with nearest prior experiments, constraint checks, and failure-mode warnings
- Run through reproducible CLI workflows plus a lightweight review UI for experimentalists

### In Scope For MVP

- Existing and new experiments from conventional impact-driven liquid-liquid encapsulation
- Penetration/trapping boundaries, low-air operating windows, crown-forming density contrasts, and shell-thickness control
- Circular-loop-assisted constrained interfacial-layer operation and loop minimum-volume/overflow limits
- Limited multilayer decision support where route and layer-sequence labels exist
- Video segmentation, trajectory extraction, morphology-label QA, model training, calibration, recommendation, prospective campaign analysis, and governance artifacts

### Out Of Scope For MVP

- Function-first optimization for release, reaction, targeting, or actuation
- Full automated experimentation
- Comprehensive 3D CFD or magnetic-coupled simulation coverage
- Broad external/public release hardening
- Unsupported material domains such as unvalidated viscoelastic or poor-imaging cases

## 2) Delivery Gates And Success Criteria

- Gate G1 (Data + baseline ready): morphology-resolved canonical dataset, schema validation, split artifact, dataset card/inventory, and baseline benchmark complete
- Gate G2 (Model usable): mode prediction improves >=10-20% over thermodynamic/regime-map baselines; morphology regression reported against pre-registered tolerances; calibration/abstention report complete
- Gate G3 (Planning value): model-guided search reaches target morphology with >=30% fewer experiments versus grid or expert heuristic search; top-3 recommendation success reported
- Gate G4 (Tool usable): lab user can run documented CLI/UI workflows and inspect uncertainty, nearest evidence, constraints, and failure-mode warnings

## 3) Detailed Implementation Backlog

Legend: `P0` critical, `P1` important, `P2` optional for MVP.

| ID | Priority | Task | Concrete Deliverable | Depends On |
|---|---|---|---|---|
| MVP-001 | P0 | Finalize revised INTERACT-Morph scope and target outputs | Updated MVP spec covering morphology-first inverse design | - |
| MVP-002 | P0 | Define experiment metadata schema | Versioned schema for fluids, setup, route, confinement, outcomes, imaging, and quality flags | MVP-001 |
| MVP-003 | P0 | Define derived morphology feature schema | Standard fields for penetration depth, cavity radius, closure time, shell thickness, trapped air, crown index, volume, core offset, and layer sequence | MVP-002 |
| MVP-004 | P0 | Build raw data inventory | Catalog of existing high-speed videos, post images, metadata, material families, route types, and annotation state | MVP-002 |
| MVP-005 | P0 | Build ingestion pipeline | Scripted import into canonical dataset layout with source ID preservation and deterministic canonical IDs | MVP-004 |
| MVP-006 | P0 | Implement data validation checks | Schema checks, missing-value checks, unit checks, asset checks, and route/confinement consistency checks | MVP-005 |
| MVP-007 | P0 | Implement dataset versioning | Snapshot manifest and dataset card inputs for every training/validation dataset | MVP-005 |
| MVP-008 | P0 | Define split policy | Random plus held-out material, operating-window, and route/confinement splits | MVP-006 |
| MVP-009 | P0 | Build baseline benchmark | Thermodynamic/regime-map/tabular baseline report for mode and morphology targets | MVP-008 |
| MVP-010 | P0 | Annotation guideline for key events and morphology labels | Protocol for mode labels, failure modes, event landmarks, shell metrics, air, crown, and layer sequence | MVP-003 |
| MVP-011 | P0 | Train/validate interface segmentation model | QC report for core, shell lens, host interface, air cavity, loop boundary, and final cargo masks | MVP-010 |
| MVP-012 | P0 | Build contour and trajectory extractor | Deterministic dynamic-observable extraction from masks, contours, and frames | MVP-011 |
| MVP-013 | P0 | Build morphology feature QA reports | Automated reports for trajectory sanity, missingness, outliers, and morphology proxy reliability | MVP-012 |
| MVP-014 | P1 | Active correction loop for labels and masks | Review queue for mis-segmentation, ambiguous labels, and high-impact training errors | MVP-013 |
| MVP-015 | P1 | Stand up selected simulation/surrogate workflow | Configurable sweep or surrogate generation for mechanistic comparison and smoke tests | MVP-001 |
| MVP-016 | P1 | Define simulation parameter ranges | DOE ranges for velocity, shell volume, layer thickness, density/viscosity/tension ratios, and confinement | MVP-015 |
| MVP-017 | P1 | Generate first synthetic/surrogate corpus | Minimum viable corpus with metadata parity to experimental runs | MVP-016 |
| MVP-018 | P1 | Validate simulation realism envelope | Comparison report between simulated/surrogate and experimental observable distributions | MVP-017, MVP-012 |
| MVP-019 | P0 | Design physics-aware multimodal architecture | Spec for material/process descriptors, dynamic observables, learned shape tokens, and multitask heads | MVP-008, MVP-012 |
| MVP-020 | P0 | Implement training pipeline | Reproducible train/eval with config-driven experiments and model artifacts | MVP-019 |
| MVP-021 | P1 | Run synthetic pretraining where useful | Pretraining checkpoint and logs with documented limitations | MVP-020, MVP-017 |
| MVP-022 | P0 | Run experimental fine-tuning/training | Experimental model with held-out mode and morphology reporting | MVP-020, MVP-008 |
| MVP-023 | P0 | Build uncertainty calibration module | Ensemble/temperature/isotonic/conformal-style calibration and reliability report | MVP-022 |
| MVP-024 | P0 | Generate model card | Model card with scope, inputs, outputs, calibration, unsupported domains, and failure modes | MVP-023 |
| MVP-025 | P0 | Implement morphology target objective | Multi-objective scoring for target shell thickness, air, crown, volume, mode, uncertainty, and cost | MVP-023 |
| MVP-026 | P0 | Implement acquisition strategy | EI/UCB or mixed-variable acquisition for top-k candidate ranking | MVP-025 |
| MVP-027 | P0 | Add recommendation guardrails | Reject or warn on out-of-domain materials, invalid loop volumes, infeasible route order, poor confidence, and extrapolation | MVP-026 |
| MVP-028 | P0 | Maintain stable CLI command surface | Commands for ingest, validate, train, calibrate, recommend, campaign, and report workflows | MVP-020, MVP-025 |
| MVP-029 | P0 | Implement end-to-end CLI workflows | Config file support, run artifacts, smoke checks, and operator-friendly failure messages | MVP-028 |
| MVP-030 | P1 | Lightweight recommendation review UI | Inspect ranked recommendations, target closeness, uncertainty, nearest examples, and rejection reasons | MVP-029 |
| MVP-031 | P0 | Experiment execution template | Protocol for model-recommended conditions, operator fields, morphology targets, and post-run logging | MVP-026 |
| MVP-032 | P0 | Prospective campaign: low-air or shell-thickness target | Model-guided versus baseline campaign with measured outcomes | MVP-031 |
| MVP-033 | P0 | Prospective campaign: robustness or crown-control target | Held-out material/window campaign with measured outcomes | MVP-032 |
| MVP-034 | P0 | Analyze reduction in experimental load | Report on >=30% experiment-reduction target and top-3 recommendation success | MVP-033 |
| MVP-035 | P0 | Build failure-mode map | Error taxonomy for unsupported fluids, poor imaging, invalid loop volumes, out-of-range groups, and infeasible routes | MVP-023, MVP-033 |
| MVP-036 | P0 | Reproducibility hardening | Seed control, environment lockfile, deterministic evaluation scripts, and smoke-check bundle | MVP-029 |
| MVP-037 | P0 | Documentation bundle | Setup guide, runbook, troubleshooting, operator quickstart, and workflow index | MVP-029, MVP-035 |
| MVP-038 | P1 | Internal handoff session | Walkthrough checklist and evidence pack for independent lab use | MVP-037 |
| MVP-039 | P0 | MVP go/no-go review | Decision memo against G1-G4 gates | MVP-034, MVP-037 |
| MVP-040 | P1 | Follow-on roadmap draft | Plan for function-first release/reaction/actuation, automated experiments, and external deployment | MVP-039 |
| MVP-041 | P0 | Rename public project docs to INTERACT-Morph | README, MVP spec, todo, and progress tracker aligned with revised proposal | MVP-001 |
| MVP-042 | P1 | Rename internal package/CLI from capsules to morph | Package/module/entrypoint/config/test migration plan and implementation | MVP-041 |

## 4) Execution Checklist By Workstream

### A. Data, Labels, And Morphology Features

Current status note (2026-04-30): Raw handoff, inventory, ingestion, validation, split, snapshot, annotation, segmentation, trajectory, feature QA, and correction-queue scaffolds already exist and have smoke evidence from synthetic placeholder data. Production morphology evidence is still blocked on the real experimental archive and annotation/mask handoff.

- [x] MVP-001
- [x] MVP-002
- [x] MVP-003
- [ ] MVP-004
- [ ] MVP-005
- [ ] MVP-006
- [ ] MVP-007
- [ ] MVP-008
- [x] MVP-010
- [ ] MVP-011
- [ ] MVP-012
- [ ] MVP-013
- [ ] MVP-014

### B. Simulation And Mechanistic Comparison

Current status note (2026-04-30): DOE planning, synthetic corpus generation, and realism-report scaffolds exist. Simulation remains supporting evidence, not the production data source.

- [ ] MVP-015
- [ ] MVP-016
- [ ] MVP-017
- [ ] MVP-018

### C. Modeling, Calibration, And Documentation

Current status note (2026-04-30): Multimodal training, synthetic pretraining, fine-tuning, calibration, and model-card workflows exist and are smoke-validated. They must be re-run on real morphology-resolved experimental data before G2 can be claimed.

- [ ] MVP-019
- [ ] MVP-020
- [ ] MVP-021
- [ ] MVP-022
- [ ] MVP-023
- [ ] MVP-024

### D. Inverse Recommendation Engine

Current status note (2026-04-30): Recommendation objective, EI/UCB scoring, guardrail rejection, and HTML review UI scaffolds exist. The objective now needs target-morphology tuning for shell thickness, trapped air, crown, volume, confinement limits, and route feasibility.

- [ ] MVP-025
- [ ] MVP-026
- [ ] MVP-027
- [ ] MVP-030

### E. Productization And Reproducibility

Current status note (2026-04-30): CLI, smoke checks, lockfile, deterministic checks, setup/runbook/quickstart/troubleshooting docs, and governance pack scaffolds exist. Public docs now use INTERACT-Morph, while the internal command remains `interact-capsules` until MVP-042 is implemented.

- [ ] MVP-028
- [ ] MVP-029
- [ ] MVP-036
- [ ] MVP-037
- [ ] MVP-038
- [x] MVP-041
- [ ] MVP-042

### F. Prospective Validation And Governance

Current status note (2026-04-30): Execution templates, campaign preparation, campaign analysis, failure analysis, go/no-go, and roadmap generation scaffolds exist. Production campaign evidence is still required.

- [ ] MVP-031
- [ ] MVP-032
- [ ] MVP-033
- [ ] MVP-034
- [ ] MVP-035
- [ ] MVP-039
- [ ] MVP-040

## 5) Suggested 18-Month Timeline

- Months 1-3: data foundation, schema, dataset card, segmentation/tracking starter, baseline thermodynamic/regime-map models
- Months 4-6: targeted conventional and loop-assisted experiments across impact height, shell volume, penetration/trapping boundary, low-air region, and loop window
- Months 7-9: first observable-aware multitask model, held-out operating-window tests, baseline comparison
- Months 10-12: morphology regression, uncertainty calibration, out-of-domain checks, targeted fluorescence/microscopy calibration
- Months 13-15: inverse recommendation engine, limited multilayer decision layer, first prospective target-morphology campaigns
- Months 16-18: prospective validation, software release, benchmark workflows, model card, dataset card, and failure-mode map

## 6) Critical Risks To Watch

- Morphology labels are difficult to measure consistently at scale
- Simulation or surrogate data may overstate model quality relative to experiments
- Rare but important failure modes remain under-sampled
- Recommendation engine may over-explore outside validated material or confinement domains
- Loop-assisted and multilayer route constraints may require stricter guardrails than the current scaffold implements
- Tooling may remain usable by developers but not yet independent experimentalists
