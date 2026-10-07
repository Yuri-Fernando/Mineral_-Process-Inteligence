"""Reproducible pipelines for the independent public real-data case studies."""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.ensemble import HistGradientBoostingRegressor, RandomForestRegressor
from sklearn.impute import SimpleImputer
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.pipeline import Pipeline

from mineral_process.data.loaders import load_geomet, load_polymetallic
from mineral_process.geomet.spatial import spatial_block_ids


def _metrics(actual: pd.Series, predicted: np.ndarray) -> dict[str, float]:
    return {
        "mae": float(mean_absolute_error(actual, predicted)),
        "rmse": float(mean_squared_error(actual, predicted) ** 0.5),
        "r2": float(r2_score(actual, predicted)),
    }


def _chemistry_features(frame: pd.DataFrame) -> list[str]:
    return ["X", "Y", "Z", *[column for column in frame if column.endswith(" ppm")]]


def _spatial_case(
    frame: pd.DataFrame, target: str, features: list[str], seed: int
) -> tuple[pd.DataFrame, dict[str, float | int]]:
    data = frame[[*features, target]].dropna(subset=[target, "X", "Y", "Z"]).copy()
    blocks = spatial_block_ids(data["X"], data["Y"], blocks_per_axis=3)
    counts = blocks.value_counts()
    held_out = int(counts[counts >= 3].index[-1])
    train = data.loc[blocks != held_out]
    test = data.loc[blocks == held_out]
    model = RandomForestRegressor(
        n_estimators=240, min_samples_leaf=2, random_state=seed, n_jobs=-1
    )
    imputer = SimpleImputer(strategy="median")
    train_values = imputer.fit_transform(train[features])
    test_values = imputer.transform(test[features])
    model.fit(train_values, train[target])
    tree_predictions = np.vstack([tree.predict(test_values) for tree in model.estimators_])
    prediction = tree_predictions.mean(axis=0)
    output = test[["X", "Y", "Z", target]].copy()
    output["prediction"] = prediction
    output["uncertainty_std"] = tree_predictions.std(axis=0)
    metrics: dict[str, float | int] = {
        **_metrics(test[target], prediction),
        "train_rows": len(train),
        "test_rows": len(test),
        "held_out_spatial_block": held_out,
    }
    return output, metrics


