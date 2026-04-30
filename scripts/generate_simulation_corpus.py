#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import math
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = PROJECT_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from interact_morph.io_utils import dump_json, load_json_or_yaml
from interact_morph.run_id_utils import canonicalize_run_id, ensure_unique_run_id
from interact_morph.schema_utils import validate_with_schema


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate synthetic Family A simulation corpus from planned axisymmetric sweep cases (MVP-017)."
    )
    parser.add_argument("--plan-jsonl", required=True, type=Path, help="Planned sweep JSONL from plan_axisymmetric_sweep.py")
    parser.add_argument("--output-root", required=True, type=Path, help="Output dataset root (contains runs/ and manifests/)")
    parser.add_argument(
        "--surrogate-config",
        default=Path("configs/simulations/family_a_axisymmetric_surrogate.json"),
        type=Path,
        help="Config for deterministic surrogate solver behavior",
    )
    parser.add_argument("--run-schema", default=Path("schemas/run_metadata.schema.json"), type=Path)
    parser.add_argument("--features-schema", default=Path("schemas/derived_features.schema.json"), type=Path)
    parser.add_argument("--family", default="A", choices=["A", "B", "C"])
    parser.add_argument("--max-cases", type=int, default=None, help="Optional cap for quick smoke runs")
    parser.add_argument("--overwrite", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    return parser.parse_args()


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            payload = json.loads(line)
            if not isinstance(payload, dict):
                raise ValueError(f"plan row must be an object, got {type(payload).__name__}")
            rows.append(payload)
    return rows


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        for row in rows:
            f.write(json.dumps(row, sort_keys=False) + "\n")


def file_sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        while True:
            chunk = f.read(1024 * 1024)
            if not chunk:
                break
            h.update(chunk)
    return h.hexdigest()


def stable_num_token(value: float, scale: int = 1000) -> str:
    return str(int(round(float(value) * scale)))


def build_fluid_combination_id(case: dict[str, Any]) -> str:
    fluid = case["fluid_system"]
    rho = stable_num_token(float(fluid["core_density_kg_m3"]), scale=1)
    mu = stable_num_token(float(fluid["core_viscosity_pa_s"]), scale=1_000_000)
    sigma = stable_num_token(float(fluid["interfacial_tension_n_m"]), scale=1000)
    return f"SIM_CORE{rho}_MU{mu}_SIGMA{sigma}"


def build_time_grid(cfg: dict[str, Any]) -> list[float]:
    grid_cfg = cfg.get("time_grid_ms", {})
    start = float(grid_cfg.get("start", 0.0))
    end = float(grid_cfg.get("end", 20.0))
    step = float(grid_cfg.get("step", 1.0))
    if step <= 0:
        raise ValueError("surrogate_config.time_grid_ms.step must be > 0")
    if end < start:
        raise ValueError("surrogate_config.time_grid_ms.end must be >= start")

    points: list[float] = []
    t = start
    while t <= end + 1e-9:
        points.append(round(t, 6))
        t += step
    if not points:
        raise ValueError("time grid has zero points")
    return points


def simulate_case(case: dict[str, Any], cfg: dict[str, Any]) -> dict[str, Any]:
    control = case["control_parameters"]
    fluid = case["fluid_system"]
    dim = case.get("dimensionless", {})

    velocity = float(control["impact_velocity_m_s"])
    droplet_d = float(control["droplet_diameter_mm"])
    shell_outer_d = float(control["shell_outer_diameter_mm"])
    interfacial_layer_t = float(control["interfacial_layer_thickness_mm"])
    shell_gap = max(0.001, shell_outer_d - droplet_d)

    weber = float(dim["weber"])
    ohnesorge = float(dim["ohnesorge"])
    bond = float(dim["bond"])

    regime_cfg = cfg["regime_thresholds"]
    if weber < float(regime_cfg["trapping_weber_max"]):
        regime_label = "trapping"
        failure_mode = "trapping"
    elif weber > float(regime_cfg["rupture_weber_min"]):
        regime_label = "rupture_after_wrap"
        failure_mode = "premature_rupture"
    elif ohnesorge > float(regime_cfg["partial_ohnesorge_min"]):
        regime_label = "partial_wrapping"
        failure_mode = "partial_wrapping"
    elif shell_gap < float(regime_cfg["penetration_low_shell_gap_mm"]):
        regime_label = "penetration_no_wrap"
        failure_mode = "lateral_spreading"
    else:
        regime_label = "stable_wrapping"
        failure_mode = "none"

    success_cfg = cfg["success_window"]
    encapsulation_success = (
        regime_label == "stable_wrapping"
        and float(success_cfg["weber_min"]) <= weber <= float(success_cfg["weber_max"])
        and ohnesorge <= float(success_cfg["ohnesorge_max"])
        and bond <= float(success_cfg["bond_max"])
        and shell_gap >= float(success_cfg["min_shell_gap_mm"])
    )

    thickness_cfg = cfg["shell_thickness_model"]
    base_um = interfacial_layer_t * float(thickness_cfg["base_multiplier_um_per_mm"])
    velocity_factor = max(0.35, 1.0 - float(thickness_cfg["velocity_sensitivity"]) * max(0.0, velocity - 0.6))
    weber_factor = max(0.40, 1.0 - float(thickness_cfg["weber_sensitivity"]) * max(0.0, weber - 10.0))
    shell_thickness_mean_um = max(float(thickness_cfg["thickness_floor_um"]), base_um * velocity_factor * weber_factor)

    eccentricity_cfg = cfg["eccentricity_model"]
    capsule_eccentricity = (
        float(eccentricity_cfg["base"])
        + float(eccentricity_cfg["velocity_scale"]) * (velocity / 2.0)
        + float(eccentricity_cfg["oh_scale"]) * ohnesorge
        + 0.04 * abs(shell_gap - 0.8)
    )
    capsule_eccentricity = min(float(eccentricity_cfg["cap"]), max(0.0, capsule_eccentricity))

    penetration_depth_max_mm = max(0.05, droplet_d * min(1.5, 0.35 + 0.0075 * weber))
    neck_radius_min_mm = max(0.02, (0.38 * droplet_d) / (1.0 + 0.22 * math.sqrt(max(0.0, weber)) + 0.8 * ohnesorge))

    lamella_onset_ms = max(0.2, 0.6 + 0.8 / (velocity + 0.2))
    first_contact_ms = lamella_onset_ms + 0.8
    neck_formation_ms = first_contact_ms + 0.9 + 1.8 * ohnesorge
    closure_time_ms = neck_formation_ms + max(1.0, 4.5 / (1.0 + velocity)) + 1.2 * ohnesorge
    detachment_time_ms = closure_time_ms + 2.0 + 0.9 * ohnesorge
    rupture_time_ms = detachment_time_ms + 1.5 if regime_label == "rupture_after_wrap" else None

    t_values = build_time_grid(cfg)
    tau = max(0.6, closure_time_ms / 3.2)
    neck_start_mm = max(neck_radius_min_mm * 1.8, 0.15 * droplet_d)
    neck_width = max(0.8, 0.35 * closure_time_ms)
    shell_decay_tau = max(1.0, detachment_time_ms / 2.5)

    penetration_depth: list[dict[str, float]] = []
    neck_radius: list[dict[str, float]] = []
    shell_thickness: list[dict[str, float]] = []
    for t in t_values:
        depth_t = penetration_depth_max_mm * (1.0 - math.exp(-t / tau))
        if regime_label == "trapping":
            depth_t *= 0.9

        dip = math.exp(-((t - neck_formation_ms) / neck_width) ** 2)
        neck_t = neck_start_mm - (neck_start_mm - neck_radius_min_mm) * dip
        if t > closure_time_ms:
            neck_t += 0.03 * (t - closure_time_ms)
        neck_t = min(shell_outer_d / 2.0, max(neck_radius_min_mm, neck_t))

        shell_t = shell_thickness_mean_um * (1.08 - 0.08 * (1.0 - math.exp(-t / shell_decay_tau)))
        if regime_label in {"partial_wrapping", "rupture_after_wrap"}:
            shell_t *= 0.96

        penetration_depth.append({"t_ms": round(t, 6), "value": round(depth_t, 6)})
        neck_radius.append({"t_ms": round(t, 6), "value": round(neck_t, 6)})
        shell_thickness.append({"t_ms": round(t, 6), "value": round(max(1e-6, shell_t), 6)})

    return {
        "outcomes": {
            "encapsulation_success": bool(encapsulation_success),
            "regime_label": regime_label,
            "failure_mode": failure_mode,
            "shell_thickness_mean_um": round(shell_thickness_mean_um, 6),
            "capsule_eccentricity": round(capsule_eccentricity, 6),
        },
        "events_ms": {
            "lamella_onset_ms": round(lamella_onset_ms, 6),
            "first_contact_ms": round(first_contact_ms, 6),
            "neck_formation_ms": round(neck_formation_ms, 6),
            "closure_time_ms": round(closure_time_ms, 6),
            "detachment_time_ms": round(detachment_time_ms, 6),
            "rupture_time_ms": round(rupture_time_ms, 6) if rupture_time_ms is not None else None,
        },
        "summary": {
            "penetration_depth_max_mm": round(penetration_depth_max_mm, 6),
            "neck_radius_min_mm": round(neck_radius_min_mm, 6),
            "shell_thickness_mean_um": round(shell_thickness_mean_um, 6),
            "capsule_eccentricity": round(capsule_eccentricity, 6),
        },
        "trajectories": {
            "penetration_depth_mm": penetration_depth,
            "neck_radius_mm": neck_radius,
            "shell_thickness_um": shell_thickness,
        },
        "derived_context": {
            "dimensionless": {"weber": weber, "ohnesorge": ohnesorge, "bond": bond},
            "inputs": {
                "impact_velocity_m_s": velocity,
                "droplet_diameter_mm": droplet_d,
                "shell_outer_diameter_mm": shell_outer_d,
                "interfacial_layer_thickness_mm": interfacial_layer_t,
                "core_density_kg_m3": float(fluid["core_density_kg_m3"]),
                "core_viscosity_pa_s": float(fluid["core_viscosity_pa_s"]),
                "interfacial_tension_n_m": float(fluid["interfacial_tension_n_m"]),
            },
        },
    }


def build_metadata(
    run_id: str,
    simulation_id: str,
    case: dict[str, Any],
    result: dict[str, Any],
    family: str,
    surrogate_name: str,
    timestamp_utc: str,
    ambient_temperature_c: float,
) -> dict[str, Any]:
    fluid = case["fluid_system"]
    control = case["control_parameters"]
    rho_core = float(fluid["core_density_kg_m3"])
    mu_core = float(fluid["core_viscosity_pa_s"])
    sigma = float(fluid["interfacial_tension_n_m"])

    rho_shell = max(1.0, rho_core * 1.05)
    mu_shell = max(1e-6, mu_core * 1.8)
    rho_layer = (rho_core + rho_shell) / 2.0
    mu_layer = (mu_core + mu_shell) / 2.0

    return {
        "schema_version": "1.0.0",
        "run_id": run_id,
        "source_run_id": simulation_id,
        "family": family,
        "capture_timestamp": timestamp_utc,
        "fluid_combination_id": build_fluid_combination_id(case),
        "operator": "axisymmetric_surrogate_solver",
        "source": {
            "lab": "in-silico",
            "apparatus": surrogate_name,
            "camera_model": "synthetic_placeholder",
        },
        "fluid_system": {
            "core": {
                "material_id": f"core_rho{stable_num_token(rho_core, 1)}_mu{stable_num_token(mu_core, 1_000_000)}",
                "density_kg_m3": rho_core,
                "viscosity_pa_s": mu_core,
            },
            "shell": {
                "material_id": "shell_surrogate",
                "density_kg_m3": rho_shell,
                "viscosity_pa_s": mu_shell,
            },
            "interfacial_layer": {
                "material_id": "layer_surrogate",
                "thickness_mm": float(control["interfacial_layer_thickness_mm"]),
                "density_kg_m3": rho_layer,
                "viscosity_pa_s": mu_layer,
            },
            "interfacial_tension_n_m": sigma,
        },
        "control_parameters": {
            "impact_velocity_m_s": float(control["impact_velocity_m_s"]),
            "droplet_diameter_mm": float(control["droplet_diameter_mm"]),
            "shell_outer_diameter_mm": float(control["shell_outer_diameter_mm"]),
            "ambient_temperature_c": float(ambient_temperature_c),
        },
        "outcomes": {
            **result["outcomes"],
            "notes": f"Synthetic outcome generated from {simulation_id}",
        },
        "quality_flags": {
            "video_complete": True,
            "annotation_complete": True,
            "sensors_calibrated": True,
        },
        "asset_paths": {
            "video_relpath": "video.mp4",
            "labels_relpath": "labels.json",
            "derived_features_relpath": "derived_features.json",
        },
        "tags": [
            "synthetic",
            "simulation",
            "axisymmetric",
            str(case.get("sweep_name", "")),
        ],
    }


def build_derived_features(
    run_id: str,
    result: dict[str, Any],
    timestamp_utc: str,
    frame_rate_fps: float,
    surrogate_name: str,
) -> dict[str, Any]:
    return {
        "schema_version": "1.0.0",
        "run_id": run_id,
        "source_video": "video.mp4",
        "frame_rate_fps": float(frame_rate_fps),
        "segmentation_model_version": f"{surrogate_name}:direct_features",
        "extraction_timestamp": timestamp_utc,
        "events_ms": result["events_ms"],
        "summary": result["summary"],
        "trajectories": result["trajectories"],
    }


def build_labels(run_id: str, simulation_id: str, result: dict[str, Any], timestamp_utc: str) -> dict[str, Any]:
    return {
        "run_id": run_id,
        "encapsulation_success": result["outcomes"]["encapsulation_success"],
        "regime_label": result["outcomes"]["regime_label"],
        "failure_mode": result["outcomes"]["failure_mode"],
        "events_ms": result["events_ms"],
        "confidence": "simulated",
        "annotator": "axisymmetric_surrogate_solver",
        "annotation_timestamp": timestamp_utc,
        "notes": f"Auto-generated synthetic label for {simulation_id}",
    }


def ensure_case_shape(case: dict[str, Any], family: str) -> None:
    required = {"simulation_id", "family", "sweep_name", "control_parameters", "fluid_system", "dimensionless"}
    missing = sorted(required - set(case.keys()))
    if missing:
        raise ValueError(f"planned case missing fields: {', '.join(missing)}")
    if str(case["family"]) != family:
        raise ValueError(f"planned case family={case['family']!r} does not match --family={family!r}")


def main() -> int:
    args = parse_args()
    planned_cases = load_jsonl(args.plan_jsonl)
    if args.max_cases is not None:
        planned_cases = planned_cases[: max(0, int(args.max_cases))]
    if not planned_cases:
        print("No planned simulation cases found after filtering.")
        return 1

    surrogate_cfg = load_json_or_yaml(args.surrogate_config)
    surrogate_name = str(surrogate_cfg.get("name", "axisymmetric_surrogate_v1"))
    ambient_temperature_c = float(surrogate_cfg.get("ambient_temperature_c", 25.0))
    frame_rate_fps = float(surrogate_cfg.get("frame_rate_fps", 5000.0))

    runs_dir = args.output_root / "runs"
    manifests_dir = args.output_root / "manifests"
    if not args.dry_run:
        runs_dir.mkdir(parents=True, exist_ok=True)
        manifests_dir.mkdir(parents=True, exist_ok=True)

    run_rows: list[dict[str, Any]] = []
    run_id_map_rows: list[dict[str, Any]] = []
    simulation_index_rows: list[dict[str, Any]] = []
    errors: list[str] = []
    used_run_ids: set[str] = set()

    for case in planned_cases:
        try:
            ensure_case_shape(case, args.family)
            simulation_id = str(case["simulation_id"])
            base_run_id = canonicalize_run_id(args.family, simulation_id, simulation_id)
            run_id, collision_resolved = ensure_unique_run_id(base_run_id, used_run_ids, simulation_id)
            timestamp_utc = datetime.now(timezone.utc).isoformat()

            result = simulate_case(case, surrogate_cfg)
            metadata = build_metadata(
                run_id=run_id,
                simulation_id=simulation_id,
                case=case,
                result=result,
                family=args.family,
                surrogate_name=surrogate_name,
                timestamp_utc=timestamp_utc,
                ambient_temperature_c=ambient_temperature_c,
            )
            features = build_derived_features(
                run_id=run_id,
                result=result,
                timestamp_utc=timestamp_utc,
                frame_rate_fps=frame_rate_fps,
                surrogate_name=surrogate_name,
            )
            labels = build_labels(run_id=run_id, simulation_id=simulation_id, result=result, timestamp_utc=timestamp_utc)

            metadata_schema_errors = validate_with_schema(metadata, args.run_schema)
            features_schema_errors = validate_with_schema(features, args.features_schema)
            if metadata_schema_errors or features_schema_errors:
                messages = [f"{simulation_id}: schema validation failed"]
                messages.extend([f"metadata: {msg}" for msg in metadata_schema_errors])
                messages.extend([f"derived_features: {msg}" for msg in features_schema_errors])
                raise ValueError("; ".join(messages))

            run_relpath = f"runs/{run_id}"
            run_rows.append(
                {
                    "run_id": run_id,
                    "source_run_id": simulation_id,
                    "run_id_mode": "simulation",
                    "family": args.family,
                    "fluid_combination_id": metadata["fluid_combination_id"],
                    "capture_timestamp": metadata["capture_timestamp"],
                    "encapsulation_success": metadata["outcomes"]["encapsulation_success"],
                    "regime_label": metadata["outcomes"]["regime_label"],
                    "quality_flags": metadata["quality_flags"],
                    "run_relpath": run_relpath,
                    "video_file": "video.mp4",
                    "simulation_id": simulation_id,
                    "sweep_name": case["sweep_name"],
                }
            )
            run_id_map_rows.append(
                {
                    "simulation_id": simulation_id,
                    "canonical_run_id": run_id,
                    "collision_resolved": collision_resolved,
                }
            )
            simulation_index_rows.append(
                {
                    "simulation_id": simulation_id,
                    "run_id": run_id,
                    "family": args.family,
                    "sweep_name": case["sweep_name"],
                    "status": "synthetic_generated",
                    "dimensionless": case["dimensionless"],
                    "control_parameters": case["control_parameters"],
                    "fluid_system": case["fluid_system"],
                    "outputs": result["summary"],
                }
            )

            if not args.dry_run:
                run_dir = runs_dir / run_id
                if run_dir.exists() and args.overwrite:
                    shutil.rmtree(run_dir)
                elif run_dir.exists():
                    raise FileExistsError(f"destination exists: {run_dir} (use --overwrite)")

                run_dir.mkdir(parents=True, exist_ok=True)
                dump_json(run_dir / "metadata.json", metadata)
                dump_json(run_dir / "derived_features.json", features)
                dump_json(run_dir / "labels.json", labels)
                (run_dir / "video.mp4").write_bytes(b"")
        except Exception as exc:  # noqa: BLE001
            errors.append(str(exc))

    if errors:
        print("Synthetic corpus generation finished with errors:")
        for err in errors:
            print(f"- {err}")

    if not args.dry_run and run_rows:
        run_index_path = manifests_dir / "runs_index.jsonl"
        run_id_map_path = manifests_dir / "run_id_map.jsonl"
        simulation_index_path = manifests_dir / "simulation_index.jsonl"
        write_jsonl(run_index_path, run_rows)
        write_jsonl(run_id_map_path, run_id_map_rows)
        write_jsonl(simulation_index_path, simulation_index_rows)

        dataset_manifest = {
            "created_at_utc": datetime.now(timezone.utc).isoformat(),
            "family": args.family,
            "surrogate_name": surrogate_name,
            "source_plan_jsonl": str(args.plan_jsonl),
            "surrogate_config": str(args.surrogate_config),
            "output_root": str(args.output_root),
            "planned_case_count": len(planned_cases),
            "generated_case_count": len(run_rows),
            "error_count": len(errors),
            "artifact_notes": "video.mp4 files are placeholders for MVP-017 corpus bootstrapping",
            "run_index_sha256": file_sha256(run_index_path),
            "run_id_map_sha256": file_sha256(run_id_map_path),
            "simulation_index_sha256": file_sha256(simulation_index_path),
        }
        dump_json(manifests_dir / "dataset_manifest.json", dataset_manifest)

    print(f"Planned cases considered: {len(planned_cases)}")
    print(f"Generated synthetic runs: {len(run_rows)}")
    print(f"Errors: {len(errors)}")
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
