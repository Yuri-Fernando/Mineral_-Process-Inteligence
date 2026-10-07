"""Advisory-only API for simulation and optimization."""

from dataclasses import asdict
from functools import lru_cache
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from fastapi import FastAPI
from pydantic import BaseModel, Field

from mineral_process import __version__
from mineral_process.control.mpc import economic_mpc
from mineral_process.models.soft_sensor import (
    SoftSensorBundle,
    synthetic_flotation_data,
    train_soft_sensor,
)
from mineral_process.monitoring.drift import drift_report
from mineral_process.optimization.recommend import recommend_setpoints
from mineral_process.simulation.digital_twin import PlantAction, SyntheticMineralPlant
from mineral_process.simulation.sensor_faults import FaultSpec, FaultType, inject_fault


class ActionRequest(BaseModel):
    air_flow: float = Field(ge=0.5, le=2.5)
    pulp_level: float = Field(ge=0.2, le=0.9)
    ph: float = Field(ge=8.0, le=11.5)
    reagent_gpt: float = Field(ge=5.0, le=80.0)
    throughput_tph: float = Field(ge=60.0, le=180.0)


class StateRequest(BaseModel):
    state: dict[str, float]
    data_quality: str = "GOOD"
    uncertainty: float = Field(default=0.0, ge=0.0)


class SoftSensorRequest(BaseModel):
    values: dict[str, float]


class DriftRequest(BaseModel):
    reference: list[float]
    current: list[float]


class FaultRequest(BaseModel):
    values: list[float]
    kind: FaultType
    start: int = Field(ge=0)
    severity: float = 0.1
    duration: int | None = Field(default=None, ge=1)
    seed: int = 42


@lru_cache(maxsize=1)
def _soft_sensor() -> SoftSensorBundle:
    path = Path("models/soft_sensor.joblib")
    if path.exists():
        return joblib.load(path)
    return train_soft_sensor(synthetic_flotation_data())


app = FastAPI(title="Mineral Process Intelligence", version=__version__)
plant = SyntheticMineralPlant(seed=42)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "version": __version__, "mode": "advisory-only"}


@app.get("/model/info")
def model_info() -> dict[str, str]:
    return {
        "version": __version__,
        "digital_twin": "synthetic-educational",
        "control": "advisory-only",
    }


@app.get("/simulation/state")
def simulation_state() -> dict[str, float]:
    return plant.observe()


@app.post("/simulation/step")
def simulation_step(request: ActionRequest) -> dict[str, float]:
    return plant.step(PlantAction(**request.model_dump()))


@app.post("/soft-sensor/predict")
def soft_sensor_predict(request: SoftSensorRequest) -> dict[str, object]:
    bundle = _soft_sensor()
    prediction = bundle.predict(pd.DataFrame([request.values])).iloc[0]
    return {
        "silica_prediction": float(prediction["prediction"]),
        "prediction_interval": [float(prediction["lower"]), float(prediction["upper"])],
        "data_quality": "GOOD",
        "model_version": bundle.version,
    }


@app.post("/process/state")
def process_state(request: StateRequest) -> dict[str, object]:
    critical = ("feed_grade", "feed_hardness", "throughput_tph")
    missing = [key for key in critical if key not in request.state]
    return {
        "state": request.state,
        "data_quality": request.data_quality,
        "missing_critical": missing,
        "safety_status": "REJECT" if missing else "REVIEW",
    }


@app.post("/fault/inject")
def fault_inject(request: FaultRequest) -> dict[str, object]:
    observed = inject_fault(
        np.asarray(request.values),
        FaultSpec(request.kind, request.start, request.severity, request.duration),
        request.seed,
    )
    return {"kind": request.kind, "observed": observed.tolist(), "synthetic_fault": True}


@app.post("/monitoring/drift")
def monitoring_drift(request: DriftRequest) -> dict[str, object]:
    return asdict(drift_report(np.asarray(request.reference), np.asarray(request.current)))


@app.post("/optimize")
def optimize(request: StateRequest) -> dict[str, object]:
    return recommend_setpoints(request.state, request.data_quality, request.uncertainty).to_dict()


@app.post("/mpc/recommend")
def mpc_recommend(request: StateRequest) -> dict[str, object]:
    if request.data_quality not in {"GOOD", "SUSPECT"} or request.uncertainty > 0.2:
        return {"safety_status": "REJECT", "action": None, "reason": "quality or uncertainty gate"}
    result = economic_mpc(request.state)
    return {**asdict(result), "action": asdict(result.action), "advisory_only": True}
