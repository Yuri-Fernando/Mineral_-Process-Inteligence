# Project Ledger

This is the master continuity document. Update it with every material change.

## Identity

- Project: Mineral Process Intelligence
- Current version: `0.2.2`
- Started: 2026-10-06
- Status: applied-research implementation; advisory-only; no production-mine deployment claim
- Source of truth: Python package and CLI. Dashboard and notebooks are presentation/tutorial layers.

## Non-negotiable boundaries

1. GeoMet, iron-flotation and polymetallic datasets are independent case studies and are never
   concatenated as if they came from one plant.
2. Public real data, derived artifacts and synthetic digital-twin data are visibly separated.
3. Temporal features are causal; the final holdout is later in time than training data.
4. Recommendations are advisory. Missing critical sensors, poor quality, OOD inputs or constraint
   failure return `NO_ACTION`.
5. Simplified equations are educational/calibratable surrogates, not a faithful model of a named
   industrial plant.

## Decision history

| Date | Decision | Rationale |
|---|---|---|
| 2026-10-06 | Create a standalone repository | Mineral processing/industrial control has a distinct identity from TerraBranch. |
| 2026-10-06 | Python 3.10, `src/` layout, local-first | Reproducible on a free CPU environment and compatible with the available toolchain. |
| 2026-10-06 | SciPy optimizer in the core | Keeps the end-to-end path free and executable; Optuna/MLflow remain optional extras. |
| 2026-10-06 | Synthetic fallback for demos | The Kaggle source may require credentials and real datasets must never block validation. |
| 2026-10-06 | Dashboard is read-only/advisory | The engine/CLI stays authoritative and no control command is written to a real plant. |

## Data register

| Case | Kind | Upstream | Local policy |
|---|---|---|---|
| Copper GeoMet | public real measurements | Zenodo 7051975 | downloaded locally, checksum manifest, excluded from Git |
| Iron flotation | public industrial time series | Kaggle | downloaded if public API permits; otherwise documented manual command |
| Polymetallic grinding | public real measurements | Zenodo 22773521 | downloaded locally, checksum manifest, excluded from Git |
| Synthetic plant | simulated | this repository | deterministic generator; labeled synthetic |

## Validation log

Append commands, dates and truthful results here. Do not replace older entries.

### 2026-10-06 — implementation opened

- Confirmed Python 3.10 plus the required free scientific/API/dashboard tooling are available.
- Live validation results are recorded after implementation in this section.


### 2026-10-06 — v0.1.0 local validation

- Public downloads: 5 upstream files downloaded; zero recorded failures; SHA-256 manifest written.
- Observed GeoMet shapes: drillholes `2000 x 22`, comminution `60 x 28`, flotation `53 x 26`.
- Observed polymetallic workbook: `Matriz_datos` is `691 x 47` and `Diccionario` is `47 x 3`.
  This differs from the upstream page description (`692 x 32`) and is retained as an audit finding.
- `pytest`: 13 passed. One harmless joblib warning reported unavailable physical-core metadata.
- Ruff: all checks passed after formatting.
- mypy: success across 29 source files.
- CLI synthetic demo: MAE `0.0804`, RMSE `0.1030`, R2 `0.7904`; drift was detected after the
  seeded disturbance; optimizer returned `REVIEW` because predicted grade was below specification.
- Dashboard: Streamlit AppTest rendered the title and reported zero exceptions.
- Notebooks: every code cell in all three notebooks executed sequentially with Python 3.10.
  The real-data tutorial used the first 120,000 chronological Kaggle rows; its honest holdout
  baseline was MAE `0.8522`, RMSE `1.0748`, R2 `-0.5989` and requires temporal feature improvement.
- Docker Compose configuration parsed, but image/runtime validation was not performed because the
  Docker Desktop Linux daemon was not running.

## Versioning procedure

