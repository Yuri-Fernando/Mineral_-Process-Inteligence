"""Small deterministic mineral-processing digital twin for safe offline experiments."""

from __future__ import annotations

from dataclasses import asdict, dataclass

import numpy as np

from mineral_process.domain.comminution import BondMillModel


@dataclass
class PlantState:
    feed_grade: float = 0.012
    feed_hardness: float = 16.0
    feed_f80_um: float = 2500.0
    throughput_tph: float = 110.0
    mill_power_kw: float = 1850.0
    p80_um: float = 160.0
    pulp_density: float = 1.35
    ph: float = 9.8
    air_flow: float = 1.3
    pulp_level: float = 0.55
    reagent_gpt: float = 35.0
    recovery: float = 0.82
    concentrate_grade: float = 0.22
    tailings_grade: float = 0.003
    specific_energy_kwh_t: float = 16.8
    cost_proxy: float = 0.0


@dataclass(frozen=True)
class PlantAction:
    air_flow: float
    pulp_level: float
    ph: float
    reagent_gpt: float
    throughput_tph: float


class SyntheticMineralPlant:
    """A stable, interpretable surrogate; not a model of a specific mine."""

    def __init__(self, seed: int = 42):
        self.seed = seed
        self.rng = np.random.default_rng(seed)
        self.state = PlantState()
        self.step_number = 0

    def reset(self, seed: int | None = None) -> dict[str, float]:
        if seed is not None:
            self.seed = seed
        self.rng = np.random.default_rng(self.seed)
        self.state = PlantState()
        self.step_number = 0
        return self.observe()

    @staticmethod
    def _clip_action(action: PlantAction) -> PlantAction:
        return PlantAction(
            air_flow=float(np.clip(action.air_flow, 0.5, 2.5)),
            pulp_level=float(np.clip(action.pulp_level, 0.2, 0.9)),
            ph=float(np.clip(action.ph, 8.0, 11.5)),
            reagent_gpt=float(np.clip(action.reagent_gpt, 5.0, 80.0)),
            throughput_tph=float(np.clip(action.throughput_tph, 60.0, 180.0)),
        )

    def step(self, action: PlantAction) -> dict[str, float]:
        action = self._clip_action(action)
        s = self.state
        s.air_flow += 0.35 * (action.air_flow - s.air_flow)
        s.pulp_level += 0.30 * (action.pulp_level - s.pulp_level)
        s.ph += 0.25 * (action.ph - s.ph)
        s.reagent_gpt += 0.20 * (action.reagent_gpt - s.reagent_gpt)
        s.throughput_tph += 0.25 * (action.throughput_tph - s.throughput_tph)

        mill = BondMillModel(s.feed_hardness)
        target_p80 = mill.p80_from_power(s.throughput_tph, s.feed_f80_um, s.mill_power_kw)
        s.p80_um += 0.20 * (target_p80 - s.p80_um)
        s.specific_energy_kwh_t = s.mill_power_kw / s.throughput_tph

        grind_factor = np.exp(-(((s.p80_um - 145.0) / 85.0) ** 2))
        air_factor = np.exp(-(((s.air_flow - 1.45) / 0.70) ** 2))
        ph_factor = np.exp(-(((s.ph - 10.1) / 1.05) ** 2))
        reagent_factor = 1.0 - np.exp(-s.reagent_gpt / 25.0)
        level_factor = np.exp(-(((s.pulp_level - 0.58) / 0.28) ** 2))
        equilibrium_recovery = np.clip(
            0.35
            + 0.30 * grind_factor
            + 0.12 * air_factor
            + 0.10 * ph_factor
            + 0.10 * reagent_factor
            + 0.05 * level_factor
            - 0.0012 * max(s.throughput_tph - 115, 0),
            0.20,
            0.96,
        )
        s.recovery += 0.18 * (equilibrium_recovery - s.recovery)
        s.recovery = float(np.clip(s.recovery + self.rng.normal(0, 0.0015), 0.0, 1.0))
        mass_pull = np.clip(0.025 + 0.04 * s.air_flow / 2.5 + 0.025 * s.pulp_level, 0.02, 0.15)
        s.concentrate_grade = float(
            np.clip(s.feed_grade * s.recovery / mass_pull, s.feed_grade, 0.60)
        )
        denominator = max(1 - mass_pull, 1e-6)
        s.tailings_grade = float(
            np.clip(s.feed_grade * (1 - s.recovery) / denominator, 0, s.feed_grade)
        )
        s.cost_proxy = float(
            0.06 * s.specific_energy_kwh_t + 0.004 * s.reagent_gpt + 0.02 * s.air_flow**2
        )
        self.step_number += 1
        return self.observe()

    def inject_disturbance(
        self, *, feed_grade: float | None = None, hardness: float | None = None
    ) -> None:
        if feed_grade is not None:
            if not 0.002 <= feed_grade <= 0.08:
                raise ValueError("feed grade disturbance is outside configured bounds")
            self.state.feed_grade = float(feed_grade)
        if hardness is not None:
            if not 5 <= hardness <= 30:
                raise ValueError("hardness disturbance is outside configured bounds")
            self.state.feed_hardness = float(hardness)

    def observe(self) -> dict[str, float]:
        return {key: float(value) for key, value in asdict(self.state).items()}

    def run(self, steps: int, action: PlantAction | None = None) -> list[dict[str, float]]:
        action = action or PlantAction(1.45, 0.58, 10.1, 35.0, 110.0)
        return [self.step(action) for _ in range(steps)]
