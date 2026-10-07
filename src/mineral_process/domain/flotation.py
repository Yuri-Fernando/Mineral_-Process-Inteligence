"""Calibratable first-order flotation kinetics and bank composition."""

from dataclasses import dataclass
from math import exp


@dataclass(frozen=True)
class FlotationKineticsModel:
    maximum_recovery: float = 0.90
    rate_constant_per_min: float = 0.35

    def __post_init__(self) -> None:
        if not 0 <= self.maximum_recovery <= 1:
            raise ValueError("maximum recovery must be in [0, 1]")
        if self.rate_constant_per_min <= 0:
            raise ValueError("rate constant must be positive")

    def recovery(self, residence_time_min: float) -> float:
        if residence_time_min < 0:
            raise ValueError("residence time cannot be negative")
        return self.maximum_recovery * (1 - exp(-self.rate_constant_per_min * residence_time_min))


@dataclass(frozen=True)
class FlotationCell:
    volume_m3: float
    kinetics: FlotationKineticsModel

    def recovery(self, slurry_flow_m3_min: float) -> float:
        if slurry_flow_m3_min <= 0:
            raise ValueError("slurry flow must be positive")
        return self.kinetics.recovery(self.volume_m3 / slurry_flow_m3_min)


@dataclass(frozen=True)
class FlotationBank:
    cells: tuple[FlotationCell, ...]

    def recovery(self, slurry_flow_m3_min: float) -> float:
        unrecovered = 1.0
        for cell in self.cells:
            unrecovered *= 1.0 - cell.recovery(slurry_flow_m3_min)
        return 1.0 - unrecovered
