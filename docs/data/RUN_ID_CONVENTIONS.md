# MVP-004/005: Canonical Run-ID Conventions

## Why this exists
Historical acquisition records often contain spaces, punctuation, or inconsistent prefixes in run identifiers.  
Canonicalization ensures deterministic, schema-safe IDs before dataset-wide ingestion.

## Canonical format
- Format: `<FAMILY>_<TOKEN[_TOKEN...]>`
- Example valid IDs:
  - `A_20260417_RUN_001`
  - `A_LEGACY_ALPHA_12`
  - `A_RIG2_BATCH3_SAMPLE7`

## Canonicalization rules
1. Start from `source_run_id` if present, else `run_id`, else raw directory name.
2. Uppercase and replace non-alphanumeric spans with `_`.
3. Collapse repeated underscores and trim leading/trailing underscores.
4. Ensure a single family prefix (`A_`, `B_`, `C_`).
5. If a collision occurs, append deterministic hash suffix derived from source directory path.

## Ingestion behavior
- Default mode (`--run-id-mode canonicalize`):
  - Writes canonical `run_id` in canonical metadata.
  - Preserves original ID in `source_run_id`.
  - Writes mapping artifact: `manifests/run_id_map.jsonl`.
- Preserve mode (`--run-id-mode preserve`):
  - Keeps incoming `metadata.run_id` unchanged.
  - Still stores `source_run_id` for traceability.
  - Duplicate IDs fail ingestion.

## Recommended command
```bash
python3 scripts/ingest_runs.py \
  --source-dir data/raw \
  --dest-root data/canonical/family_a \
  --family A \
  --run-id-mode canonicalize
```
