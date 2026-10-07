from mineral_process.case_studies import POLY_OPERATIONAL_FEATURES, POLY_TARGETS
from mineral_process.control.benchmark import benchmark_controllers


def test_polymetallic_contract_excludes_assay_and_recovery_leakage() -> None:
    assert not any(feature.startswith(("En_", "Rec_")) for feature in POLY_OPERATIONAL_FEATURES)
    assert all(target.startswith("Rec_") for target in POLY_TARGETS)


def test_controller_benchmark_uses_same_length_and_writes_outputs(tmp_path) -> None:
    trajectory, metrics = benchmark_controllers(tmp_path, steps=9, seed=7)
    assert set(metrics.controller) == {"fixed", "rule_based", "economic_mpc"}
    assert trajectory.groupby("controller").size().nunique() == 1
    assert (tmp_path / "mpc_benchmark.csv").exists()
