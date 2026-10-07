"""Populate the real-data case-study tutorial scaffold."""

from pathlib import Path

import nbformat

root = Path(__file__).resolve().parents[1]
path = root / "output/jupyter-notebook/04-real-geomet-polymetallic.ipynb"
notebook = nbformat.read(path, as_version=4)


def markdown(source: str):
    return nbformat.v4.new_markdown_cell(source.strip())


def code(source: str):
    return nbformat.v4.new_code_cell(source.strip())


notebook.cells = [
    markdown(
        """
# Real GeoMet and Polymetallic Reports

**Audience:** practitioners who need reproducible, leakage-aware mining case studies.
**Prerequisite:** run `python -m mineral_process.cli download-data`.
**Goals:** execute the spatial GeoMet models, execute ordered-holdout recovery baselines and inspect
an observed multiobjective frontier while keeping the two operations strictly separate.
"""
    ),
    code(
        """
import sys
from pathlib import Path

ROOT = next(
    path
    for path in (Path.cwd(), *Path.cwd().parents)
    if (path / "src" / "mineral_process").exists()
)
sys.path.insert(0, str(ROOT / "src"))
"""
    ),
    markdown("## 1. Verify provenance before modeling"),
    code(
        """
import json

manifest = json.loads((ROOT / "data/raw/provenance.json").read_text(encoding="utf-8"))
[(item["dataset"], item["size_bytes"], item["sha256"][:12]) for item in manifest["files"]]
"""
    ),
    markdown("## 2. GeoMet: chemistry and coordinates with a held-out spatial block"),
    code(
        """
import pandas as pd

from mineral_process.case_studies import run_geomet_case

geomet_summary = run_geomet_case(ROOT / "reports/generated/geomet", seed=42)
pd.DataFrame(geomet_summary["targets"]).T
"""
    ),
    markdown(
        "The upstream column names `M` and `A` are intentionally preserved. The project does not "
        "claim they are BWI/DWT fields without an authoritative dictionary."
    ),
    markdown("## 3. Polymetallic grinding: operational-only features and ordered holdout"),
    code(
        """
from mineral_process.case_studies import run_polymetallic_case

poly_summary = run_polymetallic_case(ROOT / "reports/generated/polymetallic", seed=42)
pd.DataFrame(poly_summary["targets"]).T
"""
    ),
    code(
        """
pareto = pd.read_csv(ROOT / "reports/generated/polymetallic/observed_pareto.csv")
pareto.plot.scatter(
    x="P80_12x16",
    y="Rec_total_Ag",
    c="TMS/guardia",
    colormap="viridis",
    figsize=(8, 5),
    title="Observed non-dominated rows (descriptive, not causal)",
)
"""
    ),
    markdown(
        """
## Exercise

Compare each model's RMSE with the target standard deviation. Which target is most useful despite a
negative R²? Explain why a random split would not repair a regime-shift problem.
"""
    ),
    code(
        """
# Answer scaffold: join metrics to raw target dispersion.
from mineral_process.data.loaders import load_polymetallic

raw = load_polymetallic(ROOT / "data/raw/polymetallic")["Matriz_datos"]
comparison = pd.DataFrame(poly_summary["targets"]).T
comparison["target_std"] = [raw.loc[:, target].std() for target in comparison.index]
comparison["rmse_over_std"] = comparison["rmse"] / comparison["target_std"]
comparison[["rmse", "target_std", "rmse_over_std", "r2"]]
"""
    ),
    markdown(
        """
## Pitfall and extension

**Pitfall:** interpreting the observed Pareto rows as recommended interventions. These are
associations in an observational table. **Extension:** use documented timestamps/batches and ore
domains to build grouped or rolling validation, then test interventions only in the digital twin or
a controlled campaign.
"""
    ),
]
notebook.metadata.kernelspec = {
    "display_name": "Python 3.12",
    "language": "python",
    "name": "python3",
}
notebook.metadata.language_info = {"name": "python", "version": "3.12"}
nbformat.write(notebook, path)
print(f"Populated {path}")
