# MVP-001: INTERACT-Capsules MVP Specification (Family A)

## Objective
Deliver an internal, experimentalist-facing tool for **Family A** (baseline and constrained interfacial layer encapsulation) that predicts encapsulation outcomes and recommends next experiments with uncertainty.

## Users
- Primary user: lab experimentalist running impact-driven encapsulation experiments
- Secondary user: ML/software engineer maintaining model and data pipelines

## Required Inputs
- Fluid properties (core/shell/interfacial layer): density, viscosity, interfacial tension, material identifiers
- Control settings: impact height/velocity, droplet/shell geometry, layer thickness
- High-speed video run data
- Target design constraints for inverse planning (e.g., shell thickness band)

## Required Outputs
- `encapsulation_success_probability`
- `regime_label_probability_distribution`
- `failure_mode_probability_distribution`
- Predicted geometry metrics: `shell_thickness_mean_um`, `capsule_eccentricity`
- Uncertainty metrics (calibrated confidence/reliability)
- Ranked next-experiment recommendations with rationale fields

## MVP Acceptance Gates
- G1 Data + baseline ready:
  - Family A canonical dataset assembled and schema-validated
  - Reproducible train/val/test split artifact exists
  - Baseline heuristic benchmark artifact exists
- G2 Model usable:
  - Held-out Family A macro-F1 >= 0.80
  - Calibration report included (ECE/Brier or equivalent)
- G3 Planning value:
  - Model-guided planning reaches target operating window with >=30% fewer experiments versus grid search
- G4 Tool usable:
  - Lab user can execute end-to-end workflow via CLI without developer intervention

## Non-goals for MVP
- Production-grade support for Family B/C
- Full 3D magnetic-coupled modeling stack
- External/public platform release

## Traceability
This document maps directly to `docs/mvp/ToDo.md` tasks MVP-001 through MVP-010 (and supports later gates).
