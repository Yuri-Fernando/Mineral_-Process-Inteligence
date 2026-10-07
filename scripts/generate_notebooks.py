"""Populate skill-scaffolded notebooks with production-API tutorials."""

from pathlib import Path

import nbformat

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "output" / "jupyter-notebook"


def markdown(text: str):
    return nbformat.v4.new_markdown_cell(text.strip())


def code(text: str):
    return nbformat.v4.new_code_cell(text.strip())


def write(name: str, cells: list) -> None:
    path = OUT / name
    notebook = nbformat.read(path, as_version=4)
    notebook.cells = cells
    notebook.metadata.kernelspec = {
        "display_name": "Python 3.12",
        "language": "python",
        "name": "python3",
    }
    notebook.metadata.language_info = {"name": "python", "version": "3.12"}
    nbformat.write(notebook, path)


setup = code(
    """
from pathlib import Path
import sys

ROOT = next(
    path
    for path in (Path.cwd(), *Path.cwd().parents)
    if (path / "src" / "mineral_process").exists()
)
sys.path.insert(0, str(ROOT / "src"))
"""
)

write(
    "01-domain-digital-twin.ipynb",
    [
        markdown(
            """
# Mineral Processing Domain and Digital Twin

**Audience:** data scientists and engineers learning mineral-processing analytics.
**Prerequisites:** basic Python, mass balance and process-data concepts.
**Goals:** verify metallurgical conservation, calculate Bond energy, run the synthetic plant and
stress a sensor without duplicating production logic.

Outline: (1) setup, (2) balance, (3) comminution, (4) dynamic plant, (5) sensor fault, (6) exercise.
"""
        ),
        setup,
        markdown("## 1. Two-product mass and metal balance"),
        code(
            """
from mineral_process.domain.mass_balance import solve_two_product

balance = solve_two_product(feed_mass=100, feed_grade=0.02, concentrate_grade=0.25, tailings_grade=0.004)
balance
"""  # noqa: E501
        ),
        markdown(
            "Both residuals must be numerically zero; recovery is a metal recovery, not mass pull."
        ),
        code("balance.mass_residual, balance.metal_residual, balance.metallurgical_recovery"),
        markdown("## 2. Bond comminution response"),
        code(
            """
from mineral_process.domain.comminution import BondMillModel

mill = BondMillModel(work_index_kwh_t=16)
{p80: mill.specific_energy(f80_um=2500, p80_um=p80) for p80 in (250, 180, 120)}
"""
        ),
        markdown(
            "Finer product requires more specific energy within this compact Bond-model domain."
        ),
        markdown("## 3. Dynamic synthetic plant and a feed disturbance"),
        code(
            """
import pandas as pd
from mineral_process.simulation.digital_twin import PlantAction, SyntheticMineralPlant

plant = SyntheticMineralPlant(seed=42)
action = PlantAction(air_flow=1.45, pulp_level=0.58, ph=10.1, reagent_gpt=35, throughput_tph=110)
nominal = plant.run(60, action)
plant.inject_disturbance(hardness=23, feed_grade=0.010)
trajectory = pd.DataFrame(nominal + plant.run(60, action))
trajectory[["recovery", "concentrate_grade", "p80_um", "specific_energy_kwh_t"]].tail()
"""
        ),
        code(
            """
trajectory[["recovery", "concentrate_grade", "p80_um"]].plot(
    subplots=True, figsize=(10, 7), title="Synthetic response; disturbance at sample 60"
)
"""
        ),
        markdown("## 4. Reproducible sensor degradation"),
        code(
            """
from mineral_process.simulation.sensor_faults import FaultSpec, FaultType, inject_fault

signal = trajectory["air_flow"].to_numpy()
trajectory["air_flow_faulty"] = inject_fault(signal, FaultSpec(FaultType.DRIFT, 55, 1.0), seed=42)
trajectory[["air_flow", "air_flow_faulty"]].plot(figsize=(10, 3), title="Injected sensor drift")
"""
        ),
        markdown(
            """
## Exercise

Increase throughput to 145 t/h after the disturbance. Compare P80, recovery and specific energy.
Why is a throughput change not a free improvement?
"""
        ),
        code(
            """
# Answer scaffold
exercise_plant = SyntheticMineralPlant(seed=42)
exercise_plant.inject_disturbance(hardness=23)
high_throughput = PlantAction(1.45, 0.58, 10.1, 35, 145)
answer = pd.DataFrame(exercise_plant.run(60, high_throughput))
answer[["throughput_tph", "p80_um", "recovery", "specific_energy_kwh_t"]].tail(1)
"""
        ),
        markdown(
            """
## Pitfall and extension

**Pitfall:** treating normalized air flow or a simulator-safe bound as a real setpoint. Units and
calibration are plant-specific. **Extension:** calibrate kinetics using a documented laboratory
campaign and propagate parameter uncertainty.
"""
        ),
    ],
)

