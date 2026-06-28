from __future__ import annotations

import numpy as np
from scipy.fft import fft, fftfreq, rfft, rfftfreq
from scipy.signal import find_peaks

from src.models.fft_result import FFTResult, SpectrumPeak
from src.models.signal import Signal


def compute_fft(
    signal: Signal, n_fft: int | None = None, window: np.ndarray | None = None
) -> FFTResult:
    data = signal.time_data
    n = n_fft or len(data)

    if window is not None:
        if len(window) != len(data):
            raise ValueError("Window length must match signal length")
        data = data * window

    if len(data) < n:
        data = np.pad(data, (0, n - len(data)))
    elif len(data) > n:
        data = data[:n]

    spectrum = fft(data, n)
    frequencies = fftfreq(n, 1 / signal.sampling_rate)

    magnitude = np.abs(spectrum)
    phase = np.angle(spectrum)

    peaks = []
    if n > 0:
        peak_indices, properties = find_peaks(magnitude[: n // 2], height=0.1 * np.max(magnitude))
        for idx in peak_indices:
            peaks.append(
                SpectrumPeak(
                    frequency=float(frequencies[idx]),
                    magnitude=float(magnitude[idx]),
                    magnitude_db=float(20 * np.log10(max(magnitude[idx], 1e-10))),
                    phase=float(phase[idx]),
                    index=int(idx),
                )
            )

    return FFTResult(
        frequencies=frequencies,
        magnitude=magnitude,
        phase=phase,
        n_points=n,
        sampling_rate=signal.sampling_rate,
        peaks=peaks,
    )


def compute_rfft(
    signal: Signal, n_fft: int | None = None, window: np.ndarray | None = None
) -> FFTResult:
    data = signal.time_data
    n = n_fft or len(data)

    if window is not None:
        if len(window) != len(data):
            raise ValueError("Window length must match signal length")
        data = data * window

    if len(data) < n:
        data = np.pad(data, (0, n - len(data)))
    elif len(data) > n:
        data = data[:n]

    spectrum = rfft(data, n)
    frequencies = rfftfreq(n, 1 / signal.sampling_rate)

    magnitude = np.abs(spectrum)
    phase = np.angle(spectrum)

    peaks = []
    if len(magnitude) > 1:
        peak_indices, properties = find_peaks(magnitude[:-1], height=0.1 * np.max(magnitude[:-1]))
        for idx in peak_indices:
            peaks.append(
                SpectrumPeak(
                    frequency=float(frequencies[idx]),
                    magnitude=float(magnitude[idx]),
                    magnitude_db=float(20 * np.log10(max(magnitude[idx], 1e-10))),
                    phase=float(phase[idx]),
                    index=int(idx),
                )
            )

    return FFTResult(
        frequencies=frequencies,
        magnitude=magnitude,
        phase=phase,
        n_points=n,
        sampling_rate=signal.sampling_rate,
        peaks=peaks,
    )


def compute_power_spectrum(
    signal: Signal, n_fft: int | None = None, window: np.ndarray | None = None
) -> FFTResult:
    fft_result = compute_fft(signal, n_fft, window)
    fft_result.magnitude = fft_result.magnitude**2
    fft_result.magnitude_db = 10 * np.log10(np.maximum(fft_result.magnitude, 1e-10))
    return fft_result


def compute_psd(
    signal: Signal, n_fft: int | None = None, window: np.ndarray | None = None
) -> FFTResult:
    from scipy.signal import welch

    data = signal.time_data
    n = n_fft or len(data)

    if window is not None:
        if len(window) != len(data):
            raise ValueError("Window length must match signal length")

    freqs, psd = welch(data, fs=signal.sampling_rate, window=window, nperseg=n, nfft=n)

    magnitude = np.sqrt(psd)
    phase = np.zeros_like(psd)

    peaks = []
    if len(magnitude) > 1:
        peak_indices, properties = find_peaks(magnitude, height=0.1 * np.max(magnitude))
        for idx in peak_indices:
            peaks.append(
                SpectrumPeak(
                    frequency=float(freqs[idx]),
                    magnitude=float(magnitude[idx]),
                    magnitude_db=float(10 * np.log10(max(magnitude[idx] ** 2, 1e-10))),
                    phase=0.0,
                    index=int(idx),
                )
            )

    return FFTResult(
        frequencies=freqs,
        magnitude=magnitude,
        phase=phase,
        n_points=n,
        sampling_rate=signal.sampling_rate,
        peaks=peaks,
    )


def next_power_of_two(n: int) -> int:
    n -= 1
    n |= n >> 1
    n |= n >> 2
    n |= n >> 4
    n |= n >> 8
    n |= n >> 16
    return n + 1


def compute_spectrogram(
    signal: Signal,
    n_fft: int = 256,
    hop_length: int | None = None,
    window: np.ndarray | None = None,
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    if hop_length is None:
        hop_length = n_fft // 4

    if window is None:
        window = np.hanning(n_fft)

    data = signal.time_data
    n_frames = 1 + (len(data) - n_fft) // hop_length

    if n_frames <= 0:
        return np.array([]), np.array([]), np.array([])

    freqs = rfftfreq(n_fft, 1 / signal.sampling_rate)
    times = np.arange(n_frames) * hop_length / signal.sampling_rate
    spectrogram = np.zeros((len(freqs), n_frames))

    for i in range(n_frames):
        start = i * hop_length
        frame = data[start : start + n_fft]
        if len(frame) < n_fft:
            frame = np.pad(frame, (0, n_fft - len(frame)))

        windowed = frame * window
        spectrum = rfft(windowed, n_fft)
        spectrogram[:, i] = np.abs(spectrum)

    return freqs, times, spectrogram
