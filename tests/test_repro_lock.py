from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SCRIPTS_DIR = PROJECT_ROOT / "scripts"
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

import export_environment_lockfile as lockfile


class ReproLockTests(unittest.TestCase):
    def test_parse_package_name_handles_common_requirement_forms(self) -> None:
        cases = {
            "jsonschema>=4.0": "jsonschema",
            "PyYAML>=6.0": "PyYAML",
            "requests[security]>=2.31; python_version >= '3.10'": "requests",
            "": None,
            42: None,
        }

        for requirement, expected in cases.items():
            with self.subTest(requirement=requirement):
                self.assertEqual(lockfile.parse_package_name(requirement), expected)

    def test_fallback_pyproject_parser_reads_project_and_optional_deps(self) -> None:
        pyproject = """
[project]
dependencies = [
  "basepkg>=1",
]

[project.optional-dependencies]
validation = [
  "jsonschema>=4.0",
  "PyYAML>=6.0",
]
test = [
  "pytest>=8",
]
"""
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "pyproject.toml"
            path.write_text(pyproject, encoding="utf-8")

            parsed = lockfile.read_pyproject_fallback(path)

        self.assertEqual(parsed["project"]["dependencies"], ["basepkg>=1"])
        self.assertEqual(
            parsed["project"]["optional-dependencies"]["validation"],
            ["jsonschema>=4.0", "PyYAML>=6.0"],
        )

    def test_select_dependencies_deduplicates_project_and_optional_groups(self) -> None:
        pyproject_payload = {
            "project": {
                "dependencies": ["basepkg>=1", "jsonschema>=4.0"],
                "optional-dependencies": {
                    "validation": ["jsonschema>=4.0", "PyYAML>=6.0"],
                    "ui": ["jinja2>=3"],
                },
            }
        }

        selected = lockfile.select_dependencies(
            pyproject_payload=pyproject_payload,
            include_optional=["validation"],
            skip_project_deps=False,
        )

        self.assertEqual(selected, ["basepkg", "jsonschema", "PyYAML"])

    def test_select_dependencies_rejects_unknown_optional_group(self) -> None:
        with self.assertRaises(ValueError):
            lockfile.select_dependencies(
                pyproject_payload={"project": {"optional-dependencies": {}}},
                include_optional=["missing"],
                skip_project_deps=True,
            )


if __name__ == "__main__":
    unittest.main()
