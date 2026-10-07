"""Temporal soft-sensor training with a leakage-aware feature contract."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import HistGradientBoostingRegressor
from sklearn.impute import SimpleImputer
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

from mineral_process.features.temporal import add_causal_features, temporal_split

LAB_COLUMNS = {"% iron concentrate", "% silica concentrate"}


def canonical_name(name: str) -> str:
    return " ".join(str(name).strip().lower().replace("_", " ").split())


@dataclass(frozen=True)
class ModelMetrics:
    mae: float
    rmse: float
    r2: float
    rows_train: int
    rows_test: int


@dataclass
class SoftSensorBundle:
    pipeline: Pipeline
    features: list[str]
    target: str
    metrics: ModelMetrics
    residual_std: float
    version: str = "soft-sensor-v0.1.0"

    def predict(self, frame: pd.DataFrame) -> pd.DataFrame:
        missing = sorted(set(self.features) - set(frame.columns))
        if missing:
            raise ValueError(f"missing model features: {missing}")
        prediction = self.pipeline.predict(frame[self.features])
        width = 1.96 * self.residual_std
        return pd.DataFrame(
            {
                "prediction": prediction,
                "lower": prediction - width,
                "upper": prediction + width,
                "model_version": self.version,
            },
            index=frame.index,
        )

    def save(self, path: Path = Path("models/soft_sensor.joblib")) -> Path:
        path.parent.mkdir(parents=True, exist_ok=True)
        joblib.dump(self, path)
        return path


def select_online_features(frame: pd.DataFrame, target: str) -> list[str]:
    excluded = LAB_COLUMNS | {canonical_name(target), "date", "timestamp"}
    return [
        column
        for column in frame.select_dtypes(include=np.number).columns
        if canonical_name(column) not in excluded
    ]


def prepare_temporal_soft_sensor_frame(
    frame: pd.DataFrame,
    target: str | None = None,
    timestamp: str | None = None,
) -> tuple[pd.DataFrame, str]:
    """Aggregate duplicate timestamps and create past-only features from online tags."""
    target = target or next(
        (column for column in frame if canonical_name(column) == "% silica concentrate"), None
    )
    timestamp = timestamp or next(
        (column for column in frame if canonical_name(column) in {"date", "timestamp"}), None
    )
    if target is None or timestamp is None:
        raise ValueError("target and timestamp columns are required")
    working = frame.copy()
    working[timestamp] = pd.to_datetime(working[timestamp], errors="raise", utc=True)
    numeric = working.select_dtypes(include=np.number).columns.tolist()
    aggregated = working.groupby(timestamp, sort=True)[numeric].mean()
    online = select_online_features(aggregated, target)
    featured = add_causal_features(
        aggregated,
        online,
        lags=(1, 5, 15, 60),
        windows=(5, 15, 60),
    )
    temporal_columns = [column for column in featured if "__" in column]
    return featured[[*temporal_columns, target]].dropna(subset=[target]), target


def train_soft_sensor(frame: pd.DataFrame, target: str | None = None) -> SoftSensorBundle:
    target = target or next(
        (column for column in frame.columns if canonical_name(column) == "% silica concentrate"),
        None,
    )
    if target is None:
        raise ValueError("silica target was not found")
    features = select_online_features(frame, target)
    if not features:
        raise ValueError("no online numeric features were found")
    clean = frame.loc[frame[target].notna(), features + [target]].copy()
    train, _, test = temporal_split(clean)
    transformer = ColumnTransformer(
        [
            (
                "numeric",
                Pipeline(
                    [("impute", SimpleImputer(strategy="median")), ("scale", StandardScaler())]
                ),
                features,
            )
        ]
    )
    pipeline = Pipeline(
        [
            ("prepare", transformer),
            (
                "model",
                HistGradientBoostingRegressor(
                    max_iter=180, learning_rate=0.06, max_leaf_nodes=25, random_state=42
                ),
            ),
        ]
    )
    pipeline.fit(train[features], train[target])
    predicted = pipeline.predict(test[features])
    residuals = test[target].to_numpy() - predicted
    metrics = ModelMetrics(
        mae=float(mean_absolute_error(test[target], predicted)),
        rmse=float(mean_squared_error(test[target], predicted) ** 0.5),
        r2=float(r2_score(test[target], predicted)),
        rows_train=len(train),
        rows_test=len(test),
    )
    return SoftSensorBundle(pipeline, features, target, metrics, float(np.std(residuals, ddof=1)))


def synthetic_flotation_data(rows: int = 2400, seed: int = 42) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    time = pd.date_range("2025-01-01", periods=rows, freq="min", tz="UTC")
    base = np.sin(np.arange(rows) / 180)
    frame = pd.DataFrame(
        {
            "Date": time,
            "% Iron Feed": 55 + 2 * base + rng.normal(0, 0.4, rows),
            "% Silica Feed": 12 - 1.5 * base + rng.normal(0, 0.3, rows),
            "Starch Flow": 3000 + 180 * base + rng.normal(0, 70, rows),
            "Amina Flow": 500 + rng.normal(0, 25, rows),
            "Ore Pulp Flow": 400 + rng.normal(0, 8, rows),
            "Ore Pulp pH": 10.0 + 0.25 * base + rng.normal(0, 0.05, rows),
            "Ore Pulp Density": 1.70 + rng.normal(0, 0.015, rows),
            "Flotation Column 01 Air Flow": 250 + rng.normal(0, 5, rows),
            "Flotation Column 01 Level": 450 + rng.normal(0, 10, rows),
        }
    )
    frame["% Silica Concentrate"] = (
        2.2
        + 0.20 * (frame["% Silica Feed"] - 12)
        - 0.18 * (frame["Ore Pulp pH"] - 10)
        - 0.00010 * (frame["Starch Flow"] - 3000)
        + 0.0012 * (frame["Amina Flow"] - 500)
        + rng.normal(0, 0.10, rows)
    )
    frame["% Iron Concentrate"] = (
        66.5 - 0.45 * frame["% Silica Concentrate"] + rng.normal(0, 0.05, rows)
    )
    return frame


def metrics_dict(bundle: SoftSensorBundle) -> dict[str, float | int]:
    return asdict(bundle.metrics)
