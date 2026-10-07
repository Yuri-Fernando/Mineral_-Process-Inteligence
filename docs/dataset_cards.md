# Dataset cards

## Copper GeoMet

- Source: Zenodo record `7051975`, DOI `10.5281/zenodo.7051975`.
- Files: `drillholes.csv`, `comminution.csv`, `flotation.csv`.
- Intended use: spatially validated BWI/DWT/recovery modeling and uncertainty demonstrations.
- Leakage control: spatial block holdout, not random-only validation.
- Caveat: preserve upstream attribution and terms; raw data are ignored by Git.

## Iron-ore flotation

- Source: Kaggle dataset `edumagalhaes/quality-prediction-in-a-mining-process`.
- Intended use: delayed-lab silica soft sensor, mixed-frequency audit and sensor-fault stress tests.
- Leakage control: chronological holdout; `% Iron Concentrate` and `% Silica Concentrate` are treated
  as same-assay laboratory variables and excluded from online inputs.
- Caveat: Kaggle may require an account/API credentials even for a public dataset.

## Polymetallic grinding/classification

- Source: Zenodo record `22773521`, DOI `10.5281/zenodo.22773521`.
- File: `Base de datos.xlsx` (692 observations and 32 variables per upstream description).
- Intended use: Ag/Cu/Pb/Zn recovery sensitivity and throughput/grind/recovery trade-offs.
- Caveat: small observational dataset; associations must not be presented as causal interventions.

## Synthetic mineral plant

- Source: deterministic equations in this repository.
- Intended use: software validation, DOE, faults, optimization and closed-loop MPC comparisons.
- It is not real industrial data and not calibrated to a named mine or concentrator.
