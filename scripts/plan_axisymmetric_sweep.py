#!/usr/bin/env python3
from __future__ import annotations

import argparse
import itertools
import json
import math
import sys
from collections.abc import Iterable
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = PROJECT_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from interact_morph.io_utils import dump_json, load_json_or_yaml

G = 9.80665


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Plan Family A axisymmetric simulation sweep (MVP-015/016).")
    parser.add_argument("--config", required=True, type=Path, help="Sweep config JSON/YAML")
    parser.add_argument("--output", required=True, type=Path, help="Output JSONL with simulation cases")
    parser.add_argument("--manifest-output", type=Path, default=None, help="Output JSON manifest path")
    parser.add_argument("--family", default="A", choices=["A", "B", "C"])
    return parser.parse_args()


def _linspace(min_value: float, max_value: float, steps: int) -> list[float]:
    if steps <= 1:
        return [float(min_value)]
    width = max_value - min_value
    return [float(min_value + (width * idx / (steps - 1))) for idx in range(steps)]


def expand_parameter(name: str, spec: Any) -> list[float]:
    if not isinstance(spec, dict):
        raise ValueError(f"parameter {name!r} must be an object")

    if "values" in spec:
        values = spec["values"]
        if not isinstance(values, Iterable) or isinstance(values, (str, bytes)):
            raise ValueError(f"parameter {name!r}.values must be a list")
        expanded = [float(v) for v in values]
    else:
        if "min" not in spec or "max" not in spec:
            raise ValueError(f"parameter {name!r} requires either values or min/max")
        if "steps" in spec:
            steps = int(spec["steps"])
        elif "step" in spec:
            step = float(spec["step"])
            if step <= 0:
                raise ValueError(f"parameter {name!r}.step must be > 0")
            span = float(spec["max"]) - float(spec["min"])
            steps = int(math.floor(span / step)) + 1
        else:
            raise ValueError(f"parameter {name!r} must set steps or step when using min/max")
        expanded = _linspace(float(spec["min"]), float(spec["max"]), steps)

    if not expanded:
        raise ValueError(f"parameter {name!r} expanded to 0 values")
    return expanded


def compute_dimensionless(case: dict[str, float]) -> dict[str, float]:
    rho = case["core_density_kg_m3"]
    mu = case["core_viscosity_pa_s"]
    sigma = case["interfacial_tension_n_m"]
    l = case["droplet_diameter_mm"] / 1000.0
    v = case["impact_velocity_m_s"]
    we = rho * v * v * l / sigma
    oh = mu / math.sqrt(rho * sigma * l)
    bo = rho * G * l * l / sigma
    return {"weber": we, "ohnesorge": oh, "bond": bo}


def passes_constraints(case: dict[str, float], dims: dict[str, float], constraints: dict[str, Any]) -> bool:
    shell_minus_droplet = case["shell_outer_diameter_mm"] - case["droplet_diameter_mm"]
    min_gap = constraints.get("shell_outer_minus_droplet_min_mm")
    max_gap = constraints.get("shell_outer_minus_droplet_max_mm")
    if min_gap is not None and shell_minus_droplet < float(min_gap):
        return False
    if max_gap is not None and shell_minus_droplet > float(max_gap):
        return False

    for key, dim_name in (("weber_min", "weber"), ("weber_max", "weber"), ("ohnesorge_max", "ohnesorge"), ("bond_max", "bond")):
        if key not in constraints:
            continue
        value = float(constraints[key])
        current = dims[dim_name]
        if key.endswith("_min") and current < value:
            return False
        if key.endswith("_max") and current > value:
            return False
    return True


def main() -> int:
    args = parse_args()
    cfg = load_json_or_yaml(args.config)

    sweep_name = str(cfg.get("sweep_name", "axisymmetric_sweep"))
    parameters = cfg.get("parameters", {})
    if not isinstance(parameters, dict) or not parameters:
        raise ValueError("config.parameters must be a non-empty object")
    required_parameters = {
        "impact_velocity_m_s",
        "droplet_diameter_mm",
        "shell_outer_diameter_mm",
        "interfacial_layer_thickness_mm",
        "core_density_kg_m3",
        "core_viscosity_pa_s",
        "interfacial_tension_n_m",
    }
    missing_parameters = sorted(required_parameters - set(parameters.keys()))
    if missing_parameters:
        raise ValueError(f"config.parameters missing required keys: {', '.join(missing_parameters)}")

    expanded = {name: expand_parameter(name, spec) for name, spec in parameters.items()}
    param_names = list(expanded.keys())
    constraints = cfg.get("constraints", {})
    if not isinstance(constraints, dict):
        raise ValueError("config.constraints must be an object if provided")

    planned_cases: list[dict[str, Any]] = []
    total_candidates = 0
    for values in itertools.product(*(expanded[name] for name in param_names)):
        total_candidates += 1
        case = {name: value for name, value in zip(param_names, values)}
        dims = compute_dimensionless(case)
        if not passes_constraints(case, dims, constraints):
            continue

        case_idx = len(planned_cases) + 1
        simulation_id = f"SIM_{args.family}_{case_idx:06d}"
        planned_cases.append(
            {
                "simulation_id": simulation_id,
                "family": args.family,
                "sweep_name": sweep_name,
                "control_parameters": {
                    "impact_velocity_m_s": case["impact_velocity_m_s"],
                    "droplet_diameter_mm": case["droplet_diameter_mm"],
                    "shell_outer_diameter_mm": case["shell_outer_diameter_mm"],
                    "interfacial_layer_thickness_mm": case["interfacial_layer_thickness_mm"],
                },
                "fluid_system": {
                    "core_density_kg_m3": case["core_density_kg_m3"],
                    "core_viscosity_pa_s": case["core_viscosity_pa_s"],
                    "interfacial_tension_n_m": case["interfacial_tension_n_m"],
                },
                "dimensionless": dims,
                "status": "planned",
            }
        )

    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("w", encoding="utf-8") as f:
        for row in planned_cases:
            f.write(json.dumps(row, sort_keys=False) + "\n")

    manifest_output = args.manifest_output
    if manifest_output is None:
        manifest_output = args.output.with_suffix(".manifest.json")
    manifest = {
        "sweep_name": sweep_name,
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "family": args.family,
        "source_config": str(args.config),
        "parameters": {name: expanded[name] for name in param_names},
        "constraints": constraints,
        "candidate_count": total_candidates,
        "planned_count": len(planned_cases),
        "output_jsonl": str(args.output),
    }
    dump_json(manifest_output, manifest)

    print(f"Wrote planned simulations: {len(planned_cases)} / {total_candidates} -> {args.output}")
    print(f"Wrote manifest -> {manifest_output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
