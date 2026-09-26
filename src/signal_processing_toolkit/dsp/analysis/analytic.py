from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from scipy import signal as sp_signal

from signal_processing_toolkit.dsp.fft import compute_fft
from signal_processing_toolkit.models.fft_result import FFTResult
from signal_processing_toolkit.models.signal import Signal


@dataclass(frozen=True, slots=True)
class CepstrumResult:
    quefrencies: np.ndarray
    values: np.ndarray
    parameters: dict[str, object]


def analytic_signal(signal: Signal) -> Signal:
    """Return the Hilbert analytic signal along the sample axis."""
    if signal.is_complex:
        raise ValueError("Hilbert analytic signal requires real-valued input")
    if signal.n_samples == 0:
        raise ValueError("Analytic signal is undefined for empty input")
    values = sp_signal.hilbert(signal.time_data, axis=Signal.SAMPLE_AXIS)
    return signal.updated(time_data=values, operation="hilbert_analytic_signal")


def signal_envelope(signal: Signal) -> Signal:
    analytic = signal if signal.is_complex else analytic_signal(signal)
    return signal.updated(time_data=np.abs(analytic.time_data), operation="signal_envelope")


def instantaneous_phase(signal: Signal, *, unwrap: bool = True) -> Signal:
    analytic = signal if signal.is_complex else analytic_signal(signal)
    phase = np.angle(analytic.time_data)
    if unwrap:
        phase = np.unwrap(phase, axis=Signal.SAMPLE_AXIS)
    return signal.updated(
        time_data=phase, units=("rad",) * signal.n_channels, operation="instantaneous_phase"
    )


def instantaneous_frequency(signal: Signal) -> Signal:
    """Phase derivative in hertz using a second-order central gradient."""
    phase = instantaneous_phase(signal).time_data
    frequency = np.gradient(phase, axis=Signal.SAMPLE_AXIS) * signal.sampling_rate / (2 * np.pi)
    return signal.updated(
        time_data=frequency, units=("Hz",) * signal.n_channels, operation="instantaneous_frequency"
    )


def real_cepstrum(signal: Signal, *, floor: float = 1e-15) -> CepstrumResult:
    """Real cepstrum ``real(ifft(log(max(abs(fft(x)), floor))))``."""
    if floor <= 0 or not np.isfinite(floor):
        raise ValueError("floor must be finite and positive")
    if signal.n_samples == 0:
        raise ValueError("Cepstrum is undefined for empty input")
    spectrum = np.fft.fft(signal.time_data, axis=Signal.SAMPLE_AXIS)
    values = np.fft.ifft(np.log(np.maximum(np.abs(spectrum), floor)), axis=Signal.SAMPLE_AXIS).real
    return CepstrumResult(
        np.arange(signal.n_samples) / signal.sampling_rate,
        values,
        {"floor": floor, "units": "quefrency_seconds"},
    )


def envelope_spectrum(
    signal: Signal, *, fft_length: int | None = None, remove_mean: bool = True
) -> FFTResult:
    envelope = signal_envelope(signal)
    values = envelope.time_data
    if remove_mean:
        values = values - np.mean(values, axis=Signal.SAMPLE_AXIS, keepdims=True)
    prepared = envelope.updated(time_data=values, operation="envelope_detrend")
    return compute_fft(prepared, fft_length)
