import pandas as pd

from mineral_process.models.soft_sensor import (
    prepare_temporal_soft_sensor_frame,
    synthetic_flotation_data,
)


def test_temporal_soft_sensor_features_are_past_only() -> None:
    frame = synthetic_flotation_data(rows=240, seed=5)
    original, target = prepare_temporal_soft_sensor_frame(frame)
    changed = frame.copy()
    changed.loc[changed.index >= 180, "Ore Pulp pH"] = 99.0
    mutated, _ = prepare_temporal_soft_sensor_frame(changed)
    pd.testing.assert_frame_equal(original.iloc[:180], mutated.iloc[:180])
    assert target == "% Silica Concentrate"
    assert "% Iron Concentrate" not in original.columns
