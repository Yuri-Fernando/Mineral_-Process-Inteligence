import json

from mineral_process.monitoring.tracking import track_run


def test_local_tracking_works_without_mlflow(tmp_path) -> None:
    path = track_run("test run", {"seed": 1}, {"mae": 0.5}, root=tmp_path, mirror_mlflow=False)
    payload = json.loads(path.read_text(encoding="utf-8"))
    assert payload["metrics"]["mae"] == 0.5
    assert payload["mlflow_mirrored"] is False
