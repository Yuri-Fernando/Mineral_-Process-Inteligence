"""Compact NSGA-II implementation for the synthetic mineral process."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from mineral_process.optimization.bayesian import BOUNDS
from mineral_process.optimization.recommend import _evaluate


@dataclass(frozen=True)
class NSGA2Result:
    decisions: np.ndarray
    objectives: np.ndarray


def _objectives(population: np.ndarray, state: dict[str, float]) -> np.ndarray:
    rows = []
    for decision in population:
        _, final = _evaluate(decision, state, horizon=8)
        grade_penalty = 10 * max(0.18 - final["concentrate_grade"], 0)
        rows.append(
            [
                -final["recovery"] + grade_penalty,
                -final["concentrate_grade"] + grade_penalty,
                final["cost_proxy"],
            ]
        )
    return np.asarray(rows)


def _dominates(left: np.ndarray, right: np.ndarray) -> bool:
    return bool(np.all(left <= right) and np.any(left < right))


def non_dominated_front(objectives: np.ndarray) -> np.ndarray:
    keep = np.ones(len(objectives), dtype=bool)
    for index, row in enumerate(objectives):
        keep[index] = not any(
            _dominates(other, row)
            for other_index, other in enumerate(objectives)
            if other_index != index
        )
    return np.flatnonzero(keep)


def _crowding(objectives: np.ndarray) -> np.ndarray:
    distance = np.zeros(len(objectives))
    for column in range(objectives.shape[1]):
        order = np.argsort(objectives[:, column])
        distance[order[[0, -1]]] = np.inf
        span = objectives[order[-1], column] - objectives[order[0], column]
        if span > 0:
            distance[order[1:-1]] += (
                objectives[order[2:], column] - objectives[order[:-2], column]
            ) / span
    return distance


def nsga2_optimize(
    state: dict[str, float], population_size: int = 36, generations: int = 12, seed: int = 42
) -> NSGA2Result:
    """Evolve recovery, grade and cost objectives with elitist non-dominated selection."""
    if population_size < 8 or generations < 1:
        raise ValueError("population_size >= 8 and generations >= 1 are required")
    rng = np.random.default_rng(seed)
    population = rng.uniform(BOUNDS[:, 0], BOUNDS[:, 1], (population_size, 5))
    scale = BOUNDS[:, 1] - BOUNDS[:, 0]
    for _ in range(generations):
        parents = population[rng.integers(0, population_size, size=(population_size, 2))]
        alpha = rng.uniform(size=(population_size, 1))
        children = alpha * parents[:, 0] + (1 - alpha) * parents[:, 1]
        children += rng.normal(0, 0.06 * scale, size=children.shape)
        children = np.clip(children, BOUNDS[:, 0], BOUNDS[:, 1])
        combined = np.vstack([population, children])
        objective_values = _objectives(combined, state)
        front = non_dominated_front(objective_values)
        if len(front) >= population_size:
            crowding = _crowding(objective_values[front])
            selected = front[np.argsort(crowding)[-population_size:]]
        else:
            remaining = np.setdiff1d(np.arange(len(combined)), front)
            score = objective_values[remaining].sum(axis=1)
            selected = np.concatenate(
                [front, remaining[np.argsort(score)[: population_size - len(front)]]]
            )
        population = combined[selected]
    objective_values = _objectives(population, state)
    final_front = non_dominated_front(objective_values)
    return NSGA2Result(population[final_front], objective_values[final_front])
