from __future__ import annotations

import numpy as np

from src.models.signal import Signal


def check_aliasing(signal: Signal, sampling_rate: float) -> dict:
    from scipy.fft import fft, fftfreq

    n = signal.length
    spectrum = np.abs(fft(signal.time_data))
    freqs = fftfreq(n, 1 / signal.sampling_rate)

    nyquist = sampling_rate / 2
    positive_freqs = freqs[: n // 2]
    positive_spectrum = spectrum[: n // 2]

    above_nyquist = positive_freqs > nyquist
    aliased_energy = np.sum(positive_spectrum[above_nyquist] ** 2)
    total_energy = np.sum(positive_spectrum**2)

    aliasing_ratio = aliased_energy / total_energy if total_energy > 0 else 0

    max_aliased_freq = (
        positive_freqs[above_nyquist][np.argmax(positive_spectrum[above_nyquist])]
        if np.any(above_nyquist)
        else 0
    )

    return {
        "aliasing_detected": aliasing_ratio > 0.01,
        "aliasing_ratio": aliasing_ratio,
        "max_aliased_frequency": max_aliased_freq,
        "nyquist_frequency": nyquist,
        "signal_bandwidth": float(
            np.max(positive_freqs[positive_spectrum > 0.01 * np.max(positive_spectrum)])
        ),
    }


def demonstrate_aliasing(
    original_freq: float,
    sampling_rate: float,
    duration: float = 1.0,
) -> tuple[Signal, Signal, dict]:
    t = np.linspace(0, duration, int(sampling_rate * duration), endpoint=False)
    original = np.sin(2 * np.pi * original_freq * t)

    aliased_freq = original_freq % sampling_rate
    if aliased_freq > sampling_rate / 2:
        aliased_freq = sampling_rate - aliased_freq

    aliased = np.sin(2 * np.pi * aliased_freq * t)

    original_signal = Signal(
        time_data=original,
        sampling_rate=sampling_rate,
        frequency=original_freq,
    )

    aliased_signal = Signal(
        time_data=aliased,
        sampling_rate=sampling_rate,
        frequency=aliased_freq,
    )

    info = {
        "original_frequency": original_freq,
        "sampling_rate": sampling_rate,
        "nyquist_frequency": sampling_rate / 2,
        "aliased_frequency": aliased_freq,
        "is_aliased": original_freq > sampling_rate / 2,
    }

    return original_signal, aliased_signal, info


def anti_aliasing_filter(signal: Signal, cutoff_freq: float | None = None) -> Signal:
    if cutoff_freq is None:
        cutoff_freq = signal.nyquist_frequency * 0.9

    from scipy import signal as sp_signal

    nyquist = signal.sampling_rate / 2
    normalized_cutoff = cutoff_freq / nyquist

    b, a = sp_signal.butter(8, normalized_cutoff, btype="lowpass")
    filtered = sp_signal.filtfilt(b, a, signal.time_data)

    return Signal(
        time_data=filtered,
        sampling_rate=signal.sampling_rate,
        frequency=signal.frequency,
    )


def calculate_min_sampling_rate(signal: Signal, oversampling_factor: float = 2.5) -> float:
    from scipy.fft import fft, fftfreq

    n = signal.length
    spectrum = np.abs(fft(signal.time_data))
    freqs = fftfreq(n, 1 / signal.sampling_rate)

    positive_freqs = freqs[: n // 2]
    positive_spectrum = spectrum[: n // 2]

    threshold = 0.001 * np.max(positive_spectrum)
    significant_freqs = positive_freqs[positive_spectrum > threshold]

    if len(significant_freqs) == 0:
        return signal.sampling_rate

    max_significant_freq = float(np.max(significant_freqs))
    min_rate = max_significant_freq * oversampling_factor
    return max(min_rate, signal.sampling_rate * 0.1)
