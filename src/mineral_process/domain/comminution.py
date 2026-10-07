"""Compact, unit-explicit comminution surrogate models."""

from dataclasses import dataclass
from math import sqrt


def bond_specific_energy(work_index_kwh_t: float, f80_um: float, p80_um: float) -> float:
    """Return Bond specific energy in kWh/t for F80 and P80 expressed in micrometres."""
    if work_index_kwh_t <= 0:
        raise ValueError("work index must be positive")
    if f80_um <= 0 or p80_um <= 0:
        raise ValueError("particle sizes must be positive")
    if p80_um >= f80_um:
        raise ValueError("grinding requires P80 < F80")
    return work_index_kwh_t * (10.0 / sqrt(p80_um) - 10.0 / sqrt(f80_um))


@dataclass(frozen=True)
class BondMillModel:
    work_index_kwh_t: float
    mechanical_efficiency: float = 0.92

    def __post_init__(self) -> None:
        if self.work_index_kwh_t <= 0:
            raise ValueError("work index must be positive")
        if not 0 < self.mechanical_efficiency <= 1:
            raise ValueError("mechanical_efficiency must be in (0, 1]")

    def specific_energy(self, f80_um: float, p80_um: float) -> float:
        return (
            bond_specific_energy(self.work_index_kwh_t, f80_um, p80_um) / self.mechanical_efficiency
        )

    def mill_power_kw(self, throughput_tph: float, f80_um: float, p80_um: float) -> float:
        if throughput_tph <= 0:
            raise ValueError("throughput must be positive")
        return throughput_tph * self.specific_energy(f80_um, p80_um)

    def p80_from_power(self, throughput_tph: float, f80_um: float, mill_power_kw: float) -> float:
        if throughput_tph <= 0 or mill_power_kw <= 0 or f80_um <= 0:
            raise ValueError("throughput, power and F80 must be positive")
        e = mill_power_kw * self.mechanical_efficiency / throughput_tph
        denominator = e / self.work_index_kwh_t + 10.0 / sqrt(f80_um)
        return (10.0 / denominator) ** 2
