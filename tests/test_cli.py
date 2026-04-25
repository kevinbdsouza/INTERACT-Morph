from __future__ import annotations

import sys
import unittest
from contextlib import redirect_stdout
from io import StringIO
from pathlib import Path
from unittest.mock import patch

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = PROJECT_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from interact_capsules import cli


class CliParserTests(unittest.TestCase):
    def test_expected_mvp_commands_are_registered(self) -> None:
        parser = cli.build_parser()
        subparser_action = next(
            action for action in parser._actions if getattr(action, "dest", None) == "command"
        )

        expected = {
            "inventory",
            "handoff-check",
            "ingest",
            "validate",
            "split",
            "baseline",
            "snapshot",
            "sim-plan",
            "sim-generate",
            "sim-realism",
            "model-train",
            "model-finetune",
            "model-calibrate",
            "model-card",
            "recommend",
            "recommend-ui",
            "experiment-template",
            "campaign-prepare",
            "campaign-analyze",
            "failure-analysis",
            "mvp-governance",
            "repro-lock",
            "repro-check",
            "smoke-check",
            "segment-train",
            "extract-trajectories",
            "feature-qa",
            "label-correction",
            "pipeline",
        }

        self.assertTrue(expected.issubset(set(subparser_action.choices)))

    def test_feature_qa_requires_dataset_or_index(self) -> None:
        parser = cli.build_parser()
        args = parser.parse_args(["feature-qa", "--output", "qa.json"])

        with redirect_stdout(StringIO()):
            self.assertEqual(cli._cmd_feature_qa(args), 2)

    def test_handoff_check_forwards_readiness_options(self) -> None:
        parser = cli.build_parser()
        args = parser.parse_args(
            [
                "handoff-check",
                "--source-dir",
                "data/raw",
                "--output",
                "reports/handoff.json",
                "--schema",
                "schemas/run_metadata.schema.json",
                "--family",
                "A",
                "--require-labels",
                "--require-derived",
            ]
        )

        with patch.object(cli, "_run_script", return_value=0) as run_script:
            rc = cli._cmd_handoff_check(args)

        self.assertEqual(rc, 0)
        run_script.assert_called_once_with(
            "check_data_handoff.py",
            [
                "--source-dir",
                "data/raw",
                "--output",
                "reports/handoff.json",
                "--schema",
                "schemas/run_metadata.schema.json",
                "--family",
                "A",
                "--require-labels",
                "--require-derived",
            ],
        )

    def test_pipeline_runs_steps_in_order_with_defaults(self) -> None:
        calls: list[tuple[str, list[str]]] = []

        def fake_run_script(script_name: str, script_args: list[str]) -> int:
            calls.append((script_name, script_args))
            return 0

        with patch.object(cli, "_run_script", side_effect=fake_run_script):
            with redirect_stdout(StringIO()):
                rc = cli.main(
                    [
                        "pipeline",
                        "--source-dir",
                        "data/raw",
                        "--dataset-root",
                        "data/canonical/family_a",
                        "--snapshot-name",
                        "family_a_v1",
                        "--require-labels",
                        "--require-derived",
                    ]
                )

        self.assertEqual(rc, 0)
        self.assertEqual(
            [script_name for script_name, _ in calls],
            [
                "ingest_runs.py",
                "validate_dataset.py",
                "create_split.py",
                "baseline_regime_map.py",
                "snapshot_dataset.py",
            ],
        )

        validate_args = calls[1][1]
        self.assertIn("--require-labels", validate_args)
        self.assertIn("--require-derived", validate_args)

        split_args = calls[2][1]
        baseline_args = calls[3][1]
        expected_split = "data/canonical/family_a/manifests/splits/family_a_v1.json"
        self.assertIn(expected_split, split_args)
        self.assertIn(expected_split, baseline_args)

    def test_pipeline_stops_on_first_failed_step(self) -> None:
        calls: list[str] = []

        def fake_run_script(script_name: str, script_args: list[str]) -> int:
            calls.append(script_name)
            return 7 if script_name == "validate_dataset.py" else 0

        with patch.object(cli, "_run_script", side_effect=fake_run_script):
            with redirect_stdout(StringIO()):
                rc = cli.main(
                    [
                        "pipeline",
                        "--source-dir",
                        "data/raw",
                        "--dataset-root",
                        "data/canonical/family_a",
                    ]
                )

        self.assertEqual(rc, 7)
        self.assertEqual(calls, ["ingest_runs.py", "validate_dataset.py"])

    def test_mvp_governance_defaults_use_repo_docs(self) -> None:
        parser = cli.build_parser()
        args = parser.parse_args(["mvp-governance"])

        self.assertEqual(args.progress_tracker, cli.PROJECT_ROOT / "docs" / "mvp" / "Progress_Tracking.md")
        self.assertEqual(args.todo, cli.PROJECT_ROOT / "docs" / "mvp" / "ToDo.md")

    def test_smoke_check_forwards_output_and_skip_compile(self) -> None:
        parser = cli.build_parser()
        args = parser.parse_args(
            [
                "smoke-check",
                "--output",
                "reports/smoke.json",
                "--skip-compile",
            ]
        )

        with patch.object(cli, "_run_script", return_value=0) as run_script:
            rc = cli._cmd_smoke_check(args)

        self.assertEqual(rc, 0)
        run_script.assert_called_once_with(
            "run_smoke_checks.py",
            ["--output", "reports/smoke.json", "--skip-compile"],
        )

    def test_smoke_check_forwards_optional_handoff_preflight(self) -> None:
        parser = cli.build_parser()
        args = parser.parse_args(
            [
                "smoke-check",
                "--output",
                "reports/smoke.json",
                "--handoff-source-dir",
                "data/raw",
                "--handoff-output",
                "reports/handoff.json",
                "--handoff-schema",
                "schemas/run_metadata.schema.json",
                "--handoff-family",
                "A",
                "--handoff-require-labels",
                "--handoff-require-derived",
            ]
        )

        with patch.object(cli, "_run_script", return_value=0) as run_script:
            rc = cli._cmd_smoke_check(args)

        self.assertEqual(rc, 0)
        run_script.assert_called_once_with(
            "run_smoke_checks.py",
            [
                "--output",
                "reports/smoke.json",
                "--handoff-source-dir",
                "data/raw",
                "--handoff-output",
                "reports/handoff.json",
                "--handoff-schema",
                "schemas/run_metadata.schema.json",
                "--handoff-family",
                "A",
                "--handoff-require-labels",
                "--handoff-require-derived",
            ],
        )


if __name__ == "__main__":
    unittest.main()