write(
    "02-public-data-case-studies.ipynb",
    [
        markdown(
            """
# Public Data Case Studies

**Audience:** practitioners auditing public mining datasets.
**Goals:** keep the three case studies independent, inspect local availability, train a temporally
valid soft-sensor baseline, and understand the GeoMet spatial holdout contract.

Run `python -m mineral_process.cli download-data` before this notebook to use the real files.
"""
        ),
        setup,
        markdown("## 1. Inventory: never concatenate these plants"),
        code(
            """
from pathlib import Path

cases = {
    "GeoMet": ROOT / "data/raw/geomet",
    "Iron flotation": ROOT / "data/raw/iron_flotation",
    "Polymetallic": ROOT / "data/raw/polymetallic",
}
{name: [p.name for p in path.glob("*") if p.name != ".gitkeep"] for name, path in cases.items()}
"""
        ),
        markdown("## 2. Temporal soft sensor with a deterministic fallback"),
        code(
            """
from mineral_process.data.loaders import load_iron_flotation
from mineral_process.models.soft_sensor import (
    prepare_temporal_soft_sensor_frame,
    synthetic_flotation_data,
    train_soft_sensor,
)

try:
    # A chronological prefix keeps this tutorial interactive on synced drives.
    # Use nrows=None in production training to load the complete dataset.
    flotation = load_iron_flotation(ROOT / "data/raw/iron_flotation", nrows=120_000)
    data_origin = "real public Kaggle case study"
except FileNotFoundError:
    flotation = synthetic_flotation_data(rows=2400, seed=42)
    data_origin = "synthetic fallback"
data_origin, flotation.shape
"""
        ),
        code(
            """
baseline_bundle = train_soft_sensor(flotation)
temporal_frame, target = prepare_temporal_soft_sensor_frame(flotation)
bundle = train_soft_sensor(temporal_frame, target)
{"baseline": baseline_bundle.metrics, "causal_temporal": bundle.metrics}
"""
        ),
        markdown(
            "The feature list must not contain `% Iron Concentrate`: it generally comes from the same delayed lab assay as the target."  # noqa: E501
        ),
        code(
            """
assert all("iron concentrate" not in feature.lower() for feature in bundle.features)
bundle.predict(temporal_frame.tail(5))
"""
        ),
        markdown("## 3. GeoMet spatial-block contract"),
        code(
            """
import pandas as pd
from mineral_process.geomet.spatial import spatial_block_ids

grid = pd.DataFrame({"x": range(16), "y": [v % 4 for v in range(16)]})
grid["block"] = spatial_block_ids(grid.x, grid.y, blocks_per_axis=4)
grid
"""
        ),
        markdown(
            """
## Exercise

Inspect `bundle.metrics`. Compare it with a mean-only baseline on the final 15% of rows. Do not
shuffle the observations. The answer scaffold deliberately leaves the final calculation to you.
"""
        ),
        code(
            """
# Answer scaffold
target = bundle.target
cut = int(len(flotation) * 0.85)
training_mean = flotation.iloc[:cut][target].mean()
holdout = flotation.iloc[cut:][target].dropna()
baseline_mae = (holdout - training_mean).abs().mean()
{"baseline_mae": baseline_mae, "model_mae": bundle.metrics.mae}
"""
        ),
        markdown(
            """
## Pitfall and extension

**Pitfall:** a random split overstates industrial performance because adjacent timestamps or spatial
neighbors leak regimes. **Extension:** implement rolling-origin evaluation and compare metric
dispersion across time windows or spatial blocks.
"""
        ),
    ],
)

write(
    "03-optimization-mpc.ipynb",
    [
        markdown(
            """
# Optimization and Economic MPC

**Audience:** engineers/data scientists familiar with numerical optimization.
**Goals:** generate advisory setpoints, inspect a recovery-grade-cost Pareto front and compare an
economic MPC move under explicit bounds.
"""
        ),
        setup,
        markdown("## 1. Establish a synthetic operating state"),
        code(
            """
from mineral_process.simulation.digital_twin import SyntheticMineralPlant

plant = SyntheticMineralPlant(seed=42)
plant.run(30)
state = plant.observe()
{key: state[key] for key in ("recovery", "concentrate_grade", "p80_um", "throughput_tph")}
"""
        ),
        markdown("## 2. Fail-closed constrained recommendation"),
        code(
            """
from mineral_process.optimization.recommend import recommend_setpoints

recommendation = recommend_setpoints(state, data_quality="GOOD", uncertainty=0.05, seed=42)
recommendation.to_dict()
"""
        ),
        code(
            """
rejected = recommend_setpoints(state, data_quality="BAD", uncertainty=0.05)
assert rejected.action is None and rejected.safety_status == "REJECT"
rejected.to_dict()
"""
        ),
        markdown("## 3. Gaussian-Process Bayesian optimization and NSGA-II"),
        code(
            """
import pandas as pd

from mineral_process.optimization.bayesian import bayesian_optimize
from mineral_process.optimization.nsga2 import nsga2_optimize

bayesian = bayesian_optimize(state, iterations=8, initial_points=5, seed=42)
nsga2 = nsga2_optimize(state, population_size=24, generations=6, seed=42)
pareto = pd.DataFrame(
    nsga2.objectives,
    columns=["negative_recovery_penalized", "negative_grade_penalized", "cost"],
)
pareto.plot.scatter(
    x="cost",
    y="negative_recovery_penalized",
    c="negative_grade_penalized",
    colormap="viridis",
    figsize=(8, 5),
)
"""
        ),
        code("bayesian"),
        markdown("## 4. Economic MPC prototype"),
        code(
            """
from dataclasses import asdict
from mineral_process.control.mpc import economic_mpc

mpc = economic_mpc(state, horizon=8)
asdict(mpc)
"""
        ),
        markdown(
            """
## Exercise

Inject a harder-ore disturbance and compare the recommended throughput before and after it. Explain
why controller output must still go through an operator/process-safety review.
"""
        ),
        code(
            """
# Answer scaffold
plant.inject_disturbance(hardness=25)
hard_state = plant.observe()
before = recommend_setpoints(state, seed=7)
after = recommend_setpoints(hard_state, seed=7)
{"before": before.to_dict(), "after": after.to_dict()}
"""
        ),
        markdown(
            """
## Pitfall and extension

**Pitfall:** interpreting `SAFE` as plant safety approval; here it only means simulator constraints
were satisfied. **Extension:** compare fixed setpoints, a PID rule and MPC over the same seeded
disturbance schedule, then report recovery, grade violations and control effort.
"""
        ),
    ],
)

print(f"Populated notebooks in {OUT}")
