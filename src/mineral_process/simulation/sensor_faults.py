"""Reproducible industrial sensor fault injection."""

from dataclasses import dataclass
from enum import StrEnum

import numpy as np


class FaultType(StrEnum):
    NOISE = "noise"
    BIAS = "bias"
    DRIFT = "drift"
    STUCK = "stuck"
    DROPOUT = "dropout"
    SPIKE = "spike"
    LATENCY = "latency"
    SCALING = "scaling"


@dataclass(frozen=True)
class FaultSpec:
    kind: FaultType
    start: int
    severity: float = 0.1
    duration: int | None = None


def inject_fault(values: np.ndarray, spec: FaultSpec, seed: int = 42) -> np.ndarray:
    result = np.asarray(values, dtype=float).copy()
    if not 0 <= spec.start < len(result):
        raise ValueError("fault start is outside the signal")
    end = min(len(result), spec.start + (spec.duration or len(result)))
    segment = slice(spec.start, end)
    rng = np.random.default_rng(seed)
    scale = max(float(np.nanstd(result)), 1e-9)
    if spec.kind == FaultType.NOISE:
        result[segment] += rng.normal(0, spec.severity * scale, end - spec.start)
    elif spec.kind == FaultType.BIAS:
        result[segment] += spec.severity * scale
    elif spec.kind == FaultType.DRIFT:
        result[segment] += np.linspace(0, spec.severity * scale, end - spec.start)
    elif spec.kind == FaultType.STUCK:
        result[segment] = result[spec.start]
    elif spec.kind == FaultType.DROPOUT:
        result[segment] = np.nan
    elif spec.kind == FaultType.SPIKE:
        indexes = rng.choice(
            np.arange(spec.start, end), size=max(1, (end - spec.start) // 20), replace=False
        )
        result[indexes] += spec.severity * 10 * scale
    elif spec.kind == FaultType.LATENCY:
        lag = max(1, int(round(spec.severity)))
        result[spec.start : end] = np.roll(result, lag)[spec.start : end]
    elif spec.kind == FaultType.SCALING:
        result[segment] *= 1 + spec.severity
    return result
