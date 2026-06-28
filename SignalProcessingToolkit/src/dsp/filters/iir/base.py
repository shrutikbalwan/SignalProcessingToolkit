from __future__ import annotations

import numpy as np
from scipy import signal as sp_signal

from src.models.enums import DesignMethod, FilterType
from src.models.filter_design import FilterCoefficients, FilterDesign, FrequencyResponse
from src.models.signal import Signal


def design_iir_filter(design: FilterDesign) -> FilterCoefficients:
    nyquist = design.nyquist

    cutoff: list[float] | float
    if isinstance(design.cutoff_frequency, tuple):
        low, high = design.cutoff_frequency
        if low >= high:
            raise ValueError("Invalid bandpass/bandstop cutoff frequencies")
        low_norm = low / nyquist
        high_norm = high / nyquist

        if design.filter_type == FilterType.BANDPASS:
            cutoff = [low_norm, high_norm]
            btype = "bandpass"
        elif design.filter_type == FilterType.BANDSTOP:
            cutoff = [low_norm, high_norm]
            btype = "bandstop"
        else:
            raise ValueError(f"Invalid filter type for dual cutoff: {design.filter_type}")
    else:
        cutoff_norm = design.cutoff_frequency / nyquist
        if design.filter_type == FilterType.LOWPASS:
            cutoff = float(cutoff_norm)
            btype = "lowpass"
        elif design.filter_type == FilterType.HIGHPASS:
            cutoff = float(cutoff_norm)
            btype = "highpass"
        else:
            raise ValueError(f"Invalid filter type for single cutoff: {design.filter_type}")

    if design.design_method == DesignMethod.BUTTERWORTH:
        b, a = sp_signal.butter(
            design.order,
            cutoff,
            btype=btype,
            analog=False,
            fs=design.sampling_rate,
        )
    elif design.design_method == DesignMethod.CHEBYSHEV1:
        b, a = sp_signal.cheby1(
            design.order,
            design.passband_ripple,
            cutoff,
            btype=btype,
            analog=False,
            fs=design.sampling_rate,
        )
    elif design.design_method == DesignMethod.CHEBYSHEV2:
        b, a = sp_signal.cheby2(
            design.order,
            design.stopband_attenuation,
            cutoff,
            btype=btype,
            analog=False,
            fs=design.sampling_rate,
        )
    elif design.design_method == DesignMethod.ELLIPTIC:
        b, a = sp_signal.ellip(
            design.order,
            design.passband_ripple,
            design.stopband_attenuation,
            cutoff,
            btype=btype,
            analog=False,
            fs=design.sampling_rate,
        )
    else:
        b, a = sp_signal.butter(
            design.order,
            cutoff,
            btype=btype,
            analog=False,
            fs=design.sampling_rate,
        )

    return FilterCoefficients(b=b, a=a, order=design.order)


def apply_iir_filter(signal, coefficients: FilterCoefficients):
    from scipy.signal import filtfilt

    if hasattr(signal, "time_data"):
        data = signal.time_data
        fs = signal.sampling_rate
    else:
        data = signal
        fs = 1.0

    filtered = filtfilt(coefficients.b, coefficients.a, data)

    if hasattr(signal, "time_data"):
        from src.models.signal import Signal

        return Signal(
            time_data=filtered,
            sampling_rate=fs,
            frequency=signal.frequency,
            amplitude=signal.amplitude,
            phase=signal.phase,
        )
    return filtered  # type: ignore[return-value]


def compute_frequency_response(
    coefficients: FilterCoefficients, n_points: int = 4096
) -> FrequencyResponse:
    from scipy.signal import freqz

    w, h = freqz(coefficients.b, coefficients.a, worN=n_points, fs=1.0)

    frequencies = w
    magnitude = np.abs(h)
    phase = np.angle(h)
    20 * np.log10(np.maximum(magnitude, 1e-10))

    return FrequencyResponse(
        frequencies=frequencies,
        magnitude=magnitude,
        phase=phase,
    )


def compute_group_delay(coefficients: FilterCoefficients, n_points: int = 4096) -> tuple:
    from scipy.signal import group_delay

    w, gd = group_delay((coefficients.b, coefficients.a), w=n_points, whole=False, fs=1.0)
    return w, gd


def get_poles_zeros(coefficients: FilterCoefficients) -> tuple:
    poles = np.roots(coefficients.a)
    zeros = np.roots(coefficients.b)
    return poles, zeros


def is_stable(coefficients: FilterCoefficients) -> bool:
    poles, _ = get_poles_zeros(coefficients)
    return bool(np.all(np.abs(poles) < 1))


def get_impulse_response(coefficients: FilterCoefficients, n_samples: int = 1024) -> Signal:
    impulse = np.zeros(n_samples)
    impulse[0] = 1.0
    result = apply_iir_filter(impulse, coefficients)
    return result if isinstance(result, Signal) else Signal(time_data=result, sampling_rate=1.0)


def get_step_response(coefficients: FilterCoefficients, n_samples: int = 1024) -> Signal:
    step = np.ones(n_samples)
    result = apply_iir_filter(step, coefficients)
    return result if isinstance(result, Signal) else Signal(time_data=result, sampling_rate=1.0)
