# MVP-036: Reproducibility Hardening Workflow

## Goals
- Capture environment dependency lock snapshot for each run cycle.
- Verify deterministic model train/eval artifacts under repeated identical runs.

## 1) Export Environment Lockfile
```bash
interact-capsules repro-lock
```

Default output:
- `locks/environment.lock.txt`

Optional strict mode:
```bash
interact-capsules repro-lock --strict
```

## 2) Deterministic Training/Evaluation Check
```bash
interact-capsules repro-check \
  --dataset-root data/simulation/family_a/corpus/smoke_model_train_v1 \
  --split data/simulation/family_a/corpus/smoke_model_train_v1/manifests/splits/smoke_v1.json \
  --config configs/modeling/family_a_multimodal_v1.json \
  --output data/simulation/family_a/corpus/smoke_model_train_v1/manifests/reports/determinism_report.json
```

Optional artifact retention:
```bash
interact-capsules repro-check ... --keep-artifacts --artifact-dir /tmp/interact_determinism_debug
```

## Determinism Report Contract
The report includes:
- `passed` (`true/false`)
- model/eval/predictions payload match booleans
- canonical content hashes for run A and run B

Recommendations should only be published when `passed=true`.
