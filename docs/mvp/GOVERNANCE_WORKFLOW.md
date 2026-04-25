# MVP-038/039/040: Governance Workflow

## Goal
Generate governance artifacts from tracker state:
- internal handoff session pack (`MVP-038`)
- go/no-go memo against G1-G4 gates (`MVP-039`)
- post-MVP roadmap draft (`MVP-040`)

## CLI Command
```bash
interact-capsules mvp-governance \
  --progress-tracker docs/mvp/Progress_Tracking.md \
  --todo docs/mvp/ToDo.md \
  --config configs/mvp/family_a_mvp_governance_v1.json \
  --output-dir data/canonical/family_a/manifests/reports \
  --prefix family_a_mvp
```

## Script Entry Point
```bash
python3 scripts/build_mvp_governance_pack.py \
  --progress-tracker docs/mvp/Progress_Tracking.md \
  --todo docs/mvp/ToDo.md \
  --config configs/mvp/family_a_mvp_governance_v1.json \
  --output-dir data/canonical/family_a/manifests/reports \
  --prefix family_a_mvp
```

## Outputs
- `<prefix>.handoff.{json,md}`
- `<prefix>.go_no_go.{json,md}`
- `<prefix>.roadmap.{json,md}`

The handoff pack includes an evidence snapshot for configured JSON artifacts such as:
- `data/canonical/family_a/manifests/reports/smoke_check_report.json`
- `data/simulation/family_a/corpus/smoke_model_train_v1/manifests/reports/data_handoff_check_smoke_v1.json`
- `data/simulation/family_a/corpus/smoke_model_train_v1/manifests/reports/determinism_report_smoke_v1.json`

## Notes
- The go/no-go decision is rule-based from configured gate requirements and blocker/risk thresholds.
- Evidence snapshots report whether artifacts exist and summarize fields like `passed`, `ready`, run counts, failed checks, recommended run-ID mode, handoff issue counts, and the first structured next-action types.
- Roadmap generation selects the `go` or `no-go` phase template based on the generated decision.
- Carryover tasks are pulled directly from the tracker task-status table.
