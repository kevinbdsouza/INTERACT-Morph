# MVP-008: Family A Split Policy

## Goal
Create reproducible train/validation/test splits that reflect realistic generalization pressure.

## Policy
- Grouping key: `fluid_combination_id`
- Group non-overlap: enforced across train/val/test
- Optional explicit held-out groups: configured in `configs/splits/family_a_split.json`
- Deterministic seed-based assignment for reproducibility

## Why group-based splits
Random run-level splits leak fluid-family information across splits and inflate performance. Grouping by fluid combination better approximates prospective deployment.

## Command
```bash
python3 scripts/create_split.py \
  --dataset-root data/canonical/family_a \
  --config configs/splits/family_a_split.json \
  --output data/canonical/family_a/manifests/splits/family_a_v1.json
```
