# Changelog

All notable changes follow [Keep a Changelog](https://keepachangelog.com/en/1.1.0/) and the
project uses [Semantic Versioning](https://semver.org/).

## [Unreleased]

### Planned

- Optional MLflow registry and experiment UI.
- Calibrated sequence models after the classical temporal baseline is established.
- External validation against a process-engineering simulator.


## [0.2.2] - 2026-10-06

### Fixed

- Standardized the full project, Docker image, GitHub Actions and notebooks on Python 3.10.
- Replaced Python 3.11-only StrEnum usage with Python 3.10-compatible string enums.
- Declared the clean-environment TestClient dependency required by the Linux CI runner.

### Changed

- Re-executed all four notebooks with the dedicated Python 3.10 kernel.

## [0.2.1] - 2026-10-06

### Added

- Reproducible Python 3.10 notebook executor that persists outputs and stops on cell errors.
- Expanded portfolio README with architecture, module map, real metrics, API, dashboard, notebook,
  safety, validation, limitations and roadmap documentation.

### Changed

- All four end-to-end notebooks are committed with fresh execution counts and outputs.

## [0.2.0] - 2026-10-06

### Added

- Real GeoMet spatial-holdout pipeline for upstream `M`, `A` and `LCT` targets.
- Gaussian-Process Bayesian optimization with Expected Improvement and an in-repo NSGA-II.
- Polymetallic operational-feature recovery baselines and descriptive observed Pareto frontier.
- Same-disturbance fixed/rule-based/Economic-MPC benchmark and generated HTML/CSV reports.
- Extended API endpoints for soft sensing, process state, synthetic fault injection and drift.
- Local JSON experiment tracking with optional MLflow mirroring.
- Fourth end-to-end notebook and dashboard tabs for real case studies and controller comparison.

### Changed

- Economic MPC safety status now checks predicted concentrate grade and returns `REVIEW` when the
  numerical solution violates the configured grade specification.

## [0.1.0] - 2026-10-06

### Added

- Local-first mineral-processing domain core, synthetic digital twin and sensor-fault lab.
- Causal temporal features, data-quality flags, drift monitoring and soft-sensor training.
- Constrained setpoint optimization, multiobjective Pareto search and advisory MPC.
- Dataset downloader with provenance manifests for GeoMet, iron flotation and polymetallic data.
- FastAPI service, Streamlit dashboard, end-to-end runner, notebooks and scientific tests.
- Project ledger, architecture/data/safety documentation, CI, Docker and reproducible configuration.
