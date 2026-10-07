"""Local experiment ledger with optional MLflow mirroring."""

from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


def track_run(
    run_name: str,
    params: dict[str, Any],
    metrics: dict[str, float | int],
    artifacts: list[str] | None = None,
    root: Path = Path("reports/generated/experiments"),
    mirror_mlflow: bool = True,
) -> Path:
    """Always write portable JSON; mirror to MLflow only when the optional extra is installed."""
    root.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now(UTC)
    safe_name = "".join(
        character if character.isalnum() or character in "-_" else "-" for character in run_name
    )
    path = root / f"{timestamp.strftime('%Y%m%dT%H%M%SZ')}-{safe_name}.json"
    payload = {
        "schema_version": 1,
        "run_name": run_name,
        "timestamp": timestamp.isoformat(),
        "params": params,
        "metrics": metrics,
        "artifacts": artifacts or [],
        "mlflow_mirrored": False,
    }
    if mirror_mlflow:
        try:
            import mlflow

            with mlflow.start_run(run_name=run_name):
                mlflow.log_params(params)
                mlflow.log_metrics({key: float(value) for key, value in metrics.items()})
                for artifact in artifacts or []:
                    if Path(artifact).exists():
                        mlflow.log_artifact(artifact)
            payload["mlflow_mirrored"] = True
        except ImportError:
            payload["mlflow_note"] = (
                "optional dependency not installed; local JSON is authoritative"
            )
    path.write_text(json.dumps(payload, indent=2, default=str), encoding="utf-8")
    return path
