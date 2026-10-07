"""Bounded economic MPC prototype built on the deterministic digital twin."""

from dataclasses import dataclass

import numpy as np
from scipy.optimize import minimize

from mineral_process.simulation.digital_twin import PlantAction, SyntheticMineralPlant


@dataclass(frozen=True)
class MPCResult:
    action: PlantAction
    success: bool
    objective: float
    iterations: int
    status: str
    predicted_recovery: float
    predicted_grade: float


def economic_mpc(
    state: dict[str, float], previous_action: PlantAction | None = None, horizon: int = 10
) -> MPCResult:
    previous = previous_action or PlantAction(
        state.get("air_flow", 1.3),
        state.get("pulp_level", 0.55),
        state.get("ph", 9.8),
        state.get("reagent_gpt", 35.0),
        state.get("throughput_tph", 110.0),
    )
    x0 = np.array(
        [
            previous.air_flow,
            previous.pulp_level,
            previous.ph,
            previous.reagent_gpt,
            previous.throughput_tph,
        ]
    )
    bounds = [(0.5, 2.5), (0.2, 0.9), (8.0, 11.5), (5.0, 80.0), (60.0, 180.0)]

    def objective(values: np.ndarray) -> float:
        plant = SyntheticMineralPlant(seed=11)
        plant.reset()
        for key, value in state.items():
            if hasattr(plant.state, key):
                setattr(plant.state, key, float(value))
        action = PlantAction(*map(float, values))
        trajectory = plant.run(horizon, action)
        grade_penalty = sum(max(0.18 - row["concentrate_grade"], 0) ** 2 for row in trajectory)
        recovery_value = sum(row["recovery"] for row in trajectory)
        cost = sum(row["cost_proxy"] for row in trajectory)
        move = np.sum(((values - x0) / np.array([0.5, 0.2, 0.5, 15, 25])) ** 2)
        return float(-100 * recovery_value + 1200 * grade_penalty + cost + 0.5 * move)

    result = minimize(
        objective, x0, method="SLSQP", bounds=bounds, options={"maxiter": 80, "ftol": 1e-8}
    )
    action = PlantAction(*map(float, result.x))
    validation_plant = SyntheticMineralPlant(seed=11)
    validation_plant.reset()
    for key, value in state.items():
        if hasattr(validation_plant.state, key):
            setattr(validation_plant.state, key, float(value))
    predicted = validation_plant.run(horizon, action)[-1]
    meets_grade = predicted["concentrate_grade"] >= 0.18
    status = "SAFE" if result.success and meets_grade else "REVIEW"
    return MPCResult(
        action,
        bool(result.success),
        float(result.fun),
        int(result.nit),
        status,
        predicted["recovery"],
        predicted["concentrate_grade"],
    )
