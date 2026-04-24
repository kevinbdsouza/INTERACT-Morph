# MVP-002/003/005: Data Architecture and Canonical Layout

## Canonical Dataset Layout

```text
data/
  raw/                                # Raw experimental drops from acquisition systems
  canonical/
    family_a/
      runs/
        <run_id>/
          metadata.json               # Must validate against schemas/run_metadata.schema.json
          labels.json                 # Optional during ingestion; required before model training
          derived_features.json       # Optional early; required for multimodal model
          video.mp4                   # Required
      manifests/
        runs_index.jsonl              # One JSON record per run
        run_id_map.jsonl              # Source-to-canonical run ID mapping for traceability
        dataset_manifest.json         # Dataset-level summary + schema versions + counts
  manifests/
    inventory_family_a.csv            # Raw inventory snapshot (MVP-004)
```

## Data Contract
- `metadata.json`: experimental inputs, outcomes, acquisition metadata
- `labels.json`: manual/corrected labels (regime/failure mode/event marks)
- `derived_features.json`: extracted trajectories and events
- `runs_index.jsonl`: stable index used by split generation and training scripts

## Schema Versioning
- Initial schema versions:
  - `run_metadata.schema.json`: `1.0.0`
  - `derived_features.schema.json`: `1.0.0`
- Version bump policy:
  - Patch (`1.0.x`): additive non-breaking fields
  - Minor (`1.x.0`): optional structural expansion
  - Major (`x.0.0`): breaking changes, requires migration script

## Required Run-Level IDs
- `run_id`: globally unique run identifier
- `source_run_id` (optional but recommended): original historical/acquisition ID before canonicalization
- `fluid_combination_id`: deterministic identifier for held-out fluid-family evaluations
- `family`: one of `A`, `B`, `C`

Canonical run-ID format and normalization policy are defined in `docs/data/RUN_ID_CONVENTIONS.md`.

## Storage and Reproducibility Rules
- Never overwrite an existing canonical run in-place without updating manifests
- Every ingestion run writes/updates `dataset_manifest.json`
- Split files must reference a specific dataset manifest fingerprint

## Validation Rules
- Schema validation on ingestion and pre-training
- Integrity checks:
  - Required assets exist
  - No duplicate `run_id`
  - Required numeric fields are finite and physically valid (positive where expected)
- Unit consistency check:
  - Canonical numeric units fixed by field name (`*_mm`, `*_kg_m3`, `*_pa_s`, `*_n_m`, `*_um`)
