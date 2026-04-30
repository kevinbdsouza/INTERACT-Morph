#!/usr/bin/env python3
from __future__ import annotations

import argparse
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = PROJECT_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from interact_morph.io_utils import dump_json


DEFAULT_OUTPUT = PROJECT_ROOT / "data" / "canonical" / "family_a" / "manifests" / "reports" / "smoke_check_report.json"
DEFAULT_HANDOFF_OUTPUT = PROJECT_ROOT / "data" / "canonical" / "family_a" / "manifests" / "reports" / "data_handoff_check.json"
DEFAULT_HANDOFF_SCHEMA = PROJECT_ROOT / "schemas" / "run_metadata.schema.json"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Run local MVP smoke checks for CLI registration, Python syntax, and test coverage "
            "(MVP-028/029/036/037)."
        )
    )
    parser.add_argument("--output", default=DEFAULT_OUTPUT, type=Path)
    parser.add_argument(
        "--skip-compile",
        action="store_true",
        help="Skip compileall syntax validation when only parser/test checks are needed.",
    )
    parser.add_argument(
        "--handoff-source-dir",
        type=Path,
        default=None,
        help="Optional raw handoff directory to check as part of the smoke bundle.",
    )
    parser.add_argument(
        "--handoff-output",
        type=Path,
        default=DEFAULT_HANDOFF_OUTPUT,
        help="Output path for the optional handoff readiness report.",
    )
    parser.add_argument(
        "--handoff-schema",
        type=Path,
        default=DEFAULT_HANDOFF_SCHEMA,
        help="Run metadata schema path for the optional handoff readiness check.",
    )
    parser.add_argument("--handoff-family", default="A", choices=["A", "B", "C"])
    parser.add_argument("--handoff-require-labels", action="store_true")
    parser.add_argument("--handoff-require-derived", action="store_true")
    return parser.parse_args()


def run_check(name: str, command: list[str]) -> dict[str, Any]:
    completed = subprocess.run(
        command,
        cwd=PROJECT_ROOT,
        check=False,
        capture_output=True,
        text=True,
    )
    return {
        "name": name,
        "command": command,
        "return_code": int(completed.returncode),
        "passed": completed.returncode == 0,
        "stdout_tail": completed.stdout[-4000:],
        "stderr_tail": completed.stderr[-4000:],
    }


def build_checks(
    skip_compile: bool,
    handoff_source_dir: Path | None = None,
    handoff_output: Path = DEFAULT_HANDOFF_OUTPUT,
    handoff_schema: Path = DEFAULT_HANDOFF_SCHEMA,
    handoff_family: str = "A",
    handoff_require_labels: bool = False,
    handoff_require_derived: bool = False,
) -> list[tuple[str, list[str]]]:
    checks = [
        (
            "unittest_discover",
            [sys.executable, "-m", "unittest", "discover", "-s", "tests"],
        ),
        (
            "cli_help",
            [sys.executable, "src/interact_morph/cli.py", "--help"],
        ),
    ]
    if not skip_compile:
        checks.insert(
            1,
            (
                "compileall",
                [sys.executable, "-m", "compileall", "src", "scripts", "tests"],
            ),
        )
    if handoff_source_dir is not None:
        handoff_command = [
            sys.executable,
            "scripts/check_data_handoff.py",
            "--source-dir",
            str(handoff_source_dir),
            "--output",
            str(handoff_output),
            "--schema",
            str(handoff_schema),
            "--family",
            handoff_family,
        ]
        if handoff_require_labels:
            handoff_command.append("--require-labels")
        if handoff_require_derived:
            handoff_command.append("--require-derived")
        checks.append(("handoff_check", handoff_command))
    return checks


def main() -> int:
    args = parse_args()
    checks = [
        run_check(name, command)
        for name, command in build_checks(
            skip_compile=args.skip_compile,
            handoff_source_dir=args.handoff_source_dir,
            handoff_output=args.handoff_output,
            handoff_schema=args.handoff_schema,
            handoff_family=args.handoff_family,
            handoff_require_labels=args.handoff_require_labels,
            handoff_require_derived=args.handoff_require_derived,
        )
    ]
    passed = all(check["passed"] for check in checks)

    report = {
        "name": "mvp_local_smoke_checks",
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "project_root": str(PROJECT_ROOT),
        "python_executable": sys.executable,
        "checks": checks,
        "passed": passed,
    }
    dump_json(args.output, report)

    print(f"Wrote smoke-check report -> {args.output}")
    for check in checks:
        status = "PASS" if check["passed"] else "FAIL"
        print(f"{status}: {check['name']} (exit {check['return_code']})")
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
