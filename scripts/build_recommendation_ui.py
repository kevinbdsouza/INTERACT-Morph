#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = PROJECT_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from interact_morph.io_utils import load_json


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Build a lightweight standalone HTML UI to review ranked recommendations "
            "and guardrail rejections (MVP-030)."
        )
    )
    parser.add_argument("--recommendation-report", required=True, type=Path, help="Path to *.recommendations.json")
    parser.add_argument("--output-html", required=True, type=Path, help="Output HTML file path")
    parser.add_argument(
        "--title",
        default="INTERACT-Morph Recommendation Review",
        help="Page title override",
    )
    parser.add_argument(
        "--max-rejected",
        type=int,
        default=250,
        help="Cap number of rejected candidates rendered into HTML",
    )
    return parser.parse_args()


def to_float(value: Any) -> float | None:
    if isinstance(value, bool):
        return 1.0 if value else 0.0
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        text = value.strip()
        if not text:
            return None
        try:
            return float(text)
        except ValueError:
            return None
    return None


def round_or_none(value: Any, decimals: int = 4) -> float | None:
    numeric = to_float(value)
    if numeric is None:
        return None
    return round(numeric, decimals)


def extract_guardrail_reasons(record: dict[str, Any]) -> str:
    guardrails = record.get("guardrails")
    if not isinstance(guardrails, dict):
        return ""
    reasons = guardrails.get("reasons")
    if not isinstance(reasons, list):
        return ""
    labels: list[str] = []
    for item in reasons:
        if isinstance(item, dict):
            reason = item.get("reason")
            detail = item.get("detail")
            if isinstance(reason, str) and reason.strip():
                if isinstance(detail, str) and detail.strip():
                    labels.append(f"{reason}: {detail}")
                else:
                    labels.append(reason)
    return "; ".join(labels)


