from __future__ import annotations

import warnings

import numpy as np
from scipy import signal as sp_signal
from scipy.fft import ifft, irfft

from signal_processing_toolkit.models.fft_result import FFTResult
from signal_processing_toolkit.models.signal import Signal


def inverse_fft(fft_result: FFTResult) -> Signal:
    if not fft_result.invertible:
        raise ValueError("This spectral estimate does not contain an invertible FFT")
    spectrum = fft_result.spectrum
    if fft_result.one_sided:
        time_data = irfft(spectrum, n=fft_result.n_points, axis=Signal.SAMPLE_AXIS)
    else:
        time_data = ifft(spectrum, n=fft_result.n_points, axis=Signal.SAMPLE_AXIS)
    if np.all(np.abs(time_data.imag) < 1e-12):
        time_data = time_data.real

    return Signal(
        time_data=time_data,
        sampling_rate=fft_result.sampling_rate,
    )


def inverse_rfft(fft_result: FFTResult) -> Signal:
    if not fft_result.invertible:
        raise ValueError("This spectral estimate does not contain an invertible FFT")
    if not fft_result.one_sided:
        raise ValueError("inverse_rfft requires a one-sided FFT result")
    time_data = irfft(fft_result.spectrum, n=fft_result.n_points, axis=Signal.SAMPLE_AXIS)

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
    sampling_rate: float = 44100.0,
) -> Signal:
    """Adapt a legacy array call to the canonical configurable ISTFT."""
    from signal_processing_toolkit.dsp.analysis.time_frequency import (
        STFTConfig,
        STFTResult,
        istft,
    )

    warnings.warn(
        "overlap_add_istft is deprecated; retain the STFTResult and call dsp.analysis.istft",
        DeprecationWarning,
        stacklevel=2,
    )
    if n_fft < 1 or not 1 <= hop_length <= n_fft:
        raise ValueError("Require n_fft > 0 and hop_length in [1, n_fft]")
    if not np.isfinite(sampling_rate) or sampling_rate <= 0:
        raise ValueError("sampling_rate must be finite and positive")
    values = np.asarray(spectrogram)
    if values.ndim not in (2, 3):
        raise ValueError("spectrogram must have shape (frequency, frame[, channel])")
    config = STFTConfig(
        window="hann" if window is None else np.asarray(window, dtype=float),
        window_length=n_fft,
        overlap=n_fft - hop_length,
        fft_length=n_fft,
        boundary=None,
        padded=False,
    )
    frame_count = values.shape[1]
    length = 0 if frame_count == 0 else (frame_count - 1) * hop_length + n_fft
    result = STFTResult(
        np.fft.rfftfreq(n_fft, 1 / sampling_rate),
        np.arange(frame_count) * hop_length / sampling_rate,
        values,
        sampling_rate,
        config,
        length,
    )
    return istft(result, length=length)


def griffin_lim(
    magnitude_spectrogram: np.ndarray,
    n_fft: int,
    hop_length: int,
    n_iter: int = 32,
    window: np.ndarray | None = None,
    random_state: int | None = None,
    sampling_rate: float = 44100.0,
) -> Signal:
    """Estimate phase from magnitude while preserving an explicit physical rate."""
    if n_fft < 1 or not 1 <= hop_length <= n_fft:
        raise ValueError("Require n_fft > 0 and hop_length in [1, n_fft]")
    if n_iter < 1:
        raise ValueError("n_iter must be positive")
    if not np.isfinite(sampling_rate) or sampling_rate <= 0:
        raise ValueError("sampling_rate must be finite and positive")
    magnitude = np.asarray(magnitude_spectrogram, dtype=float)
    if magnitude.ndim != 2 or magnitude.shape[0] != n_fft // 2 + 1:
        raise ValueError("magnitude_spectrogram must have shape (n_fft // 2 + 1, frames)")
    analysis_window: str | np.ndarray = "hann" if window is None else np.asarray(window)
    rng = np.random.default_rng(random_state)
    phase = rng.uniform(-np.pi, np.pi, magnitude.shape)
    estimate = np.empty(0)
    for _ in range(n_iter):
        complex_spectrum = magnitude * np.exp(1j * phase)
        _, estimate = sp_signal.istft(
            complex_spectrum,
            fs=sampling_rate,
            window=analysis_window,
            nperseg=n_fft,
            noverlap=n_fft - hop_length,
            nfft=n_fft,
            input_onesided=True,
            boundary=False,
            scaling="spectrum",
        )
        _, _, rebuilt = sp_signal.stft(
            estimate,
            fs=sampling_rate,
            window=analysis_window,
            nperseg=n_fft,
            noverlap=n_fft - hop_length,
            nfft=n_fft,
            boundary=None,
            padded=False,
            scaling="spectrum",
        )
        common = min(rebuilt.shape[1], magnitude.shape[1])
        phase[:, :common] = np.angle(rebuilt[:, :common])
    return Signal(np.asarray(estimate), sampling_rate)
