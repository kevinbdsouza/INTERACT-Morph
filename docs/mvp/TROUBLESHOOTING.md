# INTERACT-Morph MVP Troubleshooting (MVP-037)

## Common Issues

## `interact-morph` not found
- Cause: package not installed in active environment.
- Fix:
```bash
source .venv/bin/activate
pip install -e .
```

## YAML config load fails (`PyYAML` missing)
- Cause: optional validation dependencies not installed.
- Fix:
```bash
pip install -e ".[validation]"
```

## `recommend` produces many rejected candidates
- Cause: guardrails stricter than candidate distribution supports.
- Fix:
1. Inspect rejection reasons in `rejected_candidates`.
2. Tune `guardrails` section in `configs/modeling/family_a_recommendation_v1.json`.
3. Re-run `interact-morph recommend`.

## `recommend-ui` shows empty accepted table
- Cause: filters set too strict or recommendation report has no accepted candidates.
- Fix:
1. Clear UI filter fields.
2. Check `summary.accepted_count` in the recommendation JSON.

## Determinism check fails (`passed=false`)
- Cause: non-deterministic inputs or unstable artifact generation path.
- Fix:
1. Ensure same dataset root, split, config, and init model are used.
2. Re-run with explicit artifact retention:
```bash
interact-morph repro-check ... --keep-artifacts --artifact-dir /tmp/interact_determinism_debug
```
3. Diff `*_a.*` vs `*_b.*` artifacts in the saved directory.
