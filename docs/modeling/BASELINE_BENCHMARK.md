# MVP-009: Baseline Heuristic Benchmark

## Baseline type
Dimensionless-number heuristic using:
- Weber number
- Ohnesorge number
- Bond number

## Purpose
Provide a transparent, reproducible baseline before training learned models.

## Config
Thresholds are defined in `configs/baselines/family_a_heuristic.json`.

## Command
```bash
python3 scripts/baseline_regime_map.py \
  --dataset-root data/canonical/family_a \
  --config configs/baselines/family_a_heuristic.json \
  --output data/canonical/family_a/manifests/reports/baseline_family_a_v1.json
```

## Notes
- This is an initial benchmark and should be tuned only on training data.
- The script supports optional split-restricted evaluation via `--split`.
