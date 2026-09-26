from __future__ import annotations

import numpy as np

from signal_processing_toolkit.dsp.filters.design import (
    apply_zero_phase,
    design_filter,
    filter_group_delay,
    frequency_response,
    impulse_response,
    step_response,
)
from signal_processing_toolkit.models.filter_design import (
    FilterCoefficients,
    FilterDesign,
    FrequencyResponse,
)
from signal_processing_toolkit.models.signal import Signal


def design_fir_filter(design: FilterDesign) -> FilterCoefficients:
    return design_filter(design)


def apply_fir_filter(
    signal: Signal | np.ndarray, coefficients: FilterCoefficients
) -> Signal | np.ndarray:
    wrapped = signal if isinstance(signal, Signal) else Signal(np.asarray(signal), 1.0)
    result = apply_zero_phase(wrapped, coefficients)
    return result if isinstance(signal, Signal) else result.time_data


def compute_frequency_response(
    coefficients: FilterCoefficients, n_points: int = 4096
) -> FrequencyResponse:
    return frequency_response(coefficients, 1.0, n_points)


def compute_group_delay(
    coefficients: FilterCoefficients, n_points: int = 4096
) -> tuple[np.ndarray, np.ndarray]:
    return filter_group_delay(coefficients, 1.0, n_points)


def get_impulse_response(coefficients: FilterCoefficients, n_samples: int = 1024) -> Signal:
    return impulse_response(coefficients, n_samples)


def get_step_response(coefficients: FilterCoefficients, n_samples: int = 1024) -> Signal:
    return step_response(coefficients, n_samples)
