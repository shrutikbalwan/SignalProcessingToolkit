from __future__ import annotations

import numpy as np

from signal_processing_toolkit.models.signal import Signal


def _validate(signal1: Signal, signal2: Signal) -> None:
    signal1.validate_compatibility(
        signal2, require_same_length=False, require_same_start=False, require_same_units=False
    )


def _circular_result(signal1: Signal, signal2: Signal, n: int, *, correlate: bool) -> np.ndarray:
    spectrum1 = np.fft.fft(signal1.time_data, n=n, axis=Signal.SAMPLE_AXIS)
    spectrum2 = np.fft.fft(signal2.time_data, n=n, axis=Signal.SAMPLE_AXIS)
    product = np.conj(spectrum1) * spectrum2 if correlate else spectrum1 * spectrum2
    result = np.fft.ifft(product, axis=Signal.SAMPLE_AXIS)
    return result.real if not signal1.is_complex and not signal2.is_complex else result


def circular_convolve(signal1: Signal, signal2: Signal) -> Signal:
    return circular_convolve_fft(signal1, signal2)


def circular_convolve_fft(signal1: Signal, signal2: Signal, n_fft: int | None = None) -> Signal:
    from signal_processing_toolkit.services.convolution_service import ConvolutionService

    expected = max(signal1.n_samples, signal2.n_samples)
    if n_fft is not None and n_fft != expected:
        raise ValueError(f"Circular convolution length is {expected}; explicit n_fft must match")
    return ConvolutionService().circular(signal1, signal2)


def circular_correlate(signal1: Signal, signal2: Signal) -> Signal:
    _validate(signal1, signal2)
    n = max(signal1.n_samples, signal2.n_samples)
    return signal1.updated(
        time_data=_circular_result(signal1, signal2, n, correlate=True),
        start_time=signal1.start_time - signal2.start_time,
        operation="circular_correlation",
        parameters={"other_signal_id": signal2.metadata.id, "n_fft": n},
    )


def validate_same_sampling_rate(signal1: Signal, signal2: Signal) -> None:
    _validate(signal1, signal2)