1. Update `VERSION` and `project.version` together.
2. Move relevant entries from `Unreleased` into a dated section of `CHANGELOG.md`.
3. Add decisions and validation evidence here; never erase previous evidence.
4. Commit code, tests, docs and small manifests. Never commit raw datasets, models, caches or secrets.
5. Tag releases as `vMAJOR.MINOR.PATCH` after the documented checks pass.

## Known limitations

- No production historian, LIMS, PLC/DCS or mine connection is present.
- Models trained on public datasets do not transfer to another operation without revalidation.
- Digital-twin dynamics are deliberately compact and are not a calibrated plant model.
- Dataset pages did not expose an explicit machine-readable license during the initial audit;
  upstream terms and citations must be preserved and raw data must not be redistributed here.



### 2026-10-06 — v0.2.0 real-case and control validation

- GeoMet spatial holdout: `M` R2 `0.5538` (56 train/4 test), `A` R2 `0.2805`
  (56/4), and `LCT` R2 `0.4497` (45/7). Raw target names remain unchanged.
- Polymetallic ordered holdout: all four recovery baselines produced negative R2; this is retained as
  evidence that nine grinding/classification variables alone do not generalize to the final source
  segment. The descriptive observed Pareto frontier contains 41 rows and makes no causal claim.
- Controller benchmark: Economic MPC improved average recovery to `0.9356` versus fixed `0.9221`,
  but all 45 intervals violated the `0.18` concentrate-grade specification. MPC safety was corrected
  to return `REVIEW` whenever its predicted grade violates specification.
- Extended API contracts, local/optional-MLflow tracking, real-case dashboard tabs and the fourth
  notebook were added.
- Final checks: `21 passed`; Ruff clean; mypy clean across 35 source files; dashboard AppTest rendered
  five tabs with zero exceptions; all cells in the fourth notebook executed with Python 3.10.
- Docker runtime remains unvalidated because the Docker Desktop Linux daemon is not running.
- Iron-flotation causal preparation consolidated 120,000 raw rows into 667 unique timestamps and
  252 past-only features. It did not beat the simple baseline: causal R2 `-0.6141` versus baseline
  `-0.5989`; both results remain documented as regime/feature insufficiency, not hidden by shuffling.
- Local experiment JSON was written successfully; MLflow mirroring was skipped because the optional
  dependency is not installed.
- Advanced optimization run: Gaussian-Process Expected Improvement evaluated 20 points and found
  a simulator-safe candidate with predicted recovery `0.8864` and grade `0.1838`; NSGA-II produced
  36 evolved non-dominated solutions. Both remain synthetic and advisory-only.
- Final dashboard AppTest rendered five tabs and five Plotly charts with zero exceptions.

### 2026-10-06 — v0.2.1 documentation and notebook release

- Compared the public README structures of VisionBrain, TerraBranch and AegisLLM before expanding
  the project documentation around context, objectives, architecture, modules, operation, metrics,
  quickstart, validation, limitations, roadmap and license.
- Executed all four end-to-end notebooks and persisted their outputs without cell errors.
- Added `scripts/execute_notebooks.py` so the saved notebook evidence can be reproduced in one command.
- Kept raw datasets, processed data, models, generated reports and secrets outside version control.
- Prepared the public `v0.2.1` release with the validated code, documentation and notebooks.

### 2026-10-06 — v0.2.2 Python 3.10 standardization

- Standardized package metadata, Ruff, mypy, Docker, GitHub Actions and notebook kernels on Python 3.10.
- Replaced Python 3.11-only string enums with Python 3.10-compatible str, Enum classes.
- Re-executed four notebooks with Python 3.10: 29 code cells, 30 outputs and zero cell errors.
- Added the TestClient dependency exposed by the clean Linux runner and repeated local/remote gates.
- Python 3.10 validation on a local non-synchronized copy: Ruff clean; mypy clean across 35
  source files; 21 tests passed; dashboard rendered five tabs with zero exceptions.
