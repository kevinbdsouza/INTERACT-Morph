# MVP-030: Lightweight Recommendation UI Prototype

## Goal
Provide a zero-dependency HTML interface that experimentalists can open locally to review ranked recommendations and guardrail rejections.

## CLI Command
```bash
interact-morph recommend-ui \
  --recommendation-report data/canonical/family_a/manifests/recommendations/<model_id>.recommendations.json \
  --output-html data/canonical/family_a/manifests/recommendations/<model_id>.recommendations.html
```

## Script Entry Point
```bash
python3 scripts/build_recommendation_ui.py \
  --recommendation-report data/canonical/family_a/manifests/recommendations/<model_id>.recommendations.json \
  --output-html data/canonical/family_a/manifests/recommendations/<model_id>.recommendations.html
```

## What the UI Includes
- Summary cards: candidate counts, ranking method, top-k, model ID
- Accepted recommendations table with rank/objective/prediction details
- Rejected candidates table with guardrail reasons
- Client-side filters for success probability, uncertainty, and candidate ID

## Notes
- Output is standalone HTML (no server required).
- Input is the recommendation JSON artifact from `interact-morph recommend`.
