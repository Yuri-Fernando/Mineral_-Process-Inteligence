"""Leakage-resistant time-series transforms."""

from collections.abc import Iterable

import numpy as np
import pandas as pd


def normalize_time_index(frame: pd.DataFrame, timestamp: str) -> pd.DataFrame:
    result = frame.copy()
    result[timestamp] = pd.to_datetime(result[timestamp], errors="raise", utc=True)
    return (
        result.sort_values(timestamp).drop_duplicates(timestamp, keep="last").set_index(timestamp)
    )


def causal_resample(frame: pd.DataFrame, frequency: str = "1min") -> pd.DataFrame:
    if not isinstance(frame.index, pd.DatetimeIndex):
        raise TypeError("frame must use a DatetimeIndex")
    return frame.resample(frequency, label="right", closed="right").mean().ffill()


def add_causal_features(
    frame: pd.DataFrame,
    columns: Iterable[str],
    lags: tuple[int, ...] = (1, 5, 15, 30, 60),
    windows: tuple[int, ...] = (5, 15, 60),
) -> pd.DataFrame:
    """Create only past-looking features; current value is never in a rolling statistic."""
    derived: dict[str, pd.Series] = {}
    for column in columns:
        history = frame[column].shift(1)
        for lag in lags:
            derived[f"{column}__lag_{lag}"] = frame[column].shift(lag)
        for window in windows:
            rolling = history.rolling(window=window, min_periods=max(1, window // 3))
            derived[f"{column}__mean_{window}"] = rolling.mean()
            derived[f"{column}__std_{window}"] = rolling.std()
        derived[f"{column}__roc"] = history.diff()
        derived[f"{column}__ewm"] = history.ewm(span=10, adjust=False).mean()
    feature_frame = pd.DataFrame(derived, index=frame.index)
    return pd.concat([frame, feature_frame], axis=1).replace([np.inf, -np.inf], np.nan)


def temporal_split(
    frame: pd.DataFrame, train_fraction: float = 0.7, validation_fraction: float = 0.15
):
    if not 0 < train_fraction < 1 or not 0 <= validation_fraction < 1:
        raise ValueError("invalid split fractions")
    if train_fraction + validation_fraction >= 1:
        raise ValueError("train + validation must leave a test interval")
    n_rows = len(frame)
    train_end = int(n_rows * train_fraction)
    validation_end = int(n_rows * (train_fraction + validation_fraction))
    return frame.iloc[:train_end], frame.iloc[train_end:validation_end], frame.iloc[validation_end:]