def run_geomet_case(
    output_dir: Path = Path("reports/generated/geomet"), seed: int = 42
) -> dict[str, object]:
    """Model raw GeoMet responses using chemistry/coordinates and spatial holdout."""
    output_dir.mkdir(parents=True, exist_ok=True)
    tables = load_geomet()
    studies = {
        "comminution_M": (tables["comminution"], "M"),
        "comminution_A": (tables["comminution"], "A"),
        "flotation_LCT": (tables["flotation"], "LCT"),
    }
    summary: dict[str, object] = {
        "data_kind": "real_public_geomet",
        "validation": "single held-out spatial block",
        "targets": {},
        "warning": "Raw M/A names are preserved; no undocumented BWI/DWT relabeling is made.",
    }
    report_rows: list[dict[str, object]] = []
    for name, (frame, target) in studies.items():
        predictions, metrics = _spatial_case(frame, target, _chemistry_features(frame), seed)
        predictions.to_csv(output_dir / f"{name}_spatial_predictions.csv", index=False)
        summary["targets"][name] = metrics  # type: ignore[index]
        report_rows.append({"target": name, **metrics})
    report = pd.DataFrame(report_rows)
    report.to_csv(output_dir / "geomet_metrics.csv", index=False)
    (output_dir / "geometallurgy_report.html").write_text(
        "<h1>GeoMet spatial holdout report</h1>"
        "<p>Real public data. Case kept separate from all other plants. M and A retain the upstream "  # noqa: E501
        "column names because their exact interpretation is not asserted without a data dictionary.</p>"  # noqa: E501
        + report.to_html(index=False, float_format=lambda value: f"{value:.4f}"),
        encoding="utf-8",
    )
    (output_dir / "summary.json").write_text(
        json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    return summary


POLY_OPERATIONAL_FEATURES = [
    "F80(um)_Faja11",
    "P80_12x16",
    "_%+65M_O/F_D12",
    "_%-200M_O/F_D12",
    "K_80(µ)_D12",
    "_%+65M_O/F_D20",
    "_%-200M_O/F_D20",
    "K_80(µ)_D20",
    "TMS/guardia",
]

POLY_TARGETS = ["Rec_total_Ag", "Rec_Cu_ConCu", "Rec_Pb_ConPb", "Rec_Zn_ConZn"]


def _ordered_holdout_model(
    frame: pd.DataFrame, target: str, seed: int
) -> tuple[pd.DataFrame, dict[str, float | int]]:
    data = frame[[*POLY_OPERATIONAL_FEATURES, target]].dropna().copy()
    cut = int(len(data) * 0.8)
    train, test = data.iloc[:cut], data.iloc[cut:]
    model = Pipeline(
        [
            ("impute", SimpleImputer(strategy="median")),
            (
                "model",
                HistGradientBoostingRegressor(
                    max_iter=180, learning_rate=0.05, max_leaf_nodes=18, random_state=seed
                ),
            ),
        ]
    )
    model.fit(train[POLY_OPERATIONAL_FEATURES], train[target])
    predicted = model.predict(test[POLY_OPERATIONAL_FEATURES])
    result = test.copy()
    result["prediction"] = predicted
    return result, {
        **_metrics(test[target], predicted),
        "train_rows": len(train),
        "test_rows": len(test),
    }


def _observed_pareto(frame: pd.DataFrame) -> pd.DataFrame:
    """Observed non-dominated rows: maximize Ag recovery/throughput, minimize P80."""
    columns = ["Rec_total_Ag", "TMS/guardia", "P80_12x16"]
    data = frame[columns].dropna().copy()
    values = data.to_numpy()
    keep = np.ones(len(data), dtype=bool)
    for index, row in enumerate(values):
        dominates = (
            (values[:, 0] >= row[0])
            & (values[:, 1] >= row[1])
            & (values[:, 2] <= row[2])
            & ((values[:, 0] > row[0]) | (values[:, 1] > row[1]) | (values[:, 2] < row[2]))
        )
        keep[index] = not dominates.any()
    return data.loc[keep].sort_values("Rec_total_Ag")


def run_polymetallic_case(
    output_dir: Path = Path("reports/generated/polymetallic"), seed: int = 42
) -> dict[str, object]:
    """Fit leakage-restricted recovery baselines and an observed Pareto frontier."""
    output_dir.mkdir(parents=True, exist_ok=True)
    sheets = load_polymetallic()
    frame = sheets["Matriz_datos"]
    targets: dict[str, dict[str, float | int]] = {}
    rows: list[dict[str, object]] = []
    for target in POLY_TARGETS:
        predictions, metrics = _ordered_holdout_model(frame, target, seed)
        predictions.to_csv(output_dir / f"{target}_ordered_holdout.csv", index=False)
        targets[target] = metrics
        rows.append({"target": target, **metrics})
    pareto = _observed_pareto(frame)
    pareto.to_csv(output_dir / "observed_pareto.csv", index=False)
    summary: dict[str, object] = {
        "data_kind": "real_public_polymetallic",
        "observed_shape": list(frame.shape),
        "validation": "final 20 percent in source row order; timestamps are unavailable",
        "features": POLY_OPERATIONAL_FEATURES,
        "targets": targets,
        "pareto_rows": len(pareto),
        "causal_claim": False,
    }
    metrics_frame = pd.DataFrame(rows)
    metrics_frame.to_csv(output_dir / "grinding_recovery_metrics.csv", index=False)
    (output_dir / "grinding_recovery_report.html").write_text(
        "<h1>Polymetallic grinding and recovery report</h1>"
        "<p>Real observational data. The holdout follows source row order because no timestamp is "
        "available. The observed Pareto set is descriptive and is not a causal setpoint policy.</p>"
        + metrics_frame.to_html(index=False, float_format=lambda value: f"{value:.4f}"),
        encoding="utf-8",
    )
    (output_dir / "summary.json").write_text(
        json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    return summary
