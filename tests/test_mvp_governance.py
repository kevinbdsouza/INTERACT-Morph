from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = PROJECT_ROOT / "src"
SCRIPTS_DIR = PROJECT_ROOT / "scripts"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

from interact_morph.io_utils import dump_json
import build_mvp_governance_pack


class MvpGovernanceTests(unittest.TestCase):
    def test_evidence_snapshot_summarizes_smoke_and_handoff_reports(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            smoke_report = tmp_path / "smoke.json"
            handoff_report = tmp_path / "handoff.json"
            dump_json(
                smoke_report,
                {
                    "name": "mvp_local_smoke_checks",
                    "passed": True,
                    "checks": [
                        {"name": "unittest_discover", "passed": True},
                        {"name": "compileall", "passed": True},
                    ],
                },
            )
            dump_json(
                handoff_report,
                {
                    "name": "family_a_data_handoff_check",
                    "ready": True,
                    "run_count": 3,
                    "ready_run_count": 3,
                    "issue_counts": {"missing_video": 1},
                    "run_id_mode_recommendation": {"recommended": "preserve"},
                    "next_actions": [
                        {"priority": "P0", "type": "run_pipeline"},
                        {"priority": "P1", "type": "attach_governance_evidence"},
                    ],
                },
            )

            snapshot = build_mvp_governance_pack.build_evidence_snapshot(
                {
                    "handoff": {
                        "evidence_artifacts": [
                            {"label": "Smoke", "path": str(smoke_report)},
                            {"label": "Handoff", "path": str(handoff_report)},
                            {"label": "Missing", "path": str(tmp_path / "missing.json")},
                        ]
                    }
                }
            )

        self.assertEqual(len(snapshot), 3)
        self.assertTrue(snapshot[0]["exists"])
        self.assertEqual(snapshot[0]["summary"]["passed"], True)
        self.assertEqual(snapshot[0]["summary"]["check_count"], 2)
        self.assertEqual(snapshot[0]["summary"]["failed_checks"], [])
        self.assertTrue(snapshot[1]["exists"])
        self.assertEqual(snapshot[1]["summary"]["ready"], True)
        self.assertEqual(snapshot[1]["summary"]["recommended_run_id_mode"], "preserve")
        self.assertEqual(snapshot[1]["summary"]["issue_counts"], {"missing_video": 1})
        self.assertEqual(snapshot[1]["summary"]["next_action_count"], 2)
        self.assertEqual(snapshot[1]["summary"]["next_actions"][0]["type"], "run_pipeline")
        self.assertFalse(snapshot[2]["exists"])

    def test_handoff_payload_includes_evidence_snapshot(self) -> None:
        payload = build_mvp_governance_pack.build_handoff_payload(
            config={"handoff": {"evidence_artifacts": []}},
            generated_at_utc="2026-04-24T00:00:00+00:00",
            task_rows=[],
            todo_task_map={},
        )

        self.assertIn("evidence_snapshot", payload)


if __name__ == "__main__":
    unittest.main()
