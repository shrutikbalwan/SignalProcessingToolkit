"""Signal measurements.

Power is mean-square magnitude and ratios are reported in dB as ``10 log10``.
THD and THD+N are RMS ratios returned as percent. SINAD is dB. ENOB uses the
ideal full-scale sine relation ``(SINAD - 1.76) / 6.02`` bits. Crest factor is
peak magnitude divided by RMS magnitude (dimensionless).
"""

from __future__ import annotations

import numpy as np
from scipy import signal as sp_signal

from signal_processing_toolkit.models.signal import Signal


def _mean_power(data: np.ndarray) -> float:
    if data.size == 0:
        raise ValueError("Power is undefined for an empty signal")
    return float(np.mean(np.abs(data) ** 2))


def _ratio_db(numerator: float, denominator: float) -> float:
    if denominator == 0:
        return float("inf") if numerator > 0 else float("nan")
    if numerator == 0:
        return -float("inf")
    return float(10 * np.log10(numerator / denominator))


def snr_from_noise(signal: Signal, noise: Signal) -> float:
    """SNR dB = 10 log10(mean(|signal|²) / mean(|noise|²))."""
    signal.validate_compatibility(noise, require_same_length=True)
    return _ratio_db(_mean_power(signal.time_data), _mean_power(noise.time_data))


def snr_from_reference(measured: Signal, reference: Signal) -> float:
    """SNR dB using noise/error = ``measured - reference``."""
    measured.validate_compatibility(reference, require_same_length=True)
    return _ratio_db(
        _mean_power(reference.time_data), _mean_power(measured.time_data - reference.time_data)
    )


def snr(signal: Signal, noise: Signal | None = None, clean: Signal | None = None) -> float:
    if clean is not None and noise is not None:
        raise ValueError("Specify either noise or clean, not both")
    if clean is not None:
        return snr_from_reference(signal, clean)
    if noise is not None:
        return snr_from_noise(signal, noise)
    raise ValueError("SNR requires an explicit noise signal or clean reference")


def psnr(measured: Signal, reference: Signal, peak: float | None = None) -> float:
    """PSNR dB = 10 log10(peak² / mean(|measured-reference|²))."""
    measured.validate_compatibility(reference, require_same_length=True)
    error_power = _mean_power(measured.time_data - reference.time_data)
    reference_peak = float(np.max(np.abs(reference.time_data))) if peak is None else float(peak)
    if not np.isfinite(reference_peak) or reference_peak <= 0:
        raise ValueError("PSNR peak reference must be finite and positive")
    return _ratio_db(reference_peak**2, error_power)


