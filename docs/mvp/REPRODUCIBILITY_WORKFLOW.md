# MVP-036: Reproducibility Hardening Workflow

## Goals
- Capture environment dependency lock snapshot for each run cycle.
- Verify deterministic model train/eval artifacts under repeated identical runs.
- Keep a local smoke-test harness for CLI orchestration and lockfile utility behavior.

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

## 3) Local Smoke Tests
Run the bundled check before changing CLI wiring, pipeline defaults, or lockfile parsing:
```bash
interact-capsules smoke-check
```

Equivalent individual checks:
```bash
python3 -m unittest discover -s tests
python3 -m compileall src scripts tests
python3 src/interact_capsules/cli.py --help
```

Current smoke coverage includes:
- CLI command registration across active MVP tasks.
- `pipeline` orchestration order and fail-fast behavior.
- `feature-qa` required input guard.
- Lockfile requirement parsing, optional dependency selection, and missing group errors.
- Smoke-check command/report wiring.
