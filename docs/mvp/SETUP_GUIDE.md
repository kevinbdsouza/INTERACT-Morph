# INTERACT-Capsules MVP Setup Guide (MVP-037)

## Goal
Provide a repeatable setup path so a lab operator can run the CLI workflow without repository-specific tribal knowledge.

## 1) Prerequisites
- Python `>=3.10`
- `bash` shell
- Enough local storage for dataset + model artifacts

## 2) Environment Setup
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e .
pip install -e ".[validation]"
```

## 3) Verify CLI Install
```bash
interact-capsules --help
```

Expected: command groups including `handoff-check`, `pipeline`, `model-train`, `recommend`, `recommend-ui`, `repro-lock`, and `repro-check`.

## 4) Run Local Smoke Checks
```bash
python3 -m unittest discover -s tests
python3 -m compileall src scripts tests
```

Expected: tests pass and all Python modules compile.

## 5) Export Lockfile Snapshot
Run once per environment update:
```bash
interact-capsules repro-lock
```

Output:
- `locks/environment.lock.txt`

## 6) Recommended Directory Baseline
- Canonical experimental dataset root: `data/canonical/family_a`
- Simulation corpus root: `data/simulation/family_a/corpus`
- Model artifacts: `data/canonical/family_a/manifests/models`
- Recommendations + UI: `data/canonical/family_a/manifests/recommendations`
