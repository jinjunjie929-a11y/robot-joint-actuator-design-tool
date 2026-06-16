from __future__ import annotations

import argparse
from typing import Any

from actuator_design import (
    calculate_design,
    format_result,
    load_config,
    parse_design_input,
    parse_design_limit,
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Preliminary robot joint actuator design calculator."
    )
    parser.add_argument(
        "-c",
        "--config",
        default="config.yaml",
        help="Path to the YAML configuration file.",
    )
    parser.add_argument("--load-mass-kg", type=float, help="Override load mass.")
    parser.add_argument("--link-length-m", type=float, help="Override link length.")
    parser.add_argument(
        "--target-angular-velocity-rad-s",
        type=float,
        help="Override target angular velocity.",
    )
    parser.add_argument(
        "--target-angular-acceleration-rad-s2",
        type=float,
        help="Override target angular acceleration.",
    )
    parser.add_argument("--gear-ratio", type=float, help="Override gear ratio.")
    parser.add_argument(
        "--transmission-efficiency",
        type=float,
        help="Override transmission efficiency.",
    )
    parser.add_argument("--safety-factor", type=float, help="Override safety factor.")
    return parser


def apply_overrides(config: dict[str, Any], args: argparse.Namespace) -> dict[str, Any]:
    config.setdefault("inputs", {})
    override_map = {
        "load_mass_kg": args.load_mass_kg,
        "link_length_m": args.link_length_m,
        "target_angular_velocity_rad_s": args.target_angular_velocity_rad_s,
        "target_angular_acceleration_rad_s2": args.target_angular_acceleration_rad_s2,
        "gear_ratio": args.gear_ratio,
        "transmission_efficiency": args.transmission_efficiency,
        "safety_factor": args.safety_factor,
    }
    for key, value in override_map.items():
        if value is not None:
            config["inputs"][key] = value
    return config


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    config = apply_overrides(load_config(args.config), args)
    design_input = parse_design_input(config)
    design_limit = parse_design_limit(config)
    result = calculate_design(design_input, design_limit)
    print(format_result(result))


if __name__ == "__main__":
    main()
