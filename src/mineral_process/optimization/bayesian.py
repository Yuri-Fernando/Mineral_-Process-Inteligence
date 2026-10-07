"""Dependency-light Bayesian optimization with Gaussian Process and expected improvement."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from scipy.stats import norm
from sklearn.gaussian_process import GaussianProcessRegressor
from sklearn.gaussian_process.kernels import Matern, WhiteKernel

from mineral_process.optimization.recommend import _evaluate
from mineral_process.simulation.digital_twin import PlantAction

BOUNDS = np.array([(0.5, 2.5), (0.2, 0.9), (8.0, 11.5), (5.0, 80.0), (60.0, 180.0)])


@dataclass(frozen=True)
class BayesianResult:
    action: PlantAction
    objective: float
    evaluations: int
    expected_recovery: float
    expected_grade: float
    safety_status: str


def _sample(rng: np.random.Generator, count: int) -> np.ndarray:
    return rng.uniform(BOUNDS[:, 0], BOUNDS[:, 1], size=(count, len(BOUNDS)))


def bayesian_optimize(
    state: dict[str, float], iterations: int = 14, initial_points: int = 6, seed: int = 42
) -> BayesianResult:
    """Minimize the constrained economic surrogate with sequential expected improvement."""
    if iterations < 1 or initial_points < 2:
        raise ValueError("iterations >= 1 and initial_points >= 2 are required")
    rng = np.random.default_rng(seed)
    points = _sample(rng, initial_points)
    objectives = np.array([_evaluate(point, state)[0] for point in points])
    kernel = Matern(length_scale=np.ones(5), nu=2.5) + WhiteKernel(noise_level=1e-5)
    for _ in range(iterations):
        scaled = (points - BOUNDS[:, 0]) / (BOUNDS[:, 1] - BOUNDS[:, 0])
        gp = GaussianProcessRegressor(kernel=kernel, normalize_y=True, random_state=seed)
        gp.fit(scaled, objectives)
        candidates = _sample(rng, 512)
        candidates_scaled = (candidates - BOUNDS[:, 0]) / (BOUNDS[:, 1] - BOUNDS[:, 0])
        mean, std = gp.predict(candidates_scaled, return_std=True)
        improvement = objectives.min() - mean - 0.01
        z_score = np.divide(improvement, std, out=np.zeros_like(std), where=std > 1e-12)
        expected_improvement = improvement * norm.cdf(z_score) + std * norm.pdf(z_score)
        next_point = candidates[int(np.argmax(expected_improvement))]
        points = np.vstack([points, next_point])
        objectives = np.append(objectives, _evaluate(next_point, state)[0])
    best = int(np.argmin(objectives))
    action = PlantAction(*map(float, points[best]))
    objective, final = _evaluate(points[best], state)
    status = "SAFE" if final["concentrate_grade"] >= 0.18 else "REVIEW"
    return BayesianResult(
        action,
        objective,
        len(objectives),
        final["recovery"],
        final["concentrate_grade"],
        status,
    )
