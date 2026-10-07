"""Spatial block splitting and uncertainty-aware baseline modeling."""

from dataclasses import dataclass

import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score


def spatial_block_ids(x: pd.Series, y: pd.Series, blocks_per_axis: int = 4) -> pd.Series:
    if blocks_per_axis < 2:
        raise ValueError("at least two blocks per axis are required")
    x_block = pd.cut(x, bins=blocks_per_axis, labels=False, include_lowest=True)
    y_block = pd.cut(y, bins=blocks_per_axis, labels=False, include_lowest=True)
    return (x_block * blocks_per_axis + y_block).astype("Int64")


@dataclass(frozen=True)
class SpatialMetrics:
    mae: float
    rmse: float
    r2: float
    train_rows: int
    test_rows: int


def spatial_holdout_model(
    frame: pd.DataFrame, target: str, x_column: str, y_column: str, seed: int = 42
) -> tuple[pd.DataFrame, SpatialMetrics]:
    numeric = (
        frame.select_dtypes(include=np.number).dropna(subset=[target, x_column, y_column]).copy()
    )
    features = [c for c in numeric.columns if c != target]
    numeric = numeric.dropna(subset=features)
    blocks = spatial_block_ids(numeric[x_column], numeric[y_column])
    held_out = int(blocks.dropna().max())
    train = numeric[blocks != held_out]
    test = numeric[blocks == held_out]
    if len(test) < 2 or len(train) < 10:
        raise ValueError("insufficient rows for spatial holdout")
    model = RandomForestRegressor(
        n_estimators=160, min_samples_leaf=3, random_state=seed, n_jobs=-1
    )
    model.fit(train[features], train[target])
    tree_predictions = np.vstack([tree.predict(test[features]) for tree in model.estimators_])
    prediction = tree_predictions.mean(axis=0)
    output = test[[x_column, y_column, target]].copy()
    output["prediction"] = prediction
    output["uncertainty_std"] = tree_predictions.std(axis=0)
    metrics = SpatialMetrics(
        float(mean_absolute_error(test[target], prediction)),
        float(mean_squared_error(test[target], prediction) ** 0.5),
        float(r2_score(test[target], prediction)),
        len(train),
        len(test),
    )
    return output, metrics
