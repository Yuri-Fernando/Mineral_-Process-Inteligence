"""Two-product metallurgical mass-balance utilities."""

from dataclasses import dataclass
from math import isclose


def _fraction(value: float, name: str) -> float:
    if not 0.0 <= value <= 1.0:
        raise ValueError(f"{name} must be a mass fraction in [0, 1]")
    return float(value)


@dataclass(frozen=True)
class MassBalanceResult:
    feed_mass: float
    concentrate_mass: float
    tailings_mass: float
    feed_grade: float
    concentrate_grade: float
    tailings_grade: float

    @property
    def mass_recovery(self) -> float:
        return self.concentrate_mass / self.feed_mass

    @property
    def metallurgical_recovery(self) -> float:
        feed_metal = self.feed_mass * self.feed_grade
        return (
            0.0 if feed_metal == 0 else self.concentrate_mass * self.concentrate_grade / feed_metal
        )

    @property
    def mass_residual(self) -> float:
        return self.feed_mass - self.concentrate_mass - self.tailings_mass

    @property
    def metal_residual(self) -> float:
        return (
            self.feed_mass * self.feed_grade
            - self.concentrate_mass * self.concentrate_grade
            - self.tailings_mass * self.tailings_grade
        )

    def assert_conserved(self, tolerance: float = 1e-9) -> None:
        if not isclose(self.mass_residual, 0.0, abs_tol=tolerance):
            raise ValueError(f"mass is not conserved: residual={self.mass_residual}")
        if not isclose(self.metal_residual, 0.0, abs_tol=tolerance):
            raise ValueError(f"metal is not conserved: residual={self.metal_residual}")


def solve_two_product(
    feed_mass: float, feed_grade: float, concentrate_grade: float, tailings_grade: float
) -> MassBalanceResult:
    """Solve a steady two-product balance from feed flow and three assays."""
    if feed_mass <= 0:
        raise ValueError("feed_mass must be positive")
    f = _fraction(feed_grade, "feed_grade")
    c = _fraction(concentrate_grade, "concentrate_grade")
    t = _fraction(tailings_grade, "tailings_grade")
    if not t <= f <= c or c == t:
        raise ValueError("expected tailings_grade <= feed_grade <= concentrate_grade")
    concentrate_mass = feed_mass * (f - t) / (c - t)
    result = MassBalanceResult(
        feed_mass=float(feed_mass),
        concentrate_mass=concentrate_mass,
        tailings_mass=float(feed_mass) - concentrate_mass,
        feed_grade=f,
        concentrate_grade=c,
        tailings_grade=t,
    )
    result.assert_conserved()
    return result
