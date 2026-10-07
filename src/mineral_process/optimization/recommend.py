"""Constrained advisory setpoint optimization against the digital twin."""

from dataclasses import asdict, dataclass

import numpy as np
from scipy.optimize import differential_evolution

from mineral_process.simulation.digital_twin import PlantAction, SyntheticMineralPlant


@dataclass(frozen=True)
class Recommendation:
    action: PlantAction | None
    expected_recovery: float | None
    expected_grade: float | None
    objective: float | None
    safety_status: str
    reason: str

    def to_dict(self) -> dict[str, object]:
        payload = asdict(self)
        payload["action"] = None if self.action is None else asdict(self.action)
        return payload


def _evaluate(
    values: np.ndarray, state: dict[str, float], horizon: int = 12
) -> tuple[float, dict[str, float]]:
    plant = SyntheticMineralPlant(seed=7)
    plant.reset()
    for key, value in state.items():
        if hasattr(plant.state, key):
            setattr(plant.state, key, float(value))
    action = PlantAction(*map(float, values))
    final = plant.run(horizon, action)[-1]
    grade_violation = max(0.18 - final["concentrate_grade"], 0.0)
    economic_objective = (
        -150.0 * final["recovery"]
        + 1200.0 * grade_violation**2
        + 0.8 * final["cost_proxy"]
        + 0.003 * action.reagent_gpt
    )
    return economic_objective, final


def recommend_setpoints(
    state: dict[str, float], data_quality: str = "GOOD", uncertainty: float = 0.0, seed: int = 42
) -> Recommendation:
    critical = ("feed_grade", "feed_hardness", "throughput_tph")
    if any(key not in state or not np.isfinite(state[key]) for key in critical):
        return Recommendation(None, None, None, None, "REJECT", "missing critical state")
    if data_quality not in {"GOOD", "SUSPECT"}:
        return Recommendation(None, None, None, None, "REJECT", "critical data quality")
    if uncertainty > 0.20:
        return Recommendation(None, None, None, None, "REJECT", "uncertainty above limit")
    bounds = [(0.5, 2.5), (0.2, 0.9), (8.0, 11.5), (5.0, 80.0), (60.0, 180.0)]
    result = differential_evolution(
        lambda values: _evaluate(values, state)[0],
        bounds=bounds,
        seed=seed,
        popsize=6,
        maxiter=18,
        polish=True,
    )
    action = PlantAction(*map(float, result.x))
    objective, final = _evaluate(result.x, state)
    status = "SAFE" if result.success and final["concentrate_grade"] >= 0.18 else "REVIEW"
    return Recommendation(
        action, final["recovery"], final["concentrate_grade"], objective, status, result.message
    )


def pareto_search(
    state: dict[str, float], samples: int = 300, seed: int = 42
) -> list[dict[str, float]]:
    rng = np.random.default_rng(seed)
    candidates: list[dict[str, float]] = []
    for _ in range(samples):
        values = np.array(
            [
                rng.uniform(0.5, 2.5),
                rng.uniform(0.2, 0.9),
                rng.uniform(8, 11.5),
                rng.uniform(5, 80),
                rng.uniform(60, 180),
            ]
        )
        _, final = _evaluate(values, state, horizon=8)
        candidates.append(
            {
                "air_flow": values[0],
                "pulp_level": values[1],
                "ph": values[2],
                "reagent_gpt": values[3],
                "throughput_tph": values[4],
                "recovery": final["recovery"],
                "grade": final["concentrate_grade"],
                "cost": final["cost_proxy"],
            }
        )
    front: list[dict[str, float]] = []
    for candidate in candidates:
        dominated = any(
            other["recovery"] >= candidate["recovery"]
            and other["grade"] >= candidate["grade"]
            and other["cost"] <= candidate["cost"]
            and other is not candidate
            for other in candidates
        )
        if not dominated:
            front.append(candidate)
    return sorted(front, key=lambda row: row["recovery"])
