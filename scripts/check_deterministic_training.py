#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import subprocess
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = PROJECT_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from interact_capsules.io_utils import dump_json, load_json


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Run train_multimodal_model.py twice and verify deterministic model/eval/predictions "
            "content under identical inputs (MVP-036)."
        )
    )
    parser.add_argument("--dataset-root", required=True, type=Path)
    parser.add_argument("--split", required=True, type=Path)
    parser.add_argument("--config", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path, help="Output determinism report JSON")
    parser.add_argument("--init-model", default=None, type=Path, help="Optional warm-start model artifact")
    parser.add_argument(
        "--model-id-prefix",
        default="determinism_probe",
        help="Prefix for run-specific model IDs",
    )
    parser.add_argument(
        "--artifact-dir",
        default=None,
        type=Path,
        help="Optional directory to keep probe artifacts; otherwise uses a temporary directory.",
    )
    parser.add_argument("--keep-artifacts", action="store_true")
    return parser.parse_args()


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def canonical_dumps(payload: Any) -> str:
    return json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def canonicalize_model(payload: dict[str, Any]) -> dict[str, Any]:
    clone = json.loads(json.dumps(payload))
    clone.pop("model_id", None)
    clone.pop("created_at_utc", None)
    return clone


def canonicalize_eval(payload: dict[str, Any]) -> dict[str, Any]:
    clone = json.loads(json.dumps(payload))
    clone.pop("model_id", None)
    clone.pop("created_at_utc", None)
    return clone


def load_predictions(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as f:
        for idx, line in enumerate(f, start=1):
            text = line.strip()
            if not text:
                continue
            payload = json.loads(text)
            if not isinstance(payload, dict):
                raise ValueError(f"{path}:{idx} expected JSON object")
            rows.append(payload)
    return rows


def run_probe(
    dataset_root: Path,
    split: Path,
    config: Path,
    output_dir: Path,
    model_id: str,
    init_model: Path | None,
) -> tuple[int, str, str]:
    command = [
        sys.executable,
        str(PROJECT_ROOT / "scripts" / "train_multimodal_model.py"),
        "--dataset-root",
        str(dataset_root),
        "--split",
        str(split),
        "--config",
        str(config),
        "--output-dir",
        str(output_dir),
        "--model-id",
        model_id,
    ]
    if init_model is not None:
        command.extend(["--init-model", str(init_model)])

    completed = subprocess.run(command, check=False, capture_output=True, text=True)
    return int(completed.returncode), completed.stdout, completed.stderr


def main() -> int:
    args = parse_args()
    started_at = datetime.now(timezone.utc).isoformat()

    cleanup_needed = False
    if args.artifact_dir is not None:
        artifact_root = args.artifact_dir
        artifact_root.mkdir(parents=True, exist_ok=True)
    else:
        artifact_root = Path(tempfile.mkdtemp(prefix="interact_determinism_"))
        cleanup_needed = not args.keep_artifacts

    output_dir = artifact_root / "models"
    output_dir.mkdir(parents=True, exist_ok=True)

    run_a_id = f"{args.model_id_prefix}_a"
    run_b_id = f"{args.model_id_prefix}_b"

    rc_a, stdout_a, stderr_a = run_probe(
        dataset_root=args.dataset_root,
        split=args.split,
        config=args.config,
        output_dir=output_dir,
        model_id=run_a_id,
        init_model=args.init_model,
    )
    rc_b, stdout_b, stderr_b = run_probe(
        dataset_root=args.dataset_root,
        split=args.split,
        config=args.config,
        output_dir=output_dir,
        model_id=run_b_id,
        init_model=args.init_model,
    )

    report: dict[str, Any] = {
        "name": "mvp_036_deterministic_training_check",
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "started_at_utc": started_at,
        "inputs": {
            "dataset_root": str(args.dataset_root),
            "split": str(args.split),
            "config": str(args.config),
            "init_model": str(args.init_model) if args.init_model else None,
            "artifact_dir": str(artifact_root),
            "model_id_prefix": args.model_id_prefix,
        },
        "runs": {
            "a": {"model_id": run_a_id, "return_code": rc_a},
            "b": {"model_id": run_b_id, "return_code": rc_b},
        },
        "determinism": {},
        "passed": False,
    }

    if rc_a != 0 or rc_b != 0:
        report["runs"]["a"]["stdout_tail"] = stdout_a[-2000:]
        report["runs"]["a"]["stderr_tail"] = stderr_a[-2000:]
        report["runs"]["b"]["stdout_tail"] = stdout_b[-2000:]
        report["runs"]["b"]["stderr_tail"] = stderr_b[-2000:]
        report["determinism"] = {"error": "training subprocess failed"}
        dump_json(args.output, report)
        print(f"Wrote determinism report -> {args.output}")
        if cleanup_needed:
            shutil.rmtree(artifact_root, ignore_errors=True)
        return 1

    a_model = load_json(output_dir / f"{run_a_id}.model.json")
    b_model = load_json(output_dir / f"{run_b_id}.model.json")
    a_eval = load_json(output_dir / f"{run_a_id}.eval.json")
    b_eval = load_json(output_dir / f"{run_b_id}.eval.json")
    a_predictions = load_predictions(output_dir / f"{run_a_id}.predictions.jsonl")
    b_predictions = load_predictions(output_dir / f"{run_b_id}.predictions.jsonl")

    model_match = canonical_dumps(canonicalize_model(a_model)) == canonical_dumps(canonicalize_model(b_model))
    eval_match = canonical_dumps(canonicalize_eval(a_eval)) == canonical_dumps(canonicalize_eval(b_eval))
    predictions_match = canonical_dumps(a_predictions) == canonical_dumps(b_predictions)

    report["determinism"] = {
        "model_payload_match": model_match,
        "eval_payload_match": eval_match,
        "predictions_match": predictions_match,
        "model_hash_a": sha256_text(canonical_dumps(canonicalize_model(a_model))),
        "model_hash_b": sha256_text(canonical_dumps(canonicalize_model(b_model))),
        "eval_hash_a": sha256_text(canonical_dumps(canonicalize_eval(a_eval))),
        "eval_hash_b": sha256_text(canonical_dumps(canonicalize_eval(b_eval))),
        "predictions_hash_a": sha256_text(canonical_dumps(a_predictions)),
        "predictions_hash_b": sha256_text(canonical_dumps(b_predictions)),
    }
    report["passed"] = bool(model_match and eval_match and predictions_match)

    dump_json(args.output, report)
    print(f"Wrote determinism report -> {args.output}")
    print(f"Determinism passed: {report['passed']}")

    if cleanup_needed:
        shutil.rmtree(artifact_root, ignore_errors=True)

    return 0 if report["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
