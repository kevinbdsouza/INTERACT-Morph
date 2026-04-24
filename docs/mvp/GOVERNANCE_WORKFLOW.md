# MVP-038/039/040: Governance Workflow

## Goal
Generate governance artifacts from tracker state:
- internal handoff session pack (`MVP-038`)
- go/no-go memo against G1-G4 gates (`MVP-039`)
- post-MVP roadmap draft (`MVP-040`)

## CLI Command
```bash
interact-capsules mvp-governance \
  --progress-tracker ../Progress_Tracking.md \
  --todo ../ToDo.md \
  --config configs/mvp/family_a_mvp_governance_v1.json \
  --output-dir data/canonical/family_a/manifests/reports \
  --prefix family_a_mvp
```

## Script Entry Point
```bash
python3 scripts/build_mvp_governance_pack.py \
  --progress-tracker ../Progress_Tracking.md \
  --todo ../ToDo.md \
  --config configs/mvp/family_a_mvp_governance_v1.json \
  --output-dir data/canonical/family_a/manifests/reports \
  --prefix family_a_mvp
```

## Outputs
- `<prefix>.handoff.{json,md}`
- `<prefix>.go_no_go.{json,md}`
- `<prefix>.roadmap.{json,md}`

## Notes
- The go/no-go decision is rule-based from configured gate requirements and blocker/risk thresholds.
- Roadmap generation selects the `go` or `no-go` phase template based on the generated decision.
- Carryover tasks are pulled directly from the tracker task-status table.
