from __future__ import annotations

import json
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
import build_dataset_card


class DatasetCardTests(unittest.TestCase):
    def test_dataset_card_summarizes_manifest_split_and_gaps(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            root = Path(tmp_dir) / "family_a"
            manifests = root / "manifests"
            runs = root / "runs"
            manifests.mkdir(parents=True)
            run_dir = runs / "A_RUN_001"
            run_dir.mkdir(parents=True)

            dump_json(
                manifests / "dataset_manifest.json",
                {
                    "family": "A",
                    "run_id_mode": "preserve",
                    "source_dir": "data/raw",
                    "run_count": 1,
                },
            )
            (manifests / "runs_index.jsonl").write_text(
                json.dumps(
                    {
                        "run_id": "A_RUN_001",
                        "family": "A",
                        "fluid_combination_id": "FC1",
                        "regime_label": "stable_wrapping",
                        "encapsulation_success": True,
                        "quality_flags": {
                            "video_complete": True,
                            "annotation_complete": False,
                            "sensors_calibrated": True,
                        },
                        "run_relpath": "runs/A_RUN_001",
                    }
                )
                + "\n",
                encoding="utf-8",
            )
            dump_json(
                run_dir / "metadata.json",
                {
                    "control_parameters": {
                        "route_type": "single_layer",
                        "confinement_type": "conventional",
                    },
                    "outcomes": {
                        "shell_thickness_mean_um": 120.0,
                        "trapped_air_fraction": 0.02,
                    },
                },
            )
            split = manifests / "splits" / "family_a_v1.json"
            dump_json(
                split,
                {
                    "split_name": "family_a_v1",
                    "seed": 42,
                    "group_by": "fluid_combination_id",
                    "counts": {"train": 1, "val": 0, "test": 0},
                    "groups": {"train": ["FC1"], "val": [], "test": []},
                },
            )

            summary, markdown = build_dataset_card.build_dataset_card(
                dataset_root=root,
                split_path=split,
                generated_at_utc="2026-04-30T00:00:00+00:00",
            )

        self.assertEqual(summary["run_count"], 1)
        self.assertEqual(summary["fluid_combination_count"], 1)
        self.assertEqual(summary["route_type_distribution"], {"single_layer": 1})
        self.assertEqual(summary["confinement_type_distribution"], {"conventional": 1})
        self.assertEqual(summary["morphology_coverage"]["shell_thickness_mean_um"]["present"], 1)
        self.assertEqual(summary["morphology_coverage"]["crown_index"]["missing"], 1)
        self.assertEqual(summary["split"]["counts"], {"train": 1, "val": 0, "test": 0})
        self.assertIn("## Morphology Label Coverage", markdown)
        self.assertIn("missing_outcome:crown_index", markdown)


if __name__ == "__main__":
    unittest.main()