def normalize_recommendation_rows(recommendations: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for idx, rec in enumerate(recommendations, start=1):
        predictions = rec.get("predictions")
        success_block = predictions.get("success_probability") if isinstance(predictions, dict) else {}
        if not isinstance(success_block, dict):
            success_block = {}

        objective = rec.get("objective")
        if not isinstance(objective, dict):
            objective = {}

        candidate = rec.get("candidate")
        if not isinstance(candidate, dict):
            candidate = {}
        control = candidate.get("control_parameters")
        if not isinstance(control, dict):
            control = {}

        rows.append(
            {
                "rank": rec.get("rank", idx),
                "candidate_id": rec.get("candidate_id"),
                "ranking_score": round_or_none(rec.get("ranking_score")),
                "mean_objective": round_or_none(objective.get("mean_objective")),
                "success_probability": round_or_none(success_block.get("calibrated_probability")),
                "geometry_score": round_or_none(objective.get("geometry_score")),
                "uncertainty_proxy": round_or_none(rec.get("uncertainty_proxy")),
                "predicted_regime": predictions.get("regime_label") if isinstance(predictions, dict) else None,
                "impact_velocity_m_s": round_or_none(control.get("impact_velocity_m_s")),
                "droplet_diameter_mm": round_or_none(control.get("droplet_diameter_mm")),
                "shell_outer_diameter_mm": round_or_none(control.get("shell_outer_diameter_mm")),
                "guardrail_reasons": extract_guardrail_reasons(rec),
            }
        )
    return rows


def normalize_rejected_rows(rejected: list[dict[str, Any]], max_rows: int) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for rec in rejected[: max_rows if max_rows >= 0 else len(rejected)]:
        predictions = rec.get("predictions")
        success_block = predictions.get("success_probability") if isinstance(predictions, dict) else {}
        if not isinstance(success_block, dict):
            success_block = {}

        rows.append(
            {
                "candidate_id": rec.get("candidate_id"),
                "ranking_score": round_or_none(rec.get("ranking_score")),
                "success_probability": round_or_none(success_block.get("calibrated_probability")),
                "uncertainty_proxy": round_or_none(rec.get("uncertainty_proxy")),
                "reasons": extract_guardrail_reasons(rec) or "Rejected by guardrail",
            }
        )
    return rows


def build_html(title: str, summary: dict[str, Any], accepted_rows: list[dict[str, Any]], rejected_rows: list[dict[str, Any]]) -> str:
    payload = {
        "title": title,
        "summary": summary,
        "accepted": accepted_rows,
        "rejected": rejected_rows,
    }
    payload_json = json.dumps(payload, separators=(",", ":"), ensure_ascii=True).replace("</", "<\\/")

    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{title}</title>
  <style>
    :root {{
      --bg: #f3f4ef;
      --panel: #fbfbf7;
      --ink: #101410;
      --muted: #4e5b4e;
      --border: #d1d6c9;
      --accent: #1f6f5f;
      --warn: #9f5300;
    }}
    * {{ box-sizing: border-box; }}
    body {{
      margin: 0;
      font-family: ui-sans-serif, system-ui, -apple-system, Segoe UI, Helvetica, Arial, sans-serif;
      color: var(--ink);
      background:
        radial-gradient(1200px 500px at 15% -10%, #dbe7d4 0%, transparent 60%),
        radial-gradient(1100px 500px at 95% -20%, #d7ece6 0%, transparent 58%),
        var(--bg);
    }}
    main {{
      max-width: 1200px;
      margin: 0 auto;
      padding: 28px 18px 44px;
    }}
    h1 {{ margin: 0; font-size: 1.7rem; }}
    .sub {{ margin-top: 6px; color: var(--muted); }}
    .cards {{
      margin-top: 16px;
      display: grid;
      gap: 10px;
      grid-template-columns: repeat(auto-fit, minmax(170px, 1fr));
    }}
    .card {{
      background: var(--panel);
      border: 1px solid var(--border);
      border-radius: 12px;
      padding: 10px 12px;
    }}
    .card label {{
      display: block;
      font-size: 0.78rem;
      color: var(--muted);
      letter-spacing: 0.02em;
      text-transform: uppercase;
    }}
    .card strong {{ display: block; margin-top: 3px; font-size: 1.18rem; }}
    .controls {{
      margin-top: 18px;
      display: flex;
      flex-wrap: wrap;
      gap: 10px;
      align-items: end;
    }}
    .controls .field {{
      background: var(--panel);
      border: 1px solid var(--border);
      border-radius: 12px;
      padding: 10px 12px;
      min-width: 220px;
    }}
    .field label {{ display: block; font-size: 0.82rem; color: var(--muted); margin-bottom: 5px; }}
    .field input {{
      width: 100%;
      border: 1px solid var(--border);
      background: #fff;
      border-radius: 8px;
      padding: 8px 9px;
      font-size: 0.95rem;
    }}
    table {{
      width: 100%;
      border-collapse: collapse;
      margin-top: 12px;
      background: var(--panel);
      border: 1px solid var(--border);
      border-radius: 12px;
      overflow: hidden;
      display: block;
      max-height: 520px;
      overflow: auto;
    }}
    thead {{
      position: sticky;
      top: 0;
      z-index: 1;
      background: #e9eee4;
    }}
    th, td {{
      text-align: left;
      padding: 8px 10px;
      border-bottom: 1px solid #e2e6da;
      white-space: nowrap;
      font-size: 0.9rem;
    }}
    tbody tr:nth-child(even) {{ background: #f7f8f3; }}
    .muted {{ color: var(--muted); }}
    .section-title {{
      margin: 22px 0 8px;
      font-size: 1.15rem;
    }}
    .warn {{ color: var(--warn); }}
  </style>
</head>
<body>
  <main>
    <h1>{title}</h1>
    <p class="sub">Interactive review view for recommendation ranking and guardrail filtering.</p>

    <section class="cards" id="summary-cards"></section>

    <section class="controls">
      <div class="field">
        <label for="min-success">Min Success Probability</label>
        <input id="min-success" type="number" min="0" max="1" step="0.01" placeholder="0.00">
      </div>
      <div class="field">
        <label for="max-uncertainty">Max Uncertainty Proxy</label>
        <input id="max-uncertainty" type="number" min="0" step="0.01" placeholder="no max">
      </div>
      <div class="field">
        <label for="search-id">Candidate ID Contains</label>
        <input id="search-id" type="text" placeholder="e.g. SIM_A_0012">
      </div>
    </section>

    <h2 class="section-title">Accepted Recommendations</h2>
    <p class="muted" id="accepted-count"></p>
    <table>
      <thead>
        <tr>
          <th>Rank</th><th>Candidate</th><th>Score</th><th>Success P</th><th>Objective</th>
          <th>Geometry</th><th>Uncertainty</th><th>Regime</th><th>Velocity (m/s)</th>
          <th>Drop Dia (mm)</th><th>Shell Dia (mm)</th><th>Notes</th>
        </tr>
      </thead>
      <tbody id="accepted-body"></tbody>
    </table>

    <h2 class="section-title warn">Rejected Candidates</h2>
    <p class="muted" id="rejected-count"></p>
    <table>
      <thead>
        <tr>
          <th>Candidate</th><th>Score</th><th>Success P</th><th>Uncertainty</th><th>Rejection Reasons</th>
        </tr>
      </thead>
      <tbody id="rejected-body"></tbody>
    </table>
  </main>

  <script id="payload" type="application/json">{payload_json}</script>
  <script>
    const payload = JSON.parse(document.getElementById("payload").textContent);

    const summaryCards = document.getElementById("summary-cards");
    const acceptedBody = document.getElementById("accepted-body");
    const rejectedBody = document.getElementById("rejected-body");
    const acceptedCount = document.getElementById("accepted-count");
    const rejectedCount = document.getElementById("rejected-count");
    const minSuccessInput = document.getElementById("min-success");
    const maxUncertaintyInput = document.getElementById("max-uncertainty");
    const searchIdInput = document.getElementById("search-id");

    const summary = payload.summary || {{}};
    const summaryItems = [
      ["Model", summary.model_id || "n/a"],
      ["Candidates", summary.candidate_count ?? "n/a"],
      ["Accepted", summary.accepted_count ?? "n/a"],
      ["Rejected", summary.rejected_count ?? "n/a"],
      ["Method", summary.ranking_method || "n/a"],
      ["Top K", summary.top_k ?? "n/a"],
    ];
    summaryItems.forEach(([label, value]) => {{
      const card = document.createElement("div");
      card.className = "card";
      card.innerHTML = `<label>${{label}}</label><strong>${{value}}</strong>`;
      summaryCards.appendChild(card);
    }});

    function fmt(value) {{
      return value === null || value === undefined || Number.isNaN(value) ? "n/a" : String(value);
    }}

    function renderAccepted() {{
      acceptedBody.innerHTML = "";
      const minSuccess = parseFloat(minSuccessInput.value);
      const maxUncertainty = parseFloat(maxUncertaintyInput.value);
      const query = (searchIdInput.value || "").trim().toLowerCase();

      const rows = (payload.accepted || []).filter((row) => {{
        const passSuccess = Number.isNaN(minSuccess) || (row.success_probability ?? -1) >= minSuccess;
        const passUncertainty = Number.isNaN(maxUncertainty) || (row.uncertainty_proxy ?? 1e9) <= maxUncertainty;
        const passQuery = !query || String(row.candidate_id || "").toLowerCase().includes(query);
        return passSuccess && passUncertainty && passQuery;
      }});

      rows.forEach((row) => {{
        const tr = document.createElement("tr");
        tr.innerHTML = `
          <td>${{fmt(row.rank)}}</td>
          <td>${{fmt(row.candidate_id)}}</td>
          <td>${{fmt(row.ranking_score)}}</td>
          <td>${{fmt(row.success_probability)}}</td>
          <td>${{fmt(row.mean_objective)}}</td>
          <td>${{fmt(row.geometry_score)}}</td>
          <td>${{fmt(row.uncertainty_proxy)}}</td>
          <td>${{fmt(row.predicted_regime)}}</td>
          <td>${{fmt(row.impact_velocity_m_s)}}</td>
          <td>${{fmt(row.droplet_diameter_mm)}}</td>
          <td>${{fmt(row.shell_outer_diameter_mm)}}</td>
          <td>${{fmt(row.guardrail_reasons)}}</td>
        `;
        acceptedBody.appendChild(tr);
      }});
      acceptedCount.textContent = `${{rows.length}} shown / ${{(payload.accepted || []).length}} total accepted`;
    }}

    function renderRejected() {{
      rejectedBody.innerHTML = "";
      (payload.rejected || []).forEach((row) => {{
        const tr = document.createElement("tr");
        tr.innerHTML = `
          <td>${{fmt(row.candidate_id)}}</td>
          <td>${{fmt(row.ranking_score)}}</td>
          <td>${{fmt(row.success_probability)}}</td>
          <td>${{fmt(row.uncertainty_proxy)}}</td>
          <td>${{fmt(row.reasons)}}</td>
        `;
        rejectedBody.appendChild(tr);
      }});
      rejectedCount.textContent = `${{(payload.rejected || []).length}} rejected rows rendered`;
    }}

    [minSuccessInput, maxUncertaintyInput, searchIdInput].forEach((el) => {{
      el.addEventListener("input", renderAccepted);
    }});

    renderAccepted();
    renderRejected();
  </script>
</body>
</html>
"""


def main() -> int:
    args = parse_args()

    report = load_json(args.recommendation_report)
    if not isinstance(report, dict):
        print(f"Recommendation report must be a JSON object: {args.recommendation_report}")
        return 1

    recommendations = report.get("recommendations")
    rejected = report.get("rejected_candidates")
    if not isinstance(recommendations, list):
        recommendations = []
    if not isinstance(rejected, list):
        rejected = []

    summary = report.get("summary")
    if not isinstance(summary, dict):
        summary = {}
    summary = {
        **summary,
        "model_id": report.get("model_id"),
    }

    accepted_rows = normalize_recommendation_rows([r for r in recommendations if isinstance(r, dict)])
    rejected_rows = normalize_rejected_rows([r for r in rejected if isinstance(r, dict)], max_rows=args.max_rejected)

    html = build_html(
        title=args.title,
        summary=summary,
        accepted_rows=accepted_rows,
        rejected_rows=rejected_rows,
    )

    args.output_html.parent.mkdir(parents=True, exist_ok=True)
    args.output_html.write_text(html, encoding="utf-8")
    print(f"Wrote recommendation UI -> {args.output_html}")
    print(f"Accepted rows rendered: {len(accepted_rows)}")
    print(f"Rejected rows rendered: {len(rejected_rows)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
