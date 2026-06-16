from __future__ import annotations

from dataclasses import dataclass
from math import pi
from pathlib import Path
from typing import Any

import yaml


@dataclass(frozen=True)
class JointDesignInput:
    load_mass_kg: float
    link_length_m: float
    target_angular_velocity_rad_s: float
    target_angular_acceleration_rad_s2: float
    gear_ratio: float
    transmission_efficiency: float
    safety_factor: float
    gravity_m_s2: float = 9.81


@dataclass(frozen=True)
class DesignLimit:
    max_motor_torque_nm: float
    max_motor_speed_rpm: float
    max_power_w: float


@dataclass(frozen=True)
class JointDesignResult:
    gravitational_torque_nm: float
    acceleration_torque_nm: float
    nominal_joint_torque_nm: float
    required_joint_torque_nm: float
    motor_side_torque_nm: float
    motor_speed_rpm: float
    reducer_output_torque_nm: float
    reducer_output_speed_rpm: float
    estimated_power_w: float
    actual_safety_factor: float | None
    meets_design: bool
    check_message: str


def load_config(config_path: str | Path = "config.yaml") -> dict[str, Any]:
    path = Path(config_path)
    with path.open("r", encoding="utf-8") as file:
        config = yaml.safe_load(file) or {}
    return config


def parse_design_input(config: dict[str, Any]) -> JointDesignInput:
    values = config.get("inputs", {})
    return JointDesignInput(
        load_mass_kg=float(values["load_mass_kg"]),
        link_length_m=float(values["link_length_m"]),
        target_angular_velocity_rad_s=float(values["target_angular_velocity_rad_s"]),
        target_angular_acceleration_rad_s2=float(
            values["target_angular_acceleration_rad_s2"]
        ),
        gear_ratio=float(values["gear_ratio"]),
        transmission_efficiency=float(values["transmission_efficiency"]),
        safety_factor=float(values["safety_factor"]),
        gravity_m_s2=float(values.get("gravity_m_s2", 9.81)),
    )


def parse_design_limit(config: dict[str, Any]) -> DesignLimit:
    values = config.get("design_limits", {})
    return DesignLimit(
        max_motor_torque_nm=float(values["max_motor_torque_nm"]),
        max_motor_speed_rpm=float(values["max_motor_speed_rpm"]),
        max_power_w=float(values["max_power_w"]),
    )


def validate_input(design_input: JointDesignInput) -> None:
    positive_fields = {
        "load_mass_kg": design_input.load_mass_kg,
        "link_length_m": design_input.link_length_m,
        "gear_ratio": design_input.gear_ratio,
        "transmission_efficiency": design_input.transmission_efficiency,
        "safety_factor": design_input.safety_factor,
        "gravity_m_s2": design_input.gravity_m_s2,
    }
    for name, value in positive_fields.items():
        if value <= 0:
            raise ValueError(f"{name} must be greater than 0, got {value}")
    if design_input.transmission_efficiency > 1:
        raise ValueError("transmission_efficiency should be in the range (0, 1]")


def calculate_design(
    design_input: JointDesignInput, design_limit: DesignLimit | None = None
) -> JointDesignResult:
    validate_input(design_input)

    gravitational_torque_nm = (
        design_input.load_mass_kg
        * design_input.gravity_m_s2
        * design_input.link_length_m
    )
    equivalent_inertia_kg_m2 = design_input.load_mass_kg * design_input.link_length_m**2
    acceleration_torque_nm = (
        equivalent_inertia_kg_m2 * design_input.target_angular_acceleration_rad_s2
    )
    nominal_joint_torque_nm = gravitational_torque_nm + acceleration_torque_nm
    required_joint_torque_nm = nominal_joint_torque_nm * design_input.safety_factor

    motor_side_torque_nm = required_joint_torque_nm / (
        design_input.gear_ratio * design_input.transmission_efficiency
    )
    motor_speed_rpm = (
        design_input.target_angular_velocity_rad_s
        * design_input.gear_ratio
        * 60
        / (2 * pi)
    )
    reducer_output_speed_rpm = (
        design_input.target_angular_velocity_rad_s * 60 / (2 * pi)
    )
    estimated_power_w = (
        abs(required_joint_torque_nm * design_input.target_angular_velocity_rad_s)
        / design_input.transmission_efficiency
    )

    actual_safety_factor = None
    meets_design = True
    messages: list[str] = []
    if design_limit is not None:
        available_output_torque_nm = (
            design_limit.max_motor_torque_nm
            * design_input.gear_ratio
            * design_input.transmission_efficiency
        )
        actual_safety_factor = available_output_torque_nm / nominal_joint_torque_nm
        checks = {
            "motor torque": motor_side_torque_nm <= design_limit.max_motor_torque_nm,
            "motor speed": motor_speed_rpm <= design_limit.max_motor_speed_rpm,
            "power": estimated_power_w <= design_limit.max_power_w,
            "safety factor": actual_safety_factor >= design_input.safety_factor,
        }
        failed_checks = [name for name, passed in checks.items() if not passed]
        meets_design = not failed_checks
        messages.append(
            "passed all configured checks"
            if meets_design
            else "failed checks: " + ", ".join(failed_checks)
        )
    else:
        messages.append("no design limits configured")

    return JointDesignResult(
        gravitational_torque_nm=gravitational_torque_nm,
        acceleration_torque_nm=acceleration_torque_nm,
        nominal_joint_torque_nm=nominal_joint_torque_nm,
        required_joint_torque_nm=required_joint_torque_nm,
        motor_side_torque_nm=motor_side_torque_nm,
        motor_speed_rpm=motor_speed_rpm,
        reducer_output_torque_nm=required_joint_torque_nm,
        reducer_output_speed_rpm=reducer_output_speed_rpm,
        estimated_power_w=estimated_power_w,
        actual_safety_factor=actual_safety_factor,
        meets_design=meets_design,
        check_message="; ".join(messages),
    )


def format_result(result: JointDesignResult) -> str:
    actual_sf = (
        "N/A"
        if result.actual_safety_factor is None
        else f"{result.actual_safety_factor:.2f}"
    )
    lines = [
        "Robot Joint Actuator Design Result",
        "-" * 40,
        f"Gravity torque:              {result.gravitational_torque_nm:10.3f} N·m",
        f"Acceleration torque:         {result.acceleration_torque_nm:10.3f} N·m",
        f"Nominal joint torque:        {result.nominal_joint_torque_nm:10.3f} N·m",
        f"Required joint torque:       {result.required_joint_torque_nm:10.3f} N·m",
        f"Motor-side torque:           {result.motor_side_torque_nm:10.3f} N·m",
        f"Motor speed:                 {result.motor_speed_rpm:10.1f} rpm",
        f"Reducer output torque:       {result.reducer_output_torque_nm:10.3f} N·m",
        f"Reducer output speed:        {result.reducer_output_speed_rpm:10.1f} rpm",
        f"Estimated power:             {result.estimated_power_w:10.1f} W",
        f"Actual safety factor:        {actual_sf:>10}",
        f"Meets design requirement:    {'YES' if result.meets_design else 'NO':>10}",
        f"Check message:               {result.check_message}",
    ]
    return "\n".join(lines)
