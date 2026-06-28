from __future__ import annotations

import numpy as np
from scipy.fft import ifft, irfft

from src.models.fft_result import FFTResult
from src.models.signal import Signal


def inverse_fft(fft_result: FFTResult) -> Signal:
    magnitude = fft_result.magnitude
    phase = fft_result.phase

    spectrum = magnitude * np.exp(1j * phase)
    time_data = np.real(ifft(spectrum))

    return Signal(
        time_data=time_data,
        sampling_rate=fft_result.sampling_rate,
    )


def inverse_rfft(fft_result: FFTResult) -> Signal:
    magnitude = fft_result.magnitude
    phase = fft_result.phase

    spectrum = magnitude * np.exp(1j * phase)
    time_data = irfft(spectrum)

    return Signal(
        time_data=time_data,
        sampling_rate=fft_result.sampling_rate,
    )


def synthesize_from_peaks(
    peaks: list,
    n_samples: int,
    sampling_rate: float,
) -> Signal:
    t = np.arange(n_samples) / sampling_rate
    signal_data = np.zeros(n_samples)

    for peak in peaks:
        signal_data += peak.magnitude * np.cos(2 * np.pi * peak.frequency * t + peak.phase)

    return Signal(
        time_data=signal_data,
        sampling_rate=sampling_rate,
    )


def overlap_add_istft(
    spectrogram: np.ndarray,
    hop_length: int,
    n_fft: int,
    window: np.ndarray | None = None,
) -> Signal:
    if window is None:
        window = np.hanning(n_fft)

    n_frames = spectrogram.shape[1]
    n_samples = (n_frames - 1) * hop_length + n_fft
    signal_data = np.zeros(n_samples)
    window_sum = np.zeros(n_samples)

    for i in range(n_frames):
        frame_spectrum = spectrogram[:, i]

        full_spectrum = np.zeros(n_fft, dtype=complex)
        full_spectrum[: len(frame_spectrum)] = frame_spectrum
        full_spectrum[-len(frame_spectrum) + 1 :] = np.conj(frame_spectrum[:0:-1])

        frame = np.real(ifft(full_spectrum))
        frame = frame * window

        start = i * hop_length
        end = start + n_fft

        if end <= n_samples:
            signal_data[start:end] += frame
            window_sum[start:end] += window**2
        else:
            signal_data[start:] += frame[: n_samples - start]
            window_sum[start:] += (window**2)[: n_samples - start]

    with np.errstate(divide="ignore", invalid="ignore"):
        signal_data = np.where(window_sum > 1e-10, signal_data / window_sum, 0)

    return Signal(
        time_data=signal_data,
        sampling_rate=44100.0,
    )


def griffin_lim(
    magnitude_spectrogram: np.ndarray,
    n_fft: int,
    hop_length: int,
    n_iter: int = 32,
    window: np.ndarray | None = None,
    random_state: int | None = None,
) -> Signal:
    if window is None:
        window = np.hanning(n_fft)

    if random_state is not None:
        np.random.seed(random_state)

    phase = np.random.uniform(-np.pi, np.pi, magnitude_spectrogram.shape)

    for _ in range(n_iter):
        complex_spec = magnitude_spectrogram * np.exp(1j * phase)

        n_frames = complex_spec.shape[1]
        n_samples = (n_frames - 1) * hop_length + n_fft
        signal_est = np.zeros(n_samples)

        for i in range(n_frames):
            frame_spectrum = complex_spec[:, i]

            full_spectrum = np.zeros(n_fft, dtype=complex)
            full_spectrum[: len(frame_spectrum)] = frame_spectrum
            full_spectrum[-len(frame_spectrum) + 1 :] = np.conj(frame_spectrum[:0:-1])

            frame = np.real(ifft(full_spectrum))
            frame = frame * window

            start = i * hop_length
            end = min(start + n_fft, n_samples)
            signal_est[start:end] += frame[: end - start]

        stft_signal = np.zeros_like(complex_spec)
        for i in range(n_frames):
            start = i * hop_length
            end = min(start + n_fft, n_samples)
            frame = signal_est[start:end]
            if len(frame) < n_fft:
                frame = np.pad(frame, (0, n_fft - len(frame)))
            windowed = frame * window
            spectrum = np.fft.rfft(windowed, n_fft)
            stft_signal[:, i] = spectrum

        phase = np.angle(stft_signal)

    n_frames = complex_spec.shape[1]
    n_samples = (n_frames - 1) * hop_length + n_fft
    signal_data = np.zeros(n_samples)
    window_sum = np.zeros(n_samples)

    for i in range(n_frames):
        frame_spectrum = complex_spec[:, i]

        full_spectrum = np.zeros(n_fft, dtype=complex)
        full_spectrum[: len(frame_spectrum)] = frame_spectrum
        full_spectrum[-len(frame_spectrum) + 1 :] = np.conj(frame_spectrum[:0:-1])

        frame = np.real(ifft(full_spectrum))
        frame = frame * window

        start = i * hop_length
        end = min(start + n_fft, n_samples)
        signal_data[start:end] += frame[: end - start]
        window_sum[start:end] += (window**2)[: end - start]

    with np.errstate(divide="ignore", invalid="ignore"):
        signal_data = np.where(window_sum > 1e-10, signal_data / window_sum, 0)

    return Signal(
        time_data=signal_data,
        sampling_rate=n_fft * 1000 // hop_length,
    )