def segmental_snr(measured: Signal, reference: Signal, frame_length: int = 256) -> float:
    measured.validate_compatibility(reference, require_same_length=True)
    if frame_length <= 0:
        raise ValueError("frame_length must be positive")
    values = []
    for start in range(0, measured.n_samples - frame_length + 1, max(1, frame_length // 2)):
        clean = reference.time_data[start : start + frame_length]
        error = measured.time_data[start : start + frame_length] - clean
        values.append(_ratio_db(_mean_power(clean), _mean_power(error)))
    if not values:
        raise ValueError("Signal is shorter than frame_length")
    return float(np.mean(values))


def noise_power(signal: Signal) -> float:
    """Mean-square noise power in squared signal units."""
    return _mean_power(signal.time_data)


def signal_power(signal: Signal) -> float:
    """Mean-square signal power in squared signal units."""
    return _mean_power(signal.time_data)


def noise_floor(signal: Signal, percentile: float = 10.0) -> float:
    if signal.n_samples == 0:
        raise ValueError("Noise floor is undefined for an empty signal")
    _, density = sp_signal.periodogram(
        signal.time_data, fs=signal.sampling_rate, axis=Signal.SAMPLE_AXIS
    )
    return float(np.percentile(density, percentile))


def dynamic_range(signal: Signal) -> float:
    """Peak-to-RMS ratio in dB."""
    factor = crest_factor(signal)
    return -float("inf") if factor == 0 else float(20 * np.log10(factor))


def crest_factor(signal: Signal) -> float:
    """Peak absolute sample divided by RMS; dimensionless."""
    if signal.n_samples == 0:
        raise ValueError("Crest factor is undefined for an empty signal")
    rms = np.sqrt(_mean_power(signal.time_data))
    return 0.0 if rms == 0 else float(np.max(np.abs(signal.time_data)) / rms)


def _tone_components(
    signal: Signal, fundamental_freq: float, max_harmonics: int
) -> tuple[np.ndarray, list[np.ndarray]]:
    if not signal.is_mono or signal.is_complex:
        raise ValueError("Distortion measurements require a real mono signal")
    if signal.n_samples < 3:
        raise ValueError("At least three samples are required")
    if not 0 < fundamental_freq < signal.nyquist_frequency:
        raise ValueError("fundamental_freq must be strictly between DC and Nyquist")
    if max_harmonics < 1:
        raise ValueError("max_harmonics must be at least 1")
    times = np.arange(signal.n_samples) / signal.sampling_rate
    frequencies = [
        fundamental_freq * harmonic
        for harmonic in range(1, max_harmonics + 1)
        if fundamental_freq * harmonic < signal.nyquist_frequency
    ]
    columns: list[np.ndarray] = [np.ones(signal.n_samples)]
    for frequency in frequencies:
        columns.extend(
            [np.cos(2 * np.pi * frequency * times), np.sin(2 * np.pi * frequency * times)]
        )
    design = np.column_stack(columns)
    coefficients, *_ = np.linalg.lstsq(design, signal.time_data, rcond=None)
    dc = coefficients[0] * np.ones(signal.n_samples)
    components = []
    for index in range(len(frequencies)):
        offset = 1 + 2 * index
        components.append(design[:, offset : offset + 2] @ coefficients[offset : offset + 2])
    return dc, components


def thd(signal: Signal, fundamental_freq: float, max_harmonics: int = 10) -> float:
    """THD percent = 100 sqrt(sum harmonic RMS²) / fundamental RMS."""
    _, components = _tone_components(signal, fundamental_freq, max_harmonics)
    fundamental_power = _mean_power(components[0])
    if np.isclose(fundamental_power, 0.0):
        raise ValueError("Fitted fundamental has zero power")
    harmonic_power = sum(_mean_power(component) for component in components[1:])
    return float(100 * np.sqrt(harmonic_power / fundamental_power))


def thdn(signal: Signal, fundamental_freq: float, max_harmonics: int = 10) -> float:
    """THD+N percent = 100 * residual RMS / fitted fundamental RMS.

    DC is excluded. ``max_harmonics`` is accepted for API compatibility; THD+N
    includes all residual noise and distortion below Nyquist.
    """
    del max_harmonics
    dc, components = _tone_components(signal, fundamental_freq, 1)
    residual = signal.time_data - dc - components[0]
    fundamental_power = _mean_power(components[0])
    if np.isclose(fundamental_power, 0.0):
        raise ValueError("Fitted fundamental has zero power")
    return float(100 * np.sqrt(_mean_power(residual) / fundamental_power))


def sinad(signal: Signal, fundamental_freq: float, max_harmonics: int = 10) -> float:
    """SINAD dB = 20 log10(fundamental RMS / residual RMS)."""
    ratio_percent = thdn(signal, fundamental_freq, max_harmonics)
    if ratio_percent == 0:
        return float("inf")
    return float(-20 * np.log10(ratio_percent / 100))


def enob(signal: Signal, fundamental_freq: float, max_harmonics: int = 10) -> float:
    """Effective bits for an ideal full-scale sine: (SINAD dB - 1.76) / 6.02."""
    return float((sinad(signal, fundamental_freq, max_harmonics) - 1.76) / 6.02)


def spectral_flatness(signal: Signal) -> float:
    if signal.is_complex:
        spectrum = np.abs(np.fft.fft(signal.time_data, axis=Signal.SAMPLE_AXIS)) ** 2
    else:
        spectrum = np.abs(np.fft.rfft(signal.time_data, axis=Signal.SAMPLE_AXIS)) ** 2
    geometric = np.exp(np.mean(np.log(np.maximum(spectrum, np.finfo(float).tiny))))
    arithmetic = np.mean(spectrum)
    return 0.0 if arithmetic == 0 else float(geometric / arithmetic)


def spectral_entropy(signal: Signal, num_bins: int = 256) -> float:
    del num_bins
    spectrum = np.abs(np.fft.fft(signal.time_data, axis=Signal.SAMPLE_AXIS)) ** 2
    total = np.sum(spectrum)
    if total == 0:
        return 0.0
    probability = spectrum.ravel() / total
    probability = probability[probability > 0]
    return float(-np.sum(probability * np.log2(probability)) / np.log2(spectrum.size))


def kurtosis(signal: Signal) -> float:
    from scipy.stats import kurtosis as sp_kurtosis

    return float(sp_kurtosis(signal.time_data, axis=None))


def skewness(signal: Signal) -> float:
    from scipy.stats import skew as sp_skew

    return float(sp_skew(signal.time_data, axis=None))
