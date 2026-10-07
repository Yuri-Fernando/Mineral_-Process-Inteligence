"""Dependency-light feature drift metrics."""

from dataclasses import dataclass

import numpy as np
from scipy.stats import ks_2samp, wasserstein_distance


@dataclass(frozen=True)
class DriftReport:
    psi: float
    ks_statistic: float
    ks_pvalue: float
    wasserstein: float
    drifted: bool


def population_stability_index(reference: np.ndarray, current: np.ndarray, bins: int = 10) -> float:
    reference = np.asarray(reference, dtype=float)
    current = np.asarray(current, dtype=float)
    reference = reference[np.isfinite(reference)]
    current = current[np.isfinite(current)]
    if not len(reference) or not len(current):
        raise ValueError("both samples need finite observations")
    edges = np.unique(np.quantile(reference, np.linspace(0, 1, bins + 1)))
    if len(edges) < 3:
        return 0.0
    ref_counts, _ = np.histogram(reference, edges)
    cur_counts, _ = np.histogram(current, edges)
    ref_rate = np.clip(ref_counts / ref_counts.sum(), 1e-6, None)
    cur_rate = np.clip(cur_counts / max(cur_counts.sum(), 1), 1e-6, None)
    return float(np.sum((cur_rate - ref_rate) * np.log(cur_rate / ref_rate)))


def drift_report(reference: np.ndarray, current: np.ndarray) -> DriftReport:
    psi = population_stability_index(reference, current)
    ks = ks_2samp(reference, current, nan_policy="omit")
    wasserstein = float(wasserstein_distance(reference, current))
    return DriftReport(
        psi, float(ks.statistic), float(ks.pvalue), wasserstein, psi >= 0.2 or ks.pvalue < 0.01
    )
