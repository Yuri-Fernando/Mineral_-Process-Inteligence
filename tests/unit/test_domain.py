import numpy as np
import pytest

from mineral_process.domain.classification import HydrocycloneModel
from mineral_process.domain.comminution import BondMillModel, bond_specific_energy
from mineral_process.domain.flotation import FlotationBank, FlotationCell, FlotationKineticsModel
from mineral_process.domain.mass_balance import solve_two_product


def test_two_product_balance_conserves_mass_and_metal() -> None:
    result = solve_two_product(100.0, 0.02, 0.25, 0.004)
    result.assert_conserved()
    assert 0 < result.metallurgical_recovery < 1


def test_invalid_assay_order_is_rejected() -> None:
    with pytest.raises(ValueError):
        solve_two_product(100, 0.02, 0.01, 0.03)


def test_bond_energy_is_physical_and_monotonic() -> None:
    coarse = bond_specific_energy(15, 2500, 200)
    fine = bond_specific_energy(15, 2500, 100)
    assert 0 < coarse < fine
    model = BondMillModel(15)
    assert model.p80_from_power(100, 2500, model.mill_power_kw(100, 2500, 150)) == pytest.approx(
        150
    )


def test_hydrocyclone_partition_increases_with_size() -> None:
    curve = HydrocycloneModel().coarse_partition(np.array([20, 150, 500]))
    assert np.all(np.diff(curve) > 0)


def test_flotation_bank_recovers_more_than_one_cell() -> None:
    cell = FlotationCell(20, FlotationKineticsModel())
    bank = FlotationBank((cell, cell))
    assert cell.recovery(10) < bank.recovery(10) < 1
