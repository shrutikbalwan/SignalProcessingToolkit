from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

import numpy as np
from scipy import integrate
from scipy import signal as sp_signal

from signal_processing_toolkit.dsp.fft import compute_fft, compute_welch_psd
from signal_processing_toolkit.models.signal import Signal


@dataclass(frozen=True, slots=True)
class CrossSpectrumResult:
    frequencies: np.ndarray
    values: np.ndarray
    sampling_rate: float
    parameters: dict[str, object]


@dataclass(frozen=True, slots=True)
class PeakEstimate:
    frequency: float
    magnitude: float
    bin_index: int
    bin_offset: float


@dataclass(frozen=True, slots=True)
class HarmonicMarker:
    harmonic: int
    frequency: float
    in_band: bool


def _spectral_compatibility(first: Signal, second: Signal) -> None:
    first.validate_compatibility(
        second, require_same_length=True, require_same_start=False, require_same_units=False
    )


def cross_spectral_density(
    first: Signal,
    second: Signal,
    *,
    window: str | tuple = "hann",
    segment_length: int = 256,
    overlap: int | None = None,
    fft_length: int | None = None,
    scaling: Literal["density", "spectrum"] = "density",
) -> CrossSpectrumResult:
    """Welch cross spectrum, in units²/Hz for density scaling."""
    _spectral_compatibility(first, second)
    if not 1 <= segment_length <= first.n_samples:
        raise ValueError("segment_length must be in [1, signal.n_samples]")
    frequencies, values = sp_signal.csd(
        first.time_data,
        second.time_data,
        fs=first.sampling_rate,
        window=window,
        nperseg=segment_length,
        noverlap=overlap,
        nfft=fft_length,
        detrend=False,
        return_onesided=not first.is_complex and not second.is_complex,
        scaling=scaling,
        axis=Signal.SAMPLE_AXIS,
    )
    parameters: dict[str, object] = {
        "window": window,
        "segment_length": segment_length,
        "overlap": overlap,
        "fft_length": fft_length or segment_length,
        "scaling": scaling,
    }
    return CrossSpectrumResult(frequencies, values, first.sampling_rate, parameters)


def magnitude_squared_coherence(
    first: Signal,
    second: Signal,
    *,
    window: str | tuple = "hann",
    segment_length: int = 256,
    overlap: int | None = None,
    fft_length: int | None = None,
) -> CrossSpectrumResult:
    """Magnitude-squared coherence ``|Pxy|² / (Pxx Pyy)``, bounded in [0, 1]."""
    _spectral_compatibility(first, second)
    if first.is_complex or second.is_complex:
        raise ValueError("SciPy coherence currently requires real-valued signals")
    frequencies, values = sp_signal.coherence(
        first.time_data,
        second.time_data,
        fs=first.sampling_rate,
        window=window,
        nperseg=segment_length,
        noverlap=overlap,
        nfft=fft_length,
        detrend=False,
        axis=Signal.SAMPLE_AXIS,
    )
    values = np.clip(values, 0.0, 1.0)
    return CrossSpectrumResult(
        frequencies,
        values,
        first.sampling_rate,
        {
            "window": window,
            "segment_length": segment_length,
            "overlap": overlap,
            "fft_length": fft_length or segment_length,
        },
    )


def band_power(
    signal: Signal,
    low_frequency: float,
    high_frequency: float,
    *,
    method: Literal["welch", "periodogram"] = "welch",
    segment_length: int | None = None,
    relative: bool = False,
) -> float | np.ndarray:
    """Integrate PSD over ``[low_frequency, high_frequency]`` using trapezoids."""
    if not 0 <= low_frequency < high_frequency <= signal.nyquist_frequency:
        raise ValueError("Band edges must satisfy 0 <= low < high <= Nyquist")
    if method == "welch":
        result = compute_welch_psd(signal, segment_length)
    elif method == "periodogram":
        from signal_processing_toolkit.dsp.fft import compute_periodogram

        result = compute_periodogram(signal)
    else:
        raise ValueError("method must be 'welch' or 'periodogram'")
    density = result.psd
    assert density is not None
    selected = (result.frequencies >= low_frequency) & (result.frequencies <= high_frequency)
    if np.count_nonzero(selected) < 2:
        raise ValueError("Band contains fewer than two PSD bins")
    power = integrate.trapezoid(density[selected], result.frequencies[selected], axis=0)
    if relative:
        total = integrate.trapezoid(density, result.frequencies, axis=0)
        power = np.divide(power, total, out=np.zeros_like(power), where=total > 0)
    return float(power) if np.ndim(power) == 0 else np.asarray(power)


def interpolate_peak(
    frequencies: np.ndarray,
    magnitude: np.ndarray,
    peak_index: int,
    *,
    logarithmic: bool = True,
) -> PeakEstimate:
    """Three-bin parabolic interpolation for a uniformly spaced spectrum."""
    frequencies = np.asarray(frequencies, dtype=float)
    magnitude = np.asarray(magnitude, dtype=float)
    if frequencies.ndim != 1 or magnitude.ndim != 1 or frequencies.size != magnitude.size:
        raise ValueError("frequencies and magnitude must be equal-length one-dimensional arrays")
    if not 0 <= peak_index < magnitude.size:
        raise IndexError("peak_index is outside the spectrum")
    if peak_index in (0, magnitude.size - 1):
        return PeakEstimate(
            float(frequencies[peak_index]), float(magnitude[peak_index]), peak_index, 0.0
        )
    values = magnitude[peak_index - 1 : peak_index + 2]
    if logarithmic:
        values = np.log(np.maximum(values, np.finfo(float).tiny))
    denominator = values[0] - 2 * values[1] + values[2]
    offset = 0.0 if np.isclose(denominator, 0.0) else 0.5 * (values[0] - values[2]) / denominator
    offset = float(np.clip(offset, -0.5, 0.5))
    spacing = frequencies[peak_index + 1] - frequencies[peak_index]
    frequency = frequencies[peak_index] + offset * spacing
    interpolated = values[1] - 0.25 * (values[0] - values[2]) * offset
    magnitude_value = np.exp(interpolated) if logarithmic else interpolated
    return PeakEstimate(float(frequency), float(magnitude_value), peak_index, offset)


def estimate_dominant_peak(signal: Signal, *, fft_length: int | None = None) -> PeakEstimate:
    result = compute_fft(signal, fft_length)
    magnitude = result.magnitude
    if magnitude.ndim != 1:
        raise ValueError("Dominant peak estimation requires a mono signal")
    start = 1 if magnitude.size > 1 else 0
    index = int(np.argmax(magnitude[start:]) + start)
    return interpolate_peak(result.frequencies, magnitude, index)


def harmonic_markers(
    fundamental_frequency: float, sampling_rate: float, max_harmonics: int = 10
) -> list[HarmonicMarker]:
    if fundamental_frequency <= 0 or not np.isfinite(fundamental_frequency):
        raise ValueError("fundamental_frequency must be finite and positive")
    if sampling_rate <= 0 or not np.isfinite(sampling_rate):
        raise ValueError("sampling_rate must be finite and positive")
    if max_harmonics < 1:
        raise ValueError("max_harmonics must be positive")
    nyquist = sampling_rate / 2
    return [
        HarmonicMarker(
            index, fundamental_frequency * index, fundamental_frequency * index <= nyquist
        )
        for index in range(1, max_harmonics + 1)
    ]
