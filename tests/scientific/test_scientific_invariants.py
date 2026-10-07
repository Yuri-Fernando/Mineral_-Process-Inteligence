import numpy as np
import pandas as pd

from mineral_process.control.mpc import economic_mpc
from mineral_process.features.temporal import add_causal_features, temporal_split
from mineral_process.optimization.recommend import recommend_setpoints
from mineral_process.simulation.digital_twin import PlantAction, SyntheticMineralPlant
from mineral_process.simulation.sensor_faults import FaultSpec, FaultType, inject_fault


def test_causal_features_do_not_change_when_future_changes() -> None:
    base = pd.DataFrame({"x": np.arange(100, dtype=float)})
    changed = base.copy()
    changed.loc[80:, "x"] = 1e9
    left = add_causal_features(base, ["x"])
    right = add_causal_features(changed, ["x"])
    pd.testing.assert_frame_equal(left.iloc[:80], right.iloc[:80])


def test_temporal_split_preserves_order() -> None:
    frame = pd.DataFrame({"time": range(100)})
    train, validation, test = temporal_split(frame)
    assert train.time.max() < validation.time.min() < test.time.min()


def test_simulation_is_deterministic_and_physical() -> None:
    action = PlantAction(1.4, 0.55, 10, 35, 110)
    first = SyntheticMineralPlant(9).run(20, action)
    second = SyntheticMineralPlant(9).run(20, action)
    assert first == second
    assert all(0 <= row["recovery"] <= 1 for row in first)
    assert all(
        row["tailings_grade"] <= row["feed_grade"] <= row["concentrate_grade"] for row in first
    )


def test_fault_injection_is_reproducible() -> None:
    signal = np.linspace(0, 1, 100)
    spec = FaultSpec(FaultType.NOISE, 20, severity=0.5)
    np.testing.assert_array_equal(inject_fault(signal, spec, 7), inject_fault(signal, spec, 7))


def test_recommendation_and_mpc_stay_in_bounds() -> None:
    plant = SyntheticMineralPlant()
    recommendation = recommend_setpoints(plant.observe(), seed=2)
    assert recommendation.action is not None
    assert 0.5 <= recommendation.action.air_flow <= 2.5
    result = economic_mpc(plant.observe(), horizon=3)
    assert 5 <= result.action.reagent_gpt <= 80


def test_safe_optimizer_fails_closed() -> None:
    recommendation = recommend_setpoints({"feed_grade": 0.02}, data_quality="BAD")
    assert recommendation.action is None
    assert recommendation.safety_status == "REJECT"
