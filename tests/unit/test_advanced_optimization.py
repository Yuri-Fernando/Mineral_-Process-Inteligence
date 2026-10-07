import numpy as np

from mineral_process.optimization.bayesian import BOUNDS, bayesian_optimize
from mineral_process.optimization.nsga2 import non_dominated_front, nsga2_optimize
from mineral_process.simulation.digital_twin import SyntheticMineralPlant


def test_bayesian_optimizer_returns_bounded_advisory_action() -> None:
    result = bayesian_optimize(SyntheticMineralPlant().observe(), iterations=2, initial_points=3)
    values = np.array(list(result.action.__dict__.values()))
    assert np.all(values >= BOUNDS[:, 0]) and np.all(values <= BOUNDS[:, 1])
    assert result.evaluations == 5


def test_nsga2_returns_only_non_dominated_bounded_points() -> None:
    result = nsga2_optimize(
        SyntheticMineralPlant().observe(), population_size=8, generations=2, seed=3
    )
    assert len(result.decisions) >= 1
    assert np.all(result.decisions >= BOUNDS[:, 0]) and np.all(result.decisions <= BOUNDS[:, 1])
    np.testing.assert_array_equal(
        non_dominated_front(result.objectives), np.arange(len(result.objectives))
    )
