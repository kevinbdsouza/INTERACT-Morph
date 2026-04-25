from __future__ import annotations

import json
import sys
import tempfile
import unittest
from argparse import Namespace
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SCRIPTS_DIR = PROJECT_ROOT / "scripts"
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

import check_data_handoff


def write_metadata(run_dir: Path, run_id: str) -> None:
    metadata = {
        "schema_version": "1.0.0",
        "run_id": run_id,
        "family": "A",
        "capture_timestamp": "2026-04-24T12:00:00Z",
        "fluid_combination_id": "family_a_smoke",
        "fluid_system": {
            "core": {
                "material_id": "core_a",
                "density_kg_m3": 1000.0,
                "viscosity_pa_s": 0.001,
            },
            "shell": {
                "material_id": "shell_a",
                "density_kg_m3": 1100.0,
                "viscosity_pa_s": 0.002,
            },
            "interfacial_tension_n_m": 0.03,
        },
        "control_parameters": {
            "impact_velocity_m_s": 1.2,
            "droplet_diameter_mm": 2.0,
            "shell_outer_diameter_mm": 3.0,
        },
        "outcomes": {
            "encapsulation_success": True,
            "regime_label": "stable_wrapping",
            "failure_mode": "none",
        },
        "quality_flags": {
            "video_complete": True,
            "annotation_complete": True,
            "sensors_calibrated": True,
        },
        "asset_paths": {},
    }
    (run_dir / "metadata.json").write_text(json.dumps(metadata), encoding="utf-8")


def load_metadata(run_dir: Path) -> dict:
    return json.loads((run_dir / "metadata.json").read_text(encoding="utf-8"))


class DataHandoffCheckTests(unittest.TestCase):
    def make_args(self, source_dir: Path, output: Path) -> Namespace:
        return Namespace(
            source_dir=source_dir,
            output=output,
            schema=PROJECT_ROOT / "schemas" / "run_metadata.schema.json",
            family="A",
            require_labels=False,
            require_derived=False,
        )

    def test_ready_handoff_recommends_preserve_for_canonical_ids(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            run_dir = tmp_path / "run_001"
            run_dir.mkdir()
            write_metadata(run_dir, "A_RUN_001")
            (run_dir / "video.mp4").write_bytes(b"smoke")

            report, rc = check_data_handoff.build_report(
                self.make_args(tmp_path, tmp_path / "report.json")
            )

        self.assertEqual(rc, 0)
        self.assertTrue(report["ready"])
        self.assertEqual(report["run_count"], 1)
        self.assertEqual(report["run_id_mode_recommendation"]["recommended"], "preserve")
        self.assertEqual(report["next_actions"][0]["type"], "run_pipeline")
        self.assertIn("--run-id-mode preserve", report["next_actions"][0]["command"])

    def test_noncanonical_ids_are_ready_but_recommend_canonicalize(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            run_dir = tmp_path / "run 001"
            run_dir.mkdir()
            write_metadata(run_dir, "run 001")
            (run_dir / "video.mp4").write_bytes(b"smoke")

            report, rc = check_data_handoff.build_report(
                self.make_args(tmp_path, tmp_path / "report.json")
            )

        self.assertEqual(rc, 0)
        self.assertTrue(report["ready"])
        self.assertEqual(report["run_id_mode_recommendation"]["recommended"], "canonicalize")
        self.assertEqual(
            report["run_id_mode_recommendation"]["preserve_issue_counts"],
            {"preserve_mode_noncanonical_run_id": 1},
        )
        self.assertIn("--run-id-mode canonicalize", report["next_actions"][0]["command"])

    def test_missing_video_blocks_readiness(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            run_dir = tmp_path / "run_001"
            run_dir.mkdir()
            write_metadata(run_dir, "A_RUN_001")

            report, rc = check_data_handoff.build_report(
                self.make_args(tmp_path, tmp_path / "report.json")
            )

        self.assertEqual(rc, 1)
        self.assertFalse(report["ready"])
        self.assertEqual(report["issue_counts"], {"missing_video": 1, "schema": 1})
        self.assertEqual(report["next_actions"][0]["type"], "fix_blocking_run_issues")
        self.assertEqual(report["issue_examples"]["missing_video"], [str(run_dir)])

    def test_missing_family_blocks_readiness_like_ingest(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            run_dir = tmp_path / "run_001"
            run_dir.mkdir()
            write_metadata(run_dir, "A_RUN_001")
            metadata = load_metadata(run_dir)
            del metadata["family"]
            (run_dir / "metadata.json").write_text(json.dumps(metadata), encoding="utf-8")
            (run_dir / "video.mp4").write_bytes(b"smoke")

            report, rc = check_data_handoff.build_report(
                self.make_args(tmp_path, tmp_path / "report.json")
            )

        self.assertEqual(rc, 1)
        self.assertFalse(report["ready"])
        self.assertEqual(report["issue_counts"], {"family_missing": 1})

    def test_missing_source_dir_reports_top_level_next_action(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            missing_source = tmp_path / "missing"

            report, rc = check_data_handoff.build_report(
                self.make_args(missing_source, tmp_path / "report.json")
            )

        self.assertEqual(rc, 1)
        self.assertFalse(report["ready"])
        self.assertEqual(report["top_level_errors"], ["source_dir_missing"])
        self.assertEqual(report["next_actions"][0]["type"], "fix_source_directory")


if __name__ == "__main__":
    unittest.main()
