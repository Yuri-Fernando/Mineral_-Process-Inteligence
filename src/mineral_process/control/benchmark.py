"""Seeded, same-disturbance controller benchmark for the synthetic plant."""

from __future__ import annotations

from dataclasses import asdict
from pathlib import Path

import numpy as np
import pandas as pd

from mineral_process.control.mpc import economic_mpc
from mineral_process.simulation.digital_twin import PlantAction, SyntheticMineralPlant


def _rule_action(state: dict[str, float]) -> PlantAction:
    hardness = state["feed_hardness"]
    grade = state["feed_grade"]
    return PlantAction(
        air_flow=float(np.clip(1.45 + 8 * (0.012 - grade), 0.5, 2.5)),
        pulp_level=0.58,
        ph=10.1,
        reagent_gpt=float(np.clip(35 + 1.5 * (hardness - 16), 5, 80)),
        throughput_tph=float(np.clip(110 - 2.0 * (hardness - 16), 60, 180)),
    )


def _run_controller(name: str, steps: int, seed: int) -> pd.DataFrame:
    plant = SyntheticMineralPlant(seed)
    action = PlantAction(1.45, 0.58, 10.1, 35, 110)
    rows: list[dict[str, float | str | int]] = []
    for step in range(steps):
        if step == steps // 3:
            plant.inject_disturbance(hardness=23.0, feed_grade=0.0095)
        if name == "rule_based":
            action = _rule_action(plant.observe())
        elif name == "economic_mpc" and step % 5 == 0:
            result = economic_mpc(plant.observe(), previous_action=action, horizon=5)
            if result.success:
                action = result.action
        state = plant.step(action)
        rows.append({"controller": name, "step": step, **state, **asdict(action)})
    return pd.DataFrame(rows)


def benchmark_controllers(
    output_dir: Path = Path("reports/generated/mpc"), steps: int = 45, seed: int = 42
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Compare fixed, rule-based and economic MPC under an identical disturbance schedule."""
    output_dir.mkdir(parents=True, exist_ok=True)
    trajectory = pd.concat(
        [_run_controller(name, steps, seed) for name in ("fixed", "rule_based", "economic_mpc")],
        ignore_index=True,
    )
    summaries: list[dict[str, float | str | int]] = []
    for name, group in trajectory.groupby("controller"):
        actions = group[["air_flow", "pulp_level", "ph", "reagent_gpt", "throughput_tph"]]
        summaries.append(
            {
                "controller": name,
                "average_recovery": float(group["recovery"].mean()),
                "average_grade": float(group["concentrate_grade"].mean()),
                "grade_violations": int((group["concentrate_grade"] < 0.18).sum()),
                "average_energy_kwh_t": float(group["specific_energy_kwh_t"].mean()),
                "average_reagent_gpt": float(group["reagent_gpt"].mean()),
                "control_effort": float(actions.diff().pow(2).sum().sum()),
            }
        )
    metrics = pd.DataFrame(summaries).sort_values("controller")
    trajectory.to_csv(output_dir / "mpc_trajectories.csv", index=False)
    metrics.to_csv(output_dir / "mpc_benchmark.csv", index=False)
    (output_dir / "mpc_benchmark_report.html").write_text(
        "<h1>Controller benchmark</h1>"
        "<p>Fixed, rule-based and economic MPC controllers receive the same seeded synthetic "
        "disturbance. Results apply only to this educational digital twin.</p>"
        + metrics.to_html(index=False, float_format=lambda value: f"{value:.4f}"),
        encoding="utf-8",
    )
    return trajectory, metrics
