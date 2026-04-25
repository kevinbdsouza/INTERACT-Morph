# INTERACT-Capsules MVP Runbook (MVP-037)

## Scope
Operational run sequence for Family A recommendation cycles once dataset artifacts are available.

## Pre-Run Checks
1. Confirm environment and lock snapshot:
```bash
interact-capsules repro-lock
```
2. Run the local smoke bundle and archive the JSON report:
```bash
interact-capsules smoke-check
```
3. Before the first production ingest, check raw handoff readiness:
```bash
interact-capsules handoff-check \
  --source-dir data/raw \
  --family A
```
Use the generated report's `next_actions` field to decide whether to fix source issues, rerun the preflight, or execute the exact `pipeline` command with the recommended `--run-id-mode`.
To capture code-health and raw-handoff readiness in one evidence file, run:
```bash
interact-capsules smoke-check \
  --handoff-source-dir data/raw \
  --handoff-output data/canonical/family_a/manifests/reports/data_handoff_check.json
```
4. Confirm split + model config paths are correct for this cycle.
5. Confirm candidate sweep artifact exists and is current.

## Run Sequence
1. Train or fine-tune model:
- `interact-capsules model-train` or `interact-capsules model-finetune`
2. Calibrate uncertainty:
- `interact-capsules model-calibrate`
3. Generate model card:
- `interact-capsules model-card`
4. Generate recommendations:
- `interact-capsules recommend`
5. Build experiment execution template:
- `interact-capsules experiment-template`
6. Prepare campaign plans/log templates for primary and robustness arms:
- `interact-capsules campaign-prepare`
7. Build operator UI:
- `interact-capsules recommend-ui`
8. Run deterministic verification:
- `interact-capsules repro-check`
9. After campaign completion, compare against baseline:
- `interact-capsules campaign-analyze`
10. Generate failure-mode taxonomy:
- `interact-capsules failure-analysis`
11. Generate governance pack for handoff + go/no-go + roadmap:
- `interact-capsules mvp-governance`

## Required Artifacts Per Cycle
- `*.model.json`
- `*.eval.json`
- `*.predictions.jsonl`
- `*.calibration.json` and optional calibrated predictions JSONL
- `*.recommendations.json`
- `*.execution_template.json` (and optional markdown)
- `campaign_prepared_*.json` and campaign `*.jsonl` logs
- `*.recommendations.html`
- `campaign_analysis.json`
- `failure_mode_analysis.json`
- `determinism_report.json`
- `smoke_check_report.json`
- `data_handoff_check.json` for first production ingest cycles
- `family_a_mvp.{handoff,go_no_go,roadmap}.{json,md}`

## Decision Gates
- If smoke-check fails: fix parser/test/syntax failures before running production pipeline commands.
- If handoff-check fails: fix source metadata/video/schema issues shown in `issue_counts` and `issue_examples`, then rerun the preflight before `pipeline`.
- If deterministic check fails: do not publish recommendations.
- If guardrail rejections dominate accepted results: review recommendation config weights and thresholds.
- If calibration report quality regresses: revisit split quality and feature extraction quality before running campaigns.
