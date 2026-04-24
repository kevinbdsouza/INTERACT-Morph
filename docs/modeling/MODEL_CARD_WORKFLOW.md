# MVP-024: Model Card Workflow (v1)

## Goal
Generate a standardized markdown model card for each trained model artifact.

## CLI Command
```bash
interact-capsules model-card \
  --model-artifact data/canonical/family_a/manifests/models/<model_id>.model.json \
  --eval-artifact data/canonical/family_a/manifests/models/<model_id>.eval.json \
  --calibration-artifact data/canonical/family_a/manifests/models/<model_id>.calibration.json \
  --output data/canonical/family_a/manifests/model_cards/<model_id>.md
```

## Script Entry Point
```bash
python3 scripts/generate_model_card.py \
  --model-artifact data/canonical/family_a/manifests/models/<model_id>.model.json \
  --eval-artifact data/canonical/family_a/manifests/models/<model_id>.eval.json \
  --calibration-artifact data/canonical/family_a/manifests/models/<model_id>.calibration.json \
  --template templates/model_card.template.md \
  --output data/canonical/family_a/manifests/model_cards/<model_id>.md
```

## Template
- Default template: `templates/model_card.template.md`
- Includes placeholders for scope, metrics, calibration summary, and traceability hashes.

## Notes
- Calibration artifact is optional; if omitted, the card marks calibration as unavailable.
- The generated card is intended for internal review and go/no-go gate evidence.
