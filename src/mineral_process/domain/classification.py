"""Simplified hydrocyclone classification curve."""

from dataclasses import dataclass

import numpy as np


@dataclass(frozen=True)
class HydrocycloneModel:
    d50_um: float = 150.0
    sharpness: float = 3.0
    water_split_to_underflow: float = 0.25

    def __post_init__(self) -> None:
        if self.d50_um <= 0 or self.sharpness <= 0:
            raise ValueError("d50 and sharpness must be positive")
        if not 0 <= self.water_split_to_underflow <= 1:
            raise ValueError("water split must be in [0, 1]")

    def coarse_partition(self, size_um: np.ndarray | float) -> np.ndarray:
        size = np.asarray(size_um, dtype=float)
        if np.any(size < 0):
            raise ValueError("particle size cannot be negative")
        return 1.0 / (1.0 + np.exp(-self.sharpness * np.log(np.maximum(size, 1e-9) / self.d50_um)))

    def split_solids(self, size_um: np.ndarray, mass: np.ndarray) -> tuple[float, float]:
        if len(size_um) != len(mass) or np.any(np.asarray(mass) < 0):
            raise ValueError("size and mass arrays must align and mass must be non-negative")
        underflow = float(np.sum(np.asarray(mass) * self.coarse_partition(size_um)))
        total = float(np.sum(mass))
        return total - underflow, underflow
