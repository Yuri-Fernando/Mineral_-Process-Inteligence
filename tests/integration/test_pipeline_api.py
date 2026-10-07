from fastapi.testclient import TestClient

from mineral_process.api.main import app
from mineral_process.pipeline import run_end_to_end


def test_end_to_end_pipeline_writes_artifacts(tmp_path) -> None:
    summary = run_end_to_end(tmp_path, seed=3)
    assert summary["data_kind"] == "synthetic_demo"
    assert (tmp_path / "run_summary.json").exists()
    assert (tmp_path / "optimization_pareto.csv").exists()


def test_api_health_and_state() -> None:
    client = TestClient(app)
    assert client.get("/health").json()["status"] == "ok"
    state = client.get("/simulation/state").json()
    assert state["recovery"] > 0
