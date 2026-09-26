from __future__ import annotations

import numpy as np

from signal_processing_toolkit.models.fft_result import FFTResult
from signal_processing_toolkit.models.signal import Signal


def magnitude_spectrum(fft_result: FFTResult) -> np.ndarray:
    return fft_result.magnitude


def power_spectrum(fft_result: FFTResult) -> np.ndarray:
    power = fft_result.power
    assert power is not None
    return power


def log_power_spectrum(fft_result: FFTResult) -> np.ndarray:
    return fft_result.to_db(power_spectrum(fft_result), power=True)


def phase_spectrum(fft_result: FFTResult) -> np.ndarray:
    return fft_result.phase


def group_delay(fft_result: FFTResult) -> np.ndarray:
    phase = fft_result.phase
    freqs = fft_result.frequencies

    if len(phase) < 2:
        return np.array([0.0])

    phase_diff = np.diff(np.unwrap(phase))
    freq_diff = np.diff(freqs)

    with np.errstate(divide="ignore", invalid="ignore"):
        delay = -phase_diff / np.where(freq_diff != 0, freq_diff, 1e-10)

    delay = np.append(delay, delay[-1] if len(delay) > 0 else 0.0)
    return delay


def instantaneous_frequency(fft_result: FFTResult) -> np.ndarray:
    phase = fft_result.phase
    freqs = fft_result.frequencies

    if len(phase) < 2:
        return freqs

    phase_diff = np.diff(np.unwrap(phase))
    freq_diff = np.diff(freqs)

    with np.errstate(divide="ignore", invalid="ignore"):
        inst_freq = freqs[:-1] + phase_diff / (
            2 * np.pi * np.where(freq_diff != 0, freq_diff, 1e-10)
        )

    inst_freq = np.append(inst_freq, inst_freq[-1] if len(inst_freq) > 0 else 0.0)
    return inst_freq


def spectral_centroid(fft_result: FFTResult) -> float:
    mask = (
        np.ones(fft_result.bin_count, dtype=bool)
        if fft_result.one_sided
        else fft_result.frequencies >= 0
    )
    freqs = fft_result.frequencies[mask]
    mag = fft_result.magnitude[mask]

    if np.sum(mag) == 0:
        return 0.0

    return float(np.sum(freqs * mag) / np.sum(mag))


def spectral_bandwidth(fft_result: FFTResult, centroid: float | None = None) -> float:
    mask = (
        np.ones(fft_result.bin_count, dtype=bool)
        if fft_result.one_sided
        else fft_result.frequencies >= 0
    )
    freqs = fft_result.frequencies[mask]
    mag = fft_result.magnitude[mask]

    if centroid is None:
        centroid = spectral_centroid(fft_result)

    if np.sum(mag) == 0:
        return 0.0

    bandwidth = np.sqrt(np.sum(mag * (freqs - centroid) ** 2) / np.sum(mag))
    return float(bandwidth)


def spectral_rolloff(fft_result: FFTResult, threshold: float = 0.85) -> float:
    mask = (
        np.ones(fft_result.bin_count, dtype=bool)
        if fft_result.one_sided
        else fft_result.frequencies >= 0
    )
    freqs = fft_result.frequencies[mask]
    mag = fft_result.magnitude[mask]

    total_power = np.sum(mag**2)
    if total_power == 0:
        return 0.0

    cumsum = np.cumsum(mag**2)
    rolloff_idx = np.where(cumsum >= threshold * total_power)[0]

    if len(rolloff_idx) == 0:
        return float(freqs[-1])

    return float(freqs[rolloff_idx[0]])


def spectral_flux(fft_result1: FFTResult, fft_result2: FFTResult) -> float:
    mag1 = fft_result1.positive_spectrum.magnitude
    mag2 = fft_result2.positive_spectrum.magnitude

    min_len = min(len(mag1), len(mag2))
    mag1, mag2 = mag1[:min_len], mag2[:min_len]

    flux = np.sum(np.maximum(0, mag2 - mag1) ** 2)
    return float(np.sqrt(flux))


def zero_crossing_rate(signal: Signal) -> float:
    data = signal.time_data
    zero_crossings = np.sum(np.diff(np.signbit(data)))
    return float(zero_crossings / len(data))
