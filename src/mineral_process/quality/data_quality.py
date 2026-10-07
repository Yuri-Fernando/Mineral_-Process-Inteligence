"""Deterministic tag-quality assessment."""

from dataclasses import dataclass
from enum import Enum

import numpy as np
import pandas as pd


class QualityFlag(str, Enum):
    GOOD = "GOOD"
    SUSPECT = "SUSPECT"
    BAD = "BAD"
    MISSING = "MISSING"


@dataclass(frozen=True)
class TagRule:
    minimum: float
    maximum: float
    max_rate: float | None = None
    frozen_window: int = 10


def assess_series(series: pd.Series, rule: TagRule) -> pd.Series:
    flags = pd.Series(QualityFlag.GOOD, index=series.index, dtype="object")
    flags[series.isna()] = QualityFlag.MISSING
    flags[(series < rule.minimum) | (series > rule.maximum)] = QualityFlag.BAD
    if rule.max_rate is not None:
        flags[series.diff().abs() > rule.max_rate] = QualityFlag.SUSPECT
    frozen = series.rolling(rule.frozen_window, min_periods=rule.frozen_window).apply(
        lambda values: float(np.nanmax(values) - np.nanmin(values) == 0), raw=True
    )
    flags[frozen == 1] = QualityFlag.SUSPECT
    return flags


def overall_quality(flags: pd.DataFrame) -> QualityFlag:
    values = set(flags.astype(str).to_numpy().ravel())
    for level in (QualityFlag.BAD, QualityFlag.MISSING, QualityFlag.SUSPECT):
        if level.value in values:
            return level
    return QualityFlag.GOOD
