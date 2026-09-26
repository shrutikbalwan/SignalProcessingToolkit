from __future__ import annotations

from typing import Literal

import numpy as np
from scipy import signal as sp_signal
from scipy.fft import fft, ifft, irfft, next_fast_len, rfft

from signal_processing_toolkit.models.signal import Signal
from signal_processing_toolkit.services.convolution_service import ConvolutionService


def linear_convolve(
    signal1: Signal,
    signal2: Signal,
    mode: Literal["full", "same", "valid"] = "full",
) -> Signal:
    service = ConvolutionService()
    if mode == "same":
        return service.same(signal1, signal2)
    if mode == "valid":
        return service.valid(signal1, signal2)
    return service.linear(signal1, signal2)


def fft_convolve(
    signal1: Signal,
    signal2: Signal,
    mode: Literal["full", "same", "valid"] = "full",
) -> Signal:
    signal1.validate_compatibility(
        signal2, require_same_length=False, require_same_start=False, require_same_units=False
    )
    result = sp_signal.fftconvolve(
        signal1.time_data,
        signal2.time_data,
        mode=mode,
        axes=Signal.SAMPLE_AXIS,
    )
    return signal1.updated(
        time_data=result,
        start_time=(
            signal1.start_time
            + signal2.start_time
            + (
                0
                if mode == "full"
                else (min(signal1.n_samples, signal2.n_samples) - 1) // 2
                if mode == "same"
                else min(signal1.n_samples, signal2.n_samples) - 1
            )
            / signal1.sampling_rate
        ),
        operation="fft_convolution",
        parameters={"other_signal_id": signal2.metadata.id, "mode": mode},
    )


def circular_convolve(signal1: Signal, signal2: Signal) -> Signal:
    return ConvolutionService().circular(signal1, signal2)


def overlap_add_convolve(
    signal: Signal, impulse_response: Signal, block_size: int | None = None
) -> Signal:
    """Block FFT convolution using the overlap-add algorithm."""
    signal.validate_compatibility(
        impulse_response,
        require_same_length=False,
        require_same_start=False,
        require_same_units=False,
    )
    if signal.n_samples == 0 or impulse_response.n_samples == 0:
        raise ValueError("Convolution is undefined for empty signals")
    payload = max(1, min(signal.n_samples, 4096)) if block_size is None else int(block_size)
    if payload < 1:
        raise ValueError("block_size must be positive")
    data = _block_convolve(signal.time_data, impulse_response.time_data, payload, "add")
    return signal.updated(
        time_data=data,
        start_time=signal.start_time + impulse_response.start_time,
        operation="overlap_add_convolution",
        parameters={"block_size": payload},
    )


def overlap_save_convolve(
    signal: Signal, impulse_response: Signal, block_size: int | None = None
) -> Signal:
    """Block FFT convolution using the overlap-save algorithm."""
    signal.validate_compatibility(
        impulse_response,
        require_same_length=False,
        require_same_start=False,
        require_same_units=False,
    )
    if signal.n_samples == 0 or impulse_response.n_samples == 0:
        raise ValueError("Convolution is undefined for empty signals")
    payload = max(1, min(signal.n_samples, 4096)) if block_size is None else int(block_size)
    if payload < 1:
        raise ValueError("block_size must be positive")
    data = _block_convolve(signal.time_data, impulse_response.time_data, payload, "save")
    return signal.updated(
        time_data=data,
        start_time=signal.start_time + impulse_response.start_time,
        operation="overlap_save_convolution",
        parameters={"block_size": payload},
    )


def _block_convolve(
    first: np.ndarray,
    second: np.ndarray,
    payload: int,
    method: Literal["add", "save"],
) -> np.ndarray:
    """Apply one block algorithm independently to each channel."""
    first_channels = first[:, np.newaxis] if first.ndim == 1 else first
    second_channels = second[:, np.newaxis] if second.ndim == 1 else second
    results = [
        _block_convolve_mono(first_channels[:, index], second_channels[:, index], payload, method)
        for index in range(first_channels.shape[1])
    ]
    stacked = np.column_stack(results)
    return stacked[:, 0] if first.ndim == 1 else stacked


def _block_convolve_mono(
    first: np.ndarray,
    second: np.ndarray,
    payload: int,
    method: Literal["add", "save"],
) -> np.ndarray:
    target = len(first) + len(second) - 1
    transform_size = next_fast_len(payload + len(second) - 1)
    real = not np.iscomplexobj(first) and not np.iscomplexobj(second)
    transform = rfft if real else fft
    inverse = irfft if real else ifft
    kernel = transform(second, transform_size)
    dtype = np.result_type(first, second, np.float64 if real else np.complex128)

    if method == "add":
        output = np.zeros(target, dtype=dtype)
        for start in range(0, len(first), payload):
            block = first[start : start + payload]
            transformed = transform(block, transform_size) * kernel
            values = inverse(transformed, transform_size)[: len(block) + len(second) - 1]
            end = min(target, start + len(values))
            output[start:end] += values[: end - start]
        return np.asarray(output.real if real else output)

    overlap = len(second) - 1
    padded = np.pad(first, (overlap, overlap))
    blocks: list[np.ndarray] = []
    for start in range(0, target, payload):
        frame = padded[start : start + transform_size]
        if len(frame) < transform_size:
            frame = np.pad(frame, (0, transform_size - len(frame)))
        transformed = transform(frame, transform_size) * kernel
        values = inverse(transformed, transform_size)
        blocks.append(np.asarray(values[overlap : overlap + payload]))
    output = np.concatenate(blocks)[:target]
    return np.asarray(output.real if real else output, dtype=dtype)


def validate_same_sampling_rate(signal1: Signal, signal2: Signal) -> None:
    signal1.validate_compatibility(
        signal2, require_same_length=False, require_same_start=False, require_same_units=False
    )
