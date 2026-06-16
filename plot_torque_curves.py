from __future__ import annotations

from dataclasses import replace
from pathlib import Path

import matplotlib.pyplot as plt

from actuator_design import calculate_design, load_config, parse_design_input


def get_output_dir(config: dict) -> Path:
    plot_config = config.get("plot", {})
    output_dir = Path(plot_config.get("output_dir", "docs"))
    output_dir.mkdir(parents=True, exist_ok=True)
    return output_dir


def configure_style() -> None:
    plt.rcParams["font.sans-serif"] = [
        "Microsoft YaHei",
        "SimHei",
        "Arial Unicode MS",
        "DejaVu Sans",
    ]
    plt.rcParams["axes.unicode_minus"] = False
    plt.rcParams["figure.facecolor"] = "white"
    plt.rcParams["axes.facecolor"] = "white"


def annotate_key_points(
    ax, x_values: list[float], y_values: list[float], unit: str
) -> None:
    key_indexes = sorted({0, len(x_values) - 1})
    for index in key_indexes:
        ax.annotate(
            f"{y_values[index]:.2f} {unit}",
            xy=(x_values[index], y_values[index]),
            xytext=(0, 10),
            textcoords="offset points",
            ha="center",
            fontsize=9,
            bbox={"boxstyle": "round,pad=0.25", "fc": "white", "ec": "#d8dee9"},
        )


def annotate_default_point(
    ax,
    x_value: float,
    y_value: float,
    label: str,
    unit: str,
    marker: str = "D",
    xytext: tuple[int, int] = (28, 34),
    ha: str = "left",
) -> None:
    ax.scatter(
        [x_value],
        [y_value],
        marker=marker,
        s=58,
        color="#111827",
        edgecolor="white",
        linewidth=0.8,
        zorder=4,
    )
    ax.annotate(
        f"{label}\n{y_value:.2f} {unit}",
        xy=(x_value, y_value),
        xytext=xytext,
        textcoords="offset points",
        ha=ha,
        fontsize=8.5,
        bbox={"boxstyle": "round,pad=0.28", "fc": "white", "ec": "#cbd5e1"},
        arrowprops={"arrowstyle": "->", "color": "#64748b", "lw": 0.9},
    )


def mark_default_gear_ratio(ax, gear_ratio: float) -> None:
    ax.axvline(
        gear_ratio,
        color="#64748b",
        linestyle="--",
        linewidth=1.2,
        alpha=0.75,
        zorder=1,
    )


def finish_plot(fig, ax) -> None:
    ax.margins(x=0.08, y=0.18)
    ax.grid(True, linestyle="--", alpha=0.35)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.legend(frameon=False, loc="best", fontsize=8.5)
    fig.tight_layout()


def plot_load_sweep(config_path: str = "config.yaml") -> Path:
    config = load_config(config_path)
    base_input = parse_design_input(config)
    plot_config = config.get("plot", {})
    loads_kg = plot_config.get("loads_kg", [1, 2, 3, 5, 8, 10])
    output_dir = get_output_dir(config)

    torques = []
    for load_mass_kg in loads_kg:
        design_input = replace(base_input, load_mass_kg=float(load_mass_kg))
        torques.append(calculate_design(design_input).required_joint_torque_nm)

    fig, ax = plt.subplots(figsize=(8, 4.8))
    ax.plot(
        loads_kg,
        torques,
        marker="o",
        linewidth=2.4,
        color="#2563eb",
        label="Required joint torque / 关节所需扭矩",
    )
    ax.set_title("Joint Torque vs Load Mass\n关节所需扭矩随负载质量变化")
    ax.set_xlabel("Load mass / 负载质量 (kg)")
    ax.set_ylabel("Required joint torque / 关节所需扭矩 (N·m)")
    annotate_key_points(ax, list(map(float, loads_kg)), torques, "N·m")
    default_result = calculate_design(base_input)
    annotate_default_point(
        ax,
        base_input.load_mass_kg,
        default_result.required_joint_torque_nm,
        f"Default load / 默认负载 = {base_input.load_mass_kg:g} kg",
        "N·m",
        xytext=(-28, 54),
        ha="right",
    )
    finish_plot(fig, ax)

    output_path = output_dir / "torque_vs_load.png"
    fig.savefig(output_path, dpi=180, bbox_inches="tight")
    plt.close(fig)
    return output_path


