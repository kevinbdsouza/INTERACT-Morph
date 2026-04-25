from __future__ import annotations

import sys
import unittest
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SCRIPTS_DIR = PROJECT_ROOT / "scripts"
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

import run_smoke_checks


class SmokeCheckTests(unittest.TestCase):
    def test_build_checks_includes_compile_by_default(self) -> None:
        names = [name for name, _ in run_smoke_checks.build_checks(skip_compile=False)]

        self.assertEqual(names, ["unittest_discover", "compileall", "cli_help"])

    def test_build_checks_can_skip_compile(self) -> None:
        names = [name for name, _ in run_smoke_checks.build_checks(skip_compile=True)]

        self.assertEqual(names, ["unittest_discover", "cli_help"])

    def test_build_checks_can_include_handoff_preflight(self) -> None:
        checks = run_smoke_checks.build_checks(
            skip_compile=True,
            handoff_source_dir=Path("data/raw"),
            handoff_output=Path("reports/handoff.json"),
            handoff_schema=Path("schemas/run_metadata.schema.json"),
            handoff_family="A",
            handoff_require_labels=True,
            handoff_require_derived=True,
        )

        self.assertEqual([name for name, _ in checks], ["unittest_discover", "cli_help", "handoff_check"])
        handoff_command = checks[-1][1]
        self.assertIn("scripts/check_data_handoff.py", handoff_command)
        self.assertIn("--require-labels", handoff_command)
        self.assertIn("--require-derived", handoff_command)


if __name__ == "__main__":
    unittest.main()
