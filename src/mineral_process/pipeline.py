"""Reproducible top-to-bottom demonstration and report generation."""

from __future__ import annotations

import json
from dataclasses import asdict
from pathlib import Path

import pandas as pd

from mineral_process.control.mpc import economic_mpc
from mineral_process.models.soft_sensor import (
    metrics_dict,
    synthetic_flotation_data,
    train_soft_sensor,
)
from mineral_process.monitoring.drift import drift_report
from mineral_process.optimization.recommend import pareto_search, recommend_setpoints
from mineral_process.simulation.digital_twin import PlantAction, SyntheticMineralPlant
from mineral_process.simulation.sensor_faults import FaultSpec, FaultType, inject_fault


def run_end_to_end(
    output_dir: Path = Path("reports/generated"), seed: int = 42
) -> dict[str, object]:
    output_dir.mkdir(parents=True, exist_ok=True)
    synthetic = synthetic_flotation_data(seed=seed)
    model = train_soft_sensor(synthetic)
    model.save(Path("models/soft_sensor.joblib"))

    plant = SyntheticMineralPlant(seed=seed)
    nominal = pd.DataFrame(plant.run(120, PlantAction(1.45, 0.58, 10.1, 35, 110)))
    plant.inject_disturbance(hardness=22.0, feed_grade=0.010)
    disturbed = pd.DataFrame(plant.run(80, PlantAction(1.45, 0.58, 10.1, 35, 110)))
    trajectory = pd.concat(
        [nominal.assign(regime="nominal"), disturbed.assign(regime="disturbed")], ignore_index=True
    )
    trajectory.to_csv(output_dir / "digital_twin_trajectory.csv", index=False)

    signal = trajectory["air_flow"].to_numpy()
    fault = inject_fault(signal, FaultSpec(FaultType.DRIFT, start=100, severity=1.2), seed=seed)
    pd.DataFrame({"truth": signal, "observed": fault}).to_csv(
        output_dir / "sensor_fault_matrix.csv", index=False
    )

    state = plant.observe()
    recommendation = recommend_setpoints(state, seed=seed)
    pareto = pd.DataFrame(pareto_search(state, samples=180, seed=seed))
    pareto.to_csv(output_dir / "optimization_pareto.csv", index=False)
    mpc = economic_mpc(state)
    drift = drift_report(nominal["p80_um"].to_numpy(), disturbed["p80_um"].to_numpy())
    summary: dict[str, object] = {
        "schema_version": 1,
        "data_kind": "synthetic_demo",
        "soft_sensor": metrics_dict(model),
        "recommendation": recommendation.to_dict(),
        "mpc": asdict(mpc),
        "drift": asdict(drift),
        "artifacts": [
            "digital_twin_trajectory.csv",
            "sensor_fault_matrix.csv",
            "optimization_pareto.csv",
        ],
    }
    (output_dir / "run_summary.json").write_text(
        json.dumps(summary, indent=2, default=str), encoding="utf-8"
    )
    (output_dir / "model_card.md").write_text(
        "# Synthetic soft-sensor model card\n\n"
        "This validation model is trained on clearly labelled synthetic data. It proves the software path, "  # noqa: E501
        "not performance on a production plant. The industrial case-study trainer uses temporal holdout "  # noqa: E501
        "and excludes same-assay concentrate variables from online features.\n\n"
        f"Metrics: `{json.dumps(metrics_dict(model))}`\n",
        encoding="utf-8",
    )
    return summary
