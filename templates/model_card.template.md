# Model Card: {{MODEL_ID}}

## Scope
- Family: `A` (MVP scope)
- Created at (UTC): `{{CREATED_AT_UTC}}`
- Dataset root: `{{DATASET_ROOT}}`
- Split artifact: `{{SPLIT_PATH}}`

## Data Summary
- Total runs: `{{RUN_COUNT_TOTAL}}`
- Train runs: `{{RUN_COUNT_TRAIN}}`
- Val runs: `{{RUN_COUNT_VAL}}`
- Test runs: `{{RUN_COUNT_TEST}}`

## Feature Contract
{{FEATURE_LIST}}

## Success Head Metrics
{{SUCCESS_METRICS_TABLE}}

## Regime Head Metrics
{{REGIME_METRICS_TABLE}}

## Regression Head Metrics
{{REGRESSION_METRICS_TABLES}}

## Calibration Summary
{{CALIBRATION_SUMMARY}}

## Data Loading Notes
{{DATA_LOADING_NOTES}}

## Traceability
- Config SHA256: `{{CONFIG_SHA256}}`
- Split SHA256: `{{SPLIT_SHA256}}`
- Model artifact: `{{MODEL_ARTIFACT_PATH}}`
- Eval artifact: `{{EVAL_ARTIFACT_PATH}}`
- Calibration artifact: `{{CALIBRATION_ARTIFACT_PATH}}`

## Known Limitations
- This artifact is for internal Family A MVP usage only.
- Smoke/surrogate results are not representative of production lab performance.
- Recommendations should be guarded with validated-domain checks before lab execution.
