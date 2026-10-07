from fastapi.testclient import TestClient

from mineral_process.api.main import app

client = TestClient(app)


def test_fault_and_drift_endpoints() -> None:
    fault = client.post(
        "/fault/inject",
        json={"values": [1, 2, 3, 4], "kind": "bias", "start": 1, "severity": 1.0},
    )
    assert fault.status_code == 200
    assert fault.json()["synthetic_fault"] is True
    drift = client.post(
        "/monitoring/drift",
        json={"reference": [0, 0, 1, 1, 2, 2], "current": [5, 5, 6, 6, 7, 7]},
    )
    assert drift.status_code == 200
    assert drift.json()["drifted"] is True


def test_process_state_fails_closed_when_critical_field_is_missing() -> None:
    response = client.post("/process/state", json={"state": {"feed_grade": 0.02}})
    assert response.json()["safety_status"] == "REJECT"
