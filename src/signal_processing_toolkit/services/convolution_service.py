from __future__ import annotations

from typing import Literal, cast

import numpy as np

from signal_processing_toolkit.models.signal import Signal


def _validate(signal: Signal, kernel: Signal) -> None:
    signal.validate_compatibility(
        kernel, require_same_length=False, require_same_start=False, require_same_units=False
    )


def _convolve_channels(
    signal: Signal, kernel: Signal, mode: Literal["full", "same", "valid"]
) -> np.ndarray:
    if signal.is_mono:
        return cast(np.ndarray, np.convolve(signal.time_data, kernel.time_data, mode=mode))
    return np.stack(
        [
            np.convolve(signal.time_data[:, channel], kernel.time_data[:, channel], mode=mode)
            for channel in range(signal.n_channels)
        ],
        axis=Signal.CHANNEL_AXIS,
    )


class ConvolutionService:
    def linear(self, signal: Signal, kernel: Signal) -> Signal:
        _validate(signal, kernel)
        result = _convolve_channels(signal, kernel, "full")
        return signal.updated(
            time_data=result,
            start_time=signal.start_time + kernel.start_time,
            operation="linear_convolution",
            parameters={"kernel_id": kernel.metadata.id, "mode": "full"},
        )

    def circular(self, signal: Signal, kernel: Signal) -> Signal:
        _validate(signal, kernel)
        n = max(signal.n_samples, kernel.n_samples)
        result = np.fft.ifft(
            np.fft.fft(signal.time_data, n, axis=Signal.SAMPLE_AXIS)
            * np.fft.fft(kernel.time_data, n, axis=Signal.SAMPLE_AXIS),
            axis=Signal.SAMPLE_AXIS,
        )
        if not signal.is_complex and not kernel.is_complex:
            result = result.real
        return signal.updated(
            time_data=result,
            start_time=signal.start_time + kernel.start_time,
            operation="circular_convolution",
            parameters={"kernel_id": kernel.metadata.id},
        )

    def same(self, signal: Signal, kernel: Signal) -> Signal:
        _validate(signal, kernel)
        return signal.updated(
            time_data=_convolve_channels(signal, kernel, "same"),
            start_time=(
                signal.start_time
                + kernel.start_time
                + (min(signal.n_samples, kernel.n_samples) - 1) // 2 / signal.sampling_rate
            ),
            operation="linear_convolution",
            parameters={"kernel_id": kernel.metadata.id, "mode": "same"},
        )

    def valid(self, signal: Signal, kernel: Signal) -> Signal:
        _validate(signal, kernel)
        return signal.updated(
            time_data=_convolve_channels(signal, kernel, "valid"),
            start_time=(
                signal.start_time
                + kernel.start_time
                + (min(signal.n_samples, kernel.n_samples) - 1) / signal.sampling_rate
            ),
            operation="linear_convolution",
            parameters={"kernel_id": kernel.metadata.id, "mode": "valid"},
        )
