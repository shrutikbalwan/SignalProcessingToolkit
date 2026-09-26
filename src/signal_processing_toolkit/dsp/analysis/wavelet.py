from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from scipy import signal as sp_signal

from signal_processing_toolkit.models.signal import Signal


@dataclass(frozen=True, slots=True)
class WaveletResult:
    times: np.ndarray
    frequencies: np.ndarray
    coefficients: np.ndarray
    scales: np.ndarray
    parameters: dict[str, object]

    @property
    def scalogram(self) -> np.ndarray:
        """Wavelet energy ``|coefficient|²``."""
        return np.abs(self.coefficients) ** 2


def _morlet(scale: float, omega0: float) -> np.ndarray:
    half_width = max(4, int(np.ceil(8 * scale)))
    time = np.arange(-half_width, half_width + 1, dtype=float)
    normalized = time / scale
    wavelet = np.pi ** (-0.25) * np.exp(1j * omega0 * normalized) * np.exp(-0.5 * normalized**2)
    return np.asarray(wavelet / np.sqrt(scale), dtype=complex)


def continuous_wavelet_transform(
    signal: Signal,
    *,
    frequencies: np.ndarray | None = None,
    scales: np.ndarray | None = None,
    omega0: float = 6.0,
) -> WaveletResult:
    """Complex Morlet CWT.

    Exactly one of ``frequencies`` or ``scales`` may be supplied. Their relation
    is ``frequency = omega0 * sampling_rate / (2*pi*scale)``.
    """
    if signal.n_samples == 0:
        raise ValueError("CWT is undefined for empty input")
    if omega0 <= 0 or not np.isfinite(omega0):
        raise ValueError("omega0 must be finite and positive")
    if frequencies is not None and scales is not None:
        raise ValueError("Specify frequencies or scales, not both")
    if frequencies is None and scales is None:
        lower = max(signal.sampling_rate / signal.n_samples, 1e-6)
        frequencies = np.geomspace(lower, signal.nyquist_frequency * 0.95, 64)
    if frequencies is not None:
        frequencies = np.asarray(frequencies, dtype=float)
        if (
            frequencies.ndim != 1
            or np.any(frequencies <= 0)
            or np.any(frequencies > signal.nyquist_frequency)
        ):
            raise ValueError("frequencies must be a 1-D array in (0, Nyquist]")
        scales = omega0 * signal.sampling_rate / (2 * np.pi * frequencies)
    else:
        scales = np.asarray(scales, dtype=float)
        if scales.ndim != 1 or np.any(scales <= 0):
            raise ValueError("scales must be a positive 1-D array")
        frequencies = omega0 * signal.sampling_rate / (2 * np.pi * scales)
    channel_data = signal.time_data[:, np.newaxis] if signal.is_mono else signal.time_data
    output = np.empty((len(scales), signal.n_samples, signal.n_channels), dtype=complex)
    for scale_index, scale in enumerate(scales):
        kernel = np.conj(_morlet(float(scale), omega0)[::-1])
        for channel in range(signal.n_channels):
            output[scale_index, :, channel] = sp_signal.fftconvolve(
                channel_data[:, channel], kernel, mode="same"
            )
    coefficients = output[:, :, 0] if signal.is_mono else output
    return WaveletResult(
        signal.time_vector,
        frequencies,
        coefficients,
        scales,
        {"wavelet": "complex_morlet", "omega0": omega0, "n_scales": len(scales)},
    )
