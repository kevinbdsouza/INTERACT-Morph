# Post-MVP Roadmap Draft (MVP-040)

- Generated: `2026-04-24T21:08:27.223573+00:00`
- Decision context: `NO_GO`

## Phases

### Phase 1 (0-4 weeks)

Close MVP evidence gaps for data readiness and model usability.

- Run first production Family A ingestion + validation pass
- Execute first production model/fine-tune/calibration cycle
- Triage top failure clusters and close correction loop

### Phase 2 (5-8 weeks)

Complete prospective validation and operator usability proof.

- Run model-guided vs baseline campaigns with real logs
- Quantify experiment reduction versus baseline
- Run internal handoff and record independent operator results

### Phase 3 (Post-MVP start)

Prepare Family B/C extension once MVP gates are satisfied.

- Define Family B/C schema deltas and simulation requirements
- Prioritize instrumentation and data needs for multi-layer behaviors
- Draft staged release plan for broader internal deployment

## Carryover Tasks

| Task ID | Task | Status | Due Date |
|---|---|---|---|
| MVP-004 | Build raw data inventory | In Progress | 2026-04-19 |
| MVP-005 | Build ingestion pipeline | In Progress | 2026-04-20 |
| MVP-006 | Implement data validation checks | In Progress | 2026-04-20 |
| MVP-007 | Implement dataset versioning | In Progress | 2026-04-21 |
| MVP-008 | Define train/val/test policy | In Progress | 2026-04-21 |
| MVP-009 | Build baseline heuristic benchmark | In Progress | 2026-04-21 |
| MVP-011 | Train/validate interface segmentation model | In Progress | 2026-04-30 |
| MVP-012 | Build contour and trajectory extractor | In Progress | 2026-05-01 |
| MVP-013 | Build feature QA dashboards | In Progress | 2026-05-01 |
| MVP-014 | Active error-correction loop for labels | In Progress | 2026-05-03 |
| MVP-015 | Stand up axisymmetric simulation workflow | In Progress | 2026-04-23 |
| MVP-016 | Define simulation parameter ranges | In Progress | 2026-04-23 |
| MVP-017 | Generate first simulation corpus | In Progress | 2026-04-24 |
| MVP-018 | Validate simulation realism envelope | In Progress | 2026-04-25 |
| MVP-019 | Design multimodal model architecture | In Progress | 2026-04-29 |
| MVP-020 | Implement training pipeline | In Progress | 2026-04-30 |
| MVP-021 | Simulation pretraining run | In Progress | 2026-05-01 |
| MVP-022 | Experimental fine-tuning run | In Progress | 2026-05-02 |
| MVP-023 | Build uncertainty calibration module | In Progress | 2026-05-02 |
| MVP-024 | Define model-card template | In Progress | 2026-05-02 |