def plot_motor_torque_sweep(config_path: str = "config.yaml") -> Path:
    config = load_config(config_path)
    base_input = parse_design_input(config)
    plot_config = config.get("plot", {})
    gear_ratios = plot_config.get("gear_ratios", [10, 20, 50, 80, 100])
    output_dir = get_output_dir(config)

    motor_torques = []
    for gear_ratio in gear_ratios:
        design_input = replace(base_input, gear_ratio=float(gear_ratio))
        motor_torques.append(calculate_design(design_input).motor_side_torque_nm)

    fig, ax = plt.subplots(figsize=(8, 4.8))
    ax.plot(
        gear_ratios,
        motor_torques,
        marker="s",
        color="#b4492f",
        linewidth=2.4,
        label="Motor-side torque / 电机侧扭矩",
    )
    ax.set_title("Motor-Side Torque vs Gear Ratio\n电机侧扭矩随减速比变化")
    ax.set_xlabel("Gear ratio / 减速比")
    ax.set_ylabel("Motor-side torque / 电机侧扭矩 (N·m)")
    annotate_key_points(ax, list(map(float, gear_ratios)), motor_torques, "N·m")
    mark_default_gear_ratio(ax, base_input.gear_ratio)
    default_result = calculate_design(base_input)
    annotate_default_point(
        ax,
        base_input.gear_ratio,
        default_result.motor_side_torque_nm,
        f"Default gear ratio / 默认减速比 = {base_input.gear_ratio:g}",
        "N·m",
        marker="o",
    )
    finish_plot(fig, ax)

    output_path = output_dir / "motor_torque_vs_gear_ratio.png"
    fig.savefig(output_path, dpi=180, bbox_inches="tight")
    plt.close(fig)
    return output_path


def plot_motor_speed_sweep(config_path: str = "config.yaml") -> Path:
    config = load_config(config_path)
    base_input = parse_design_input(config)
    plot_config = config.get("plot", {})
    gear_ratios = plot_config.get("gear_ratios", [10, 20, 50, 80, 100])
    output_dir = get_output_dir(config)

    motor_speeds = []
    for gear_ratio in gear_ratios:
        design_input = replace(base_input, gear_ratio=float(gear_ratio))
        motor_speeds.append(calculate_design(design_input).motor_speed_rpm)

    fig, ax = plt.subplots(figsize=(8, 4.8))
    ax.plot(
        gear_ratios,
        motor_speeds,
        marker="^",
        color="#15803d",
        linewidth=2.4,
        label="Motor speed / 电机转速",
    )
    ax.set_title("Motor Speed vs Gear Ratio\n电机转速随减速比变化")
    ax.set_xlabel("Gear ratio / 减速比")
    ax.set_ylabel("Motor speed / 电机转速 (rpm)")
    annotate_key_points(ax, list(map(float, gear_ratios)), motor_speeds, "rpm")
    mark_default_gear_ratio(ax, base_input.gear_ratio)
    default_result = calculate_design(base_input)
    annotate_default_point(
        ax,
        base_input.gear_ratio,
        default_result.motor_speed_rpm,
        f"Default gear ratio / 默认减速比 = {base_input.gear_ratio:g}",
        "rpm",
        marker="o",
        xytext=(30, -82),
    )
    finish_plot(fig, ax)

    output_path = output_dir / "motor_speed_vs_gear_ratio.png"
    fig.savefig(output_path, dpi=180, bbox_inches="tight")
    plt.close(fig)
    return output_path


def main() -> None:
    configure_style()
    load_plot = plot_load_sweep()
    torque_ratio_plot = plot_motor_torque_sweep()
    speed_ratio_plot = plot_motor_speed_sweep()
    print(f"Generated: {load_plot}")
    print(f"Generated: {torque_ratio_plot}")
    print(f"Generated: {speed_ratio_plot}")


if __name__ == "__main__":
    main()
