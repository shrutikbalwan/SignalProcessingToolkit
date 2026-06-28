from __future__ import annotations

import numpy as np
from scipy import signal as sp_signal
from scipy.ndimage import gaussian_filter1d

from src.models.signal import Signal


def spectral_subtraction(
    noisy_signal: Signal,
    noise_estimate: Signal | None = None,
    alpha: float = 2.0,
    beta: float = 0.01,
    window_size: int = 1024,
    hop_length: int | None = None,
) -> Signal:
    if hop_length is None:
        hop_length = window_size // 4

    data = noisy_signal.time_data
    n_samples = len(data)

    if noise_estimate is None:
        noise_frames = min(10, n_samples // window_size)
        noise_segment = data[: noise_frames * window_size]
        noise_spectrum = np.abs(sp_signal.stft(noise_segment, nperseg=window_size)[2])
        noise_psd = np.mean(noise_spectrum**2, axis=1)
    else:
        noise_segment = noise_estimate.time_data[:window_size]
        noise_spectrum = sp_signal.stft(noise_segment, nperseg=window_size)[2]
        noise_psd = np.abs(noise_spectrum) ** 2

    freqs, times, stft = sp_signal.stft(
        data, fs=noisy_signal.sampling_rate, nperseg=window_size, noverlap=window_size - hop_length
    )
    magnitude = np.abs(stft)
    phase = np.angle(stft)

    clean_magnitude = np.maximum(
        magnitude - alpha * np.sqrt(noise_psd[:, np.newaxis]), beta * magnitude
    )

    clean_stft = clean_magnitude * np.exp(1j * phase)
    _, clean_signal = sp_signal.istft(
        clean_stft,
        fs=noisy_signal.sampling_rate,
        nperseg=window_size,
        noverlap=window_size - hop_length,
    )

    clean_signal = clean_signal[:n_samples]

    return Signal(
        time_data=clean_signal,
        sampling_rate=noisy_signal.sampling_rate,
    )


def wiener_filter(
    noisy_signal: Signal,
    noise_signal: Signal | None = None,
    snr_estimate: float | None = None,
) -> Signal:
    data = noisy_signal.time_data

    if noise_signal is not None:
        noise_data = noise_signal.time_data[: len(data)]
        noise_psd = np.abs(sp_signal.stft(noise_data, nperseg=min(256, len(noise_data)))[2]) ** 2
        noise_psd = np.mean(noise_psd, axis=1)
    elif snr_estimate is not None:
        signal_psd = np.abs(sp_signal.stft(data, nperseg=min(256, len(data)))[2]) ** 2
        signal_psd = np.mean(signal_psd, axis=1)
        noise_psd = signal_psd / snr_estimate
    else:
        raise ValueError("Either noise_signal or snr_estimate must be provided")

    freqs, times, stft = sp_signal.stft(data, fs=noisy_signal.sampling_rate, nperseg=256)
    signal_psd = np.abs(stft) ** 2
    signal_psd_mean = np.mean(signal_psd, axis=1)

    wiener_gain = signal_psd_mean / (signal_psd_mean + noise_psd + 1e-10)
    wiener_gain = np.maximum(wiener_gain, 0.01)

    clean_stft = stft * wiener_gain[:, np.newaxis]
    _, clean_signal = sp_signal.istft(clean_stft, fs=noisy_signal.sampling_rate, nperseg=256)

    clean_signal = clean_signal[: len(data)]

    return Signal(
        time_data=clean_signal,
        sampling_rate=noisy_signal.sampling_rate,
    )


def median_filter(signal: Signal, window_size: int = 5) -> Signal:
    if window_size % 2 == 0:
        window_size += 1

    filtered = sp_signal.medfilt(signal.time_data, window_size)

    return Signal(
        time_data=filtered,
        sampling_rate=signal.sampling_rate,
    )


def adaptive_filter(
    noisy_signal: Signal,
    reference_signal: Signal,
    filter_length: int = 32,
    step_size: float = 0.01,
) -> Signal:
    data = noisy_signal.time_data
    ref = reference_signal.time_data[: len(data)]

    if len(ref) < len(data):
        ref = np.pad(ref, (0, len(data) - len(ref)))

    w = np.zeros(filter_length)
    output = np.zeros(len(data))
    error = np.zeros(len(data))

    for i in range(filter_length, len(data)):
        x = ref[i - filter_length : i][::-1]
        y = np.dot(w, x)
        output[i] = y
        e = data[i] - y
        error[i] = e
        w = w + 2 * step_size * e * x

    return Signal(
        time_data=output,
        sampling_rate=noisy_signal.sampling_rate,
    )


def kalman_filter(
    signal: Signal,
    process_noise: float = 1e-4,
    measurement_noise: float = 1e-2,
    initial_state: float = 0.0,
    initial_covariance: float = 1.0,
) -> Signal:
    data = signal.time_data
    n = len(data)

    x = initial_state
    P = initial_covariance  # noqa: N806
    Q = process_noise  # noqa: N806
    R = measurement_noise  # noqa: N806

    filtered = np.zeros(n)

    for i in range(n):
        x_pred = x
        P_pred = P + Q  # noqa: N806

        K = P_pred / (P_pred + R)  # noqa: N806
        x = x_pred + K * (data[i] - x_pred)
        P = (1 - K) * P_pred  # noqa: N806

        filtered[i] = x

    return Signal(
        time_data=filtered,
        sampling_rate=signal.sampling_rate,
    )


def gaussian_smooth(signal: Signal, sigma: float = 1.0) -> Signal:
    smoothed = gaussian_filter1d(signal.time_data, sigma=sigma)

    return Signal(
        time_data=smoothed,
        sampling_rate=signal.sampling_rate,
    )


def savitzky_golay_filter(signal: Signal, window_length: int = 11, polyorder: int = 3) -> Signal:
    if window_length % 2 == 0:
        window_length += 1
    if polyorder >= window_length:
        polyorder = window_length - 1

    filtered = sp_signal.savgol_filter(signal.time_data, window_length, polyorder)

    return Signal(
        time_data=filtered,
        sampling_rate=signal.sampling_rate,
    )
