from __future__ import annotations

from dataclasses import dataclass

import numpy as np


@dataclass(frozen=True)
class ComparisonReport:
    max_abs_error: float
    rms_error: float
    mean_error: float
    passed: bool
    tolerance: float


def compare_results(
    host: np.ndarray, device: np.ndarray, tolerance: float = 1e-6
) -> ComparisonReport:
    """Compare host and device vectors without hiding length or finite-value errors."""
    left = np.asarray(host, dtype=float).reshape(-1)
    right = np.asarray(device, dtype=float).reshape(-1)
    if left.shape != right.shape:
        raise ValueError(f"result lengths differ: {left.size} != {right.size}")
    if not np.all(np.isfinite(left)) or not np.all(np.isfinite(right)):
        raise ValueError("comparison vectors must be finite")
    error = right - left
    return ComparisonReport(
        float(np.max(np.abs(error), initial=0.0)),
        float(np.sqrt(np.mean(error**2))) if error.size else 0.0,
        float(np.mean(error)) if error.size else 0.0,
        bool(np.all(np.abs(error) <= tolerance)),
        tolerance,
    )
