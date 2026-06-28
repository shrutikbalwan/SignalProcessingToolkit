from __future__ import annotations

import numpy as np
from scipy import signal as sp_signal

from src.models.signal import Signal


def snr(signal: Signal, noise: Signal | None = None, clean: Signal | None = None) -> float:
    if clean is not None:
        signal_power = np.mean(clean.time_data**2)
        noise_power = np.mean((signal.time_data - clean.time_data) ** 2)
    elif noise is not None:
        signal_power = np.mean(signal.time_data**2)
        noise_power = np.mean(noise.time_data[: len(signal.time_data)] ** 2)
    else:
        signal_power = np.mean(signal.time_data**2)
        noise_power = np.var(signal.time_data)

    if noise_power == 0:
        return float("inf")

    return float(10 * np.log10(signal_power / noise_power))


def psnr(signal: Signal, clean: Signal) -> float:
    mse = np.mean((signal.time_data - clean.time_data) ** 2)
    if mse == 0:
        return float("inf")
    max_val = np.max(np.abs(clean.time_data))
    return float(20 * np.log10(max_val / np.sqrt(mse)))


def segmental_snr(signal: Signal, clean: Signal, frame_length: int = 256) -> float:
    data = signal.time_data
    ref = clean.time_data
    n = len(data)

    snr_values = []
    for i in range(0, n - frame_length, frame_length // 2):
        frame_s = data[i : i + frame_length]
        frame_r = ref[i : i + frame_length]

        signal_power = np.mean(frame_r**2)
        noise_power = np.mean((frame_s - frame_r) ** 2)

        if noise_power > 0 and signal_power > 0:
            snr_values.append(10 * np.log10(signal_power / noise_power))

    return float(np.mean(snr_values)) if snr_values else 0.0


def noise_power(signal: Signal) -> float:
    return float(np.mean(signal.time_data**2))


def signal_power(signal: Signal) -> float:
    return float(np.mean(signal.time_data**2))


def noise_floor(signal: Signal, percentile: float = 10.0) -> float:
    magnitude = np.abs(sp_signal.stft(signal.time_data, nperseg=min(256, len(signal.time_data)))[2])
    return float(np.percentile(magnitude, percentile))


def dynamic_range(signal: Signal) -> float:
    data = signal.time_data
    max_val = np.max(np.abs(data))
    rms_val = np.sqrt(np.mean(data**2))
    if rms_val == 0:
        return float("inf")
    return float(20 * np.log10(max_val / rms_val))


def crest_factor(signal: Signal) -> float:
    data = signal.time_data
    peak = np.max(np.abs(data))
    rms = np.sqrt(np.mean(data**2))
    if rms == 0:
        return 0.0
    return float(peak / rms)


def thd(signal: Signal, fundamental_freq: float, max_harmonics: int = 10) -> float:
    from scipy.fft import rfft, rfftfreq

    data = signal.time_data
    n = len(data)

    spectrum = np.abs(rfft(data))
    freqs = rfftfreq(n, 1 / signal.sampling_rate)

    fund_idx = np.argmin(np.abs(freqs - fundamental_freq))
    fund_mag = spectrum[fund_idx]

    harmonic_power = 0
    for h in range(2, max_harmonics + 1):
        h_freq = fundamental_freq * h
        h_idx = np.argmin(np.abs(freqs - h_freq))
        if h_idx < len(spectrum):
            harmonic_power += spectrum[h_idx] ** 2

    if fund_mag == 0:
        return 0.0

    return float(np.sqrt(harmonic_power) / fund_mag * 100)


def thdn(signal: Signal, fundamental_freq: float, max_harmonics: int = 10) -> float:
    from scipy.fft import rfft, rfftfreq

    data = signal.time_data
    n = len(data)

    spectrum = np.abs(rfft(data))
    freqs = rfftfreq(n, 1 / signal.sampling_rate)

    fund_idx = np.argmin(np.abs(freqs - fundamental_freq))
    fund_mag = spectrum[fund_idx]

    total_power = np.sum(spectrum**2)
    harmonic_power = 0
    for h in range(2, max_harmonics + 1):
        h_freq = fundamental_freq * h
        h_idx = np.argmin(np.abs(freqs - h_freq))
        if h_idx < len(spectrum):
            harmonic_power += spectrum[h_idx] ** 2

    noise_power = total_power - fund_mag**2 - harmonic_power
    noise_power = max(noise_power, 0)

    if fund_mag == 0:
        return 0.0

    return float(np.sqrt(noise_power + harmonic_power) / fund_mag * 100)


def sinad(signal: Signal, fundamental_freq: float, max_harmonics: int = 10) -> float:
    from scipy.fft import rfft, rfftfreq

    data = signal.time_data
    n = len(data)

    spectrum = np.abs(rfft(data))
    freqs = rfftfreq(n, 1 / signal.sampling_rate)

    fund_idx = np.argmin(np.abs(freqs - fundamental_freq))
    fund_mag = spectrum[fund_idx]

    total_power = np.sum(spectrum**2)
    noise_dist_power = total_power - fund_mag**2

    if fund_mag == 0:
        return -float("inf")

    return float(10 * np.log10(fund_mag**2 / max(noise_dist_power, 1e-10)))


def enob(signal: Signal, fundamental_freq: float, max_harmonics: int = 10) -> float:
    sinad_val = sinad(signal, fundamental_freq, max_harmonics)
    if sinad_val <= 0:
        return 0.0
    return float((sinad_val - 1.76) / 6.02)


def spectral_flatness(signal: Signal) -> float:
    from scipy.fft import rfft

    data = signal.time_data
    spectrum = np.abs(rfft(data))

    geo_mean = np.exp(np.mean(np.log(np.maximum(spectrum, 1e-10))))
    arith_mean = np.mean(spectrum)

    if arith_mean == 0:
        return 0.0

    return float(geo_mean / arith_mean)


def spectral_entropy(signal: Signal, num_bins: int = 256) -> float:
    from scipy.fft import rfft

    data = signal.time_data
    spectrum = np.abs(rfft(data))

    hist, _ = np.histogram(spectrum, bins=num_bins, density=True)
    hist = hist[hist > 0]

    entropy = -np.sum(hist * np.log2(hist))
    max_entropy = np.log2(num_bins)

    return float(entropy / max_entropy) if max_entropy > 0 else 0.0


def kurtosis(signal: Signal) -> float:
    from scipy.stats import kurtosis as sp_kurtosis

    return float(sp_kurtosis(signal.time_data))


def skewness(signal: Signal) -> float:
    from scipy.stats import skew as sp_skew

    return float(sp_skew(signal.time_data))
