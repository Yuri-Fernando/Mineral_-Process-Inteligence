"""Artifact-producing orchestration for Bayesian optimization and NSGA-II."""

from __future__ import annotations

import json
from dataclasses import asdict
from pathlib import Path

import pandas as pd

from mineral_process.optimization.bayesian import bayesian_optimize
from mineral_process.optimization.nsga2 import nsga2_optimize
from mineral_process.simulation.digital_twin import SyntheticMineralPlant


def run_advanced_optimization(
    output_dir: Path = Path("reports/generated/advanced_optimization"), seed: int = 42
) -> dict[str, object]:
    output_dir.mkdir(parents=True, exist_ok=True)
    state = SyntheticMineralPlant(seed).observe()
    bayesian = bayesian_optimize(state, seed=seed)
    nsga2 = nsga2_optimize(state, seed=seed)
    decision_names = ["air_flow", "pulp_level", "ph", "reagent_gpt", "throughput_tph"]
    rows = []
    for decisions, objectives in zip(nsga2.decisions, nsga2.objectives, strict=True):
        rows.append(
            {
                **dict(zip(decision_names, decisions, strict=True)),
                "neg_recovery_penalized": objectives[0],
                "neg_grade_penalized": objectives[1],
                "cost_proxy": objectives[2],
            }
        )
    pd.DataFrame(rows).to_csv(output_dir / "nsga2_pareto.csv", index=False)
    summary: dict[str, object] = {
        "data_kind": "synthetic_digital_twin",
        "bayesian": asdict(bayesian),
        "nsga2_pareto_solutions": len(rows),
        "advisory_only": True,
    }
    (output_dir / "summary.json").write_text(
        json.dumps(summary, indent=2, default=str), encoding="utf-8"
    )
    return summary
