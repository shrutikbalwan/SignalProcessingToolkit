from __future__ import annotations

import numpy as np
from scipy.signal import firwin, firwin2, kaiserord, remez

from src.models.enums import FilterType
from src.models.filter_design import FilterCoefficients, FilterDesign, FrequencyResponse
from src.models.signal import Signal


def design_fir_filter(design: FilterDesign) -> FilterCoefficients:
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
            pass_zero = False
        elif design.filter_type == FilterType.BANDSTOP:
            cutoff = [low_norm, high_norm]
            pass_zero = True
        else:
            raise ValueError(f"Invalid filter type for dual cutoff: {design.filter_type}")
    else:
        cutoff_norm = design.cutoff_frequency / nyquist
        if design.filter_type == FilterType.LOWPASS:
            cutoff = float(cutoff_norm)
            pass_zero = True
        elif design.filter_type == FilterType.HIGHPASS:
            cutoff = float(cutoff_norm)
            pass_zero = False
        else:
            raise ValueError(f"Invalid filter type for single cutoff: {design.filter_type}")

    if design.design_method.value == "window":
        window = _get_window(design)
        b = firwin(
            design.order + 1,
            cutoff,
            window=window,
            pass_zero=pass_zero,
            fs=design.sampling_rate,
        )
    elif design.design_method.value == "kaiser":
        b = _design_kaiser_fir(design, cutoff, pass_zero)
    elif design.design_method.value == "equiripple":
        b = _design_equiripple_fir(design, cutoff, pass_zero)
    elif design.design_method.value == "least_squares":
        b = _design_least_squares_fir(design, cutoff, pass_zero)
    else:
        window = _get_window(design)
        b = firwin(
            design.order + 1,
            cutoff,
            window=window,
            pass_zero=pass_zero,
            fs=design.sampling_rate,
        )

    return FilterCoefficients(b=b, a=np.array([1.0]), order=design.order)


def _get_window(design: FilterDesign) -> str | tuple:
    if hasattr(design, "window_type") and design.window_type:
        return str(design.window_type.value)
    return "hamming"


def _design_kaiser_fir(
    design: FilterDesign, cutoff: list[float] | float, pass_zero: bool
) -> np.ndarray:
    beta, order = kaiserord(
        ripple=design.passband_ripple,
        width=design.stopband_attenuation,
    )
    actual_order = max(order, design.order)
    b: np.ndarray = firwin(
        actual_order + 1,
        cutoff,
        window=("kaiser", beta),
        pass_zero=pass_zero,
        fs=design.sampling_rate,
    )
    return b


def _design_equiripple_fir(
    design: FilterDesign, cutoff: list[float] | float, pass_zero: bool
) -> np.ndarray:
    nyquist = design.nyquist

    if isinstance(cutoff, list):
        bands = [0, cutoff[0], cutoff[1], nyquist]
        if pass_zero:
            desired = [1, 0, 1]
        else:
            desired = [0, 1, 0]
    else:
        bands = [0, cutoff, nyquist]
        if pass_zero:
            desired = [1, 0]
        else:
            desired = [0, 1]

    weights = [1, 10 ** (design.stopband_attenuation / 20)]

    b: np.ndarray = remez(
        design.order + 1,
        bands,
        desired,
        weight=weights,
        fs=design.sampling_rate,
    )
    return b


def _design_least_squares_fir(
    design: FilterDesign, cutoff: list[float] | float, pass_zero: bool
) -> np.ndarray:
    nyquist = design.nyquist

    if isinstance(cutoff, list):
        freq = [0, cutoff[0], cutoff[1], nyquist]
        if pass_zero:
            gain = [1, 1, 0, 0]
        else:
            gain = [0, 0, 1, 1]
    else:
        freq = [0, cutoff, nyquist]
        if pass_zero:
            gain = [1, 0]
        else:
            gain = [0, 1]

    b_result: np.ndarray = firwin2(
        design.order + 1,
        freq,
        gain,
        fs=design.sampling_rate,
    )
    return b_result


def apply_fir_filter(
    signal: Signal | np.ndarray, coefficients: FilterCoefficients
) -> Signal | np.ndarray:
    from scipy.signal import filtfilt

    from src.models.signal import Signal

    if isinstance(signal, Signal):
        data = signal.time_data
        fs = signal.sampling_rate
        result = Signal(
            time_data=filtfilt(coefficients.b, coefficients.a, data),
            sampling_rate=fs,
            frequency=signal.frequency,
            amplitude=signal.amplitude,
            phase=signal.phase,
        )
        return result
    else:
        data = signal
        fs = 1.0
        filtered = filtfilt(coefficients.b, coefficients.a, data)
        return filtered  # type: ignore[no-any-return]


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


def compute_group_delay(
    coefficients: FilterCoefficients, n_points: int = 4096
) -> tuple[np.ndarray, np.ndarray]:
    from scipy.signal import group_delay

    w, gd = group_delay((coefficients.b, coefficients.a), w=n_points, whole=False, fs=1.0)
    return w, gd


def get_impulse_response(coefficients: FilterCoefficients, n_samples: int = 1024) -> Signal:
    impulse = np.zeros(n_samples)
    impulse[0] = 1.0
    result = apply_fir_filter(impulse, coefficients)
    return result if isinstance(result, Signal) else Signal(time_data=result, sampling_rate=1.0)


def get_step_response(coefficients: FilterCoefficients, n_samples: int = 1024) -> Signal:
    step = np.ones(n_samples)
    result = apply_fir_filter(step, coefficients)
    return result if isinstance(result, Signal) else Signal(time_data=result, sampling_rate=1.0)
