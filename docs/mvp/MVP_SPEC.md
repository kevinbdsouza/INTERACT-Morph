# MVP-001: INTERACT-Morph MVP Specification

## Objective

Deliver an internal, experimentalist-facing tool for AI-guided inverse morphology design in impact-driven liquid-liquid encapsulation. The tool should transform high-speed videos, material descriptors, operating conditions, and morphology labels into a physics-aware forward model and a constrained inverse recommendation engine.

The experimentalist should be able to specify a target morphology and receive ranked operating conditions with uncertainty, nearby prior experiments, and failure-mode warnings.

## Users

- Primary user: lab experimentalist planning and executing liquid-liquid encapsulation experiments
- Secondary user: ML/software engineer maintaining data, model, calibration, and campaign pipelines
- Tertiary user: project reviewer assessing dataset, model, validation, and failure-mode evidence

## Required Inputs

- Material descriptors for core, shell-forming layer, host bath, and air-relevant conditions
- Fluid properties: density, viscosity, interfacial tensions, spreading parameters, and nondimensional groups
- Control settings: impact height or velocity, shell volume, effective interfacial-layer thickness, confinement geometry, and route type
- High-speed side-view/top-view videos and post-encapsulation images
- Segmentation masks, contours, landmarks, or correction queues where available
- Target design constraints such as shell thickness band, low trapped-air fraction, crown suppression, encapsulated volume, or layer sequence

## Required Outputs

- Wrapped/unwrapped probability
- Mode probability distribution: penetration, trapping, loop/confinement failure, overflow, or invalid route
- Morphology predictions:
  - `shell_thickness_mean_um`
  - `shell_thickness_nonuniformity`
  - `crown_index`
  - `trapped_air_fraction`
  - `encapsulated_volume`
  - `core_offset`
  - `layer_sequence` where multilayer labels are available
- Calibrated uncertainty intervals, reliability metrics, and abstention flags
- Out-of-domain and constraint-violation warnings
- Ranked top-k inverse recommendations with predicted morphology, uncertainty, nearest prior experiments, and rationale fields

## MVP Acceptance Gates

- G1 Data + baseline ready:
  - Canonical morphology-resolved dataset assembled and schema-validated
  - Reproducible train/validation/test split artifact exists
  - Thermodynamic/regime-map/tabular baseline benchmark artifacts exist
  - Dataset card or dataset inventory draft exists
- G2 Model usable:
  - Held-out mode prediction improves >=10-20% over thermodynamic/regime-map baselines on balanced accuracy or F1
  - Morphology regression reports shell thickness, trapped air, crown index, and encapsulated volume against pre-registered tolerances
  - Calibration report includes reliability evidence and abstention behavior
- G3 Planning value:
  - Model-guided planning reaches target morphology operating windows with >=30% fewer experiments versus grid or expert heuristic search
  - Top-3 recommendation success is reported for at least one prospective target-morphology campaign
- G4 Tool usable:
  - Lab user can run the end-to-end workflow through documented CLI/UI paths without developer intervention
  - Recommendation output exposes uncertainty, constraints, nearest examples, and failure-mode warnings
  - Model card, validation report, and failure-mode map are generated from current evidence

## In Scope

- Conventional impact-driven liquid-liquid encapsulation
- Penetration versus trapping modes
- Circular-loop-assisted constrained interfacial-layer operation
- Low-air, crown-control, shell-thickness, shell-uniformity, and encapsulated-volume target campaigns
- Limited multilayer route decision support when labels and feasible route metadata exist
- Selective fluorescence, dyeing, or microscopy calibration for difficult morphology labels
- Selected simulation or surrogate data for mechanistic comparison and smoke validation, not as the sole production evidence base

## Out Of Scope For This MVP

- Function-first release, targeting, reaction, or actuation optimization beyond morphology prerequisites
- Full automated experimentation
- Comprehensive 3D CFD or magnetic-coupled simulation coverage
- Broad viscoelastic, biological, or unvalidated material-family generalization
- External/public release hardening

## Traceability

This specification maps to [ToDo.md](ToDo.md) tasks MVP-001 through MVP-042 and to the revised proposal at workspace path `docs/INTERACT-Morph_SchmidtSciences_Revised.docx`.
