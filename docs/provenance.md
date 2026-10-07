# Provenance and reproducibility

Run `python -m mineral_process.cli download-data`. Each successful file is recorded in
`data/raw/provenance.json` with its source URL, download timestamp, size and SHA-256. Partial success
is preserved; exact upstream failures go to `data/raw/download_failures.json`.

Raw data, trained models and generated reports are local artifacts and are excluded from Git. The
metadata/configuration, code, tests, notebooks, changelog and master ledger are versioned.

The demo path uses seed 42 by default. It remains executable if Kaggle credentials or network access
are unavailable because the simulated case is intentionally independent of real-data performance.
