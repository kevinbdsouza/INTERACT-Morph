# MVP-015/016/017: Axisymmetric Simulation Workflow

## Scope
This workflow supports the Family A simulation track from DOE planning through first synthetic corpus generation.

## Inputs
- Sweep config: `configs/simulations/family_a_axisymmetric_doe.json`
- Parameter ranges for velocity, geometry, and fluid properties
- Constraint bounds for physically plausible candidates
- Surrogate execution config: `configs/simulations/family_a_axisymmetric_surrogate.json`

## Output Artifacts
- Planned simulation cases JSONL + manifest
- Synthetic corpus in canonical-style layout:
  - `runs/<run_id>/metadata.json`
  - `runs/<run_id>/derived_features.json`
  - `runs/<run_id>/labels.json`
  - `runs/<run_id>/video.mp4` (placeholder in MVP-017 bootstrap)
  - `manifests/runs_index.jsonl`
  - `manifests/run_id_map.jsonl`
  - `manifests/simulation_index.jsonl`
  - `manifests/dataset_manifest.json`

## Commands
1. Plan sweep:
```bash
python3 scripts/plan_axisymmetric_sweep.py \
  --config configs/simulations/family_a_axisymmetric_doe.json \
  --output data/simulation/family_a/manifests/axisymmetric_sweep_v1.jsonl \
  --family A
```

2. Generate first synthetic corpus from plan:
```bash
python3 scripts/generate_simulation_corpus.py \
  --plan-jsonl data/simulation/family_a/manifests/axisymmetric_sweep_v1.jsonl \
  --surrogate-config configs/simulations/family_a_axisymmetric_surrogate.json \
  --output-root data/simulation/family_a/corpus/family_a_axisymmetric_doe_v1 \
  --family A
```

3. Build realism summary report (MVP-018 starter):
```bash
python3 scripts/report_simulation_realism.py \
  --simulation-dataset-root data/simulation/family_a/corpus/family_a_axisymmetric_doe_v1 \
  --experimental-dataset-root data/canonical/family_a \
  --output data/simulation/family_a/manifests/reports/realism_family_a_v1.json
```

## Notes
- `simulation_id` is mapped into canonical run IDs for downstream tooling compatibility.
- `metadata.json` and `derived_features.json` are schema-validated during corpus generation.
- This surrogate runner is the MVP bootstrap path; replace or augment with production solver coupling in later milestones.
