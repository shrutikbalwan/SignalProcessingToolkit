from __future__ import annotations

import numpy as np
from scipy import signal as sp_signal

from src.models.signal import Signal


def linear_convolve(signal1: Signal, signal2: Signal, mode: str = "full") -> Signal:
    validate_same_sampling_rate(signal1, signal2)

    result_data: np.ndarray = np.convolve(signal1.time_data, signal2.time_data, mode=mode)  # type: ignore[call-overload]

    return Signal(
        time_data=result_data,
        sampling_rate=signal1.sampling_rate,
    )


def fft_convolve(signal1: Signal, signal2: Signal, mode: str = "full") -> Signal:
    validate_same_sampling_rate(signal1, signal2)

    result_data = sp_signal.fftconvolve(signal1.time_data, signal2.time_data, mode=mode)

    return Signal(
        time_data=result_data,
        sampling_rate=signal1.sampling_rate,
    )


def circular_convolve(signal1: Signal, signal2: Signal) -> Signal:
    validate_same_sampling_rate(signal1, signal2)

    n = max(signal1.length, signal2.length)

    padded1 = np.pad(signal1.time_data, (0, n - signal1.length))
    padded2 = np.pad(signal2.time_data, (0, n - signal2.length))

    from scipy.fft import fft, ifft

    fft1 = fft(padded1, n)
    fft2 = fft(padded2, n)

    result_fft = fft1 * fft2
    result_data = np.real(ifft(result_fft))

    return Signal(
        time_data=result_data,
        sampling_rate=signal1.sampling_rate,
    )


def overlap_add_convolve(
    signal: Signal, impulse_response: Signal, block_size: int | None = None
) -> Signal:
    if block_size is None:
        block_size = 1024

    validate_same_sampling_rate(signal, impulse_response)

    n_ir = impulse_response.length
    n_signal = signal.length
    n_output = n_signal + n_ir - 1

    if block_size < n_ir:
        block_size = n_ir

    output = np.zeros(n_output)

    for i in range(0, n_signal, block_size):
        block = signal.time_data[i : i + block_size]
        block_len = len(block)

        n_fft = 1
        while n_fft < block_len + n_ir - 1:
            n_fft *= 2

        from scipy.fft import fft, ifft

        block_fft = fft(block, n_fft)
        ir_fft = fft(impulse_response.time_data, n_fft)

        conv_fft = block_fft * ir_fft
        conv_block = np.real(ifft(conv_fft))

        output[i : i + block_len + n_ir - 1] += conv_block[: block_len + n_ir - 1]

    return Signal(
        time_data=output,
        sampling_rate=signal.sampling_rate,
    )


def overlap_save_convolve(
    signal: Signal, impulse_response: Signal, block_size: int | None = None
) -> Signal:
    if block_size is None:
        block_size = 1024

    validate_same_sampling_rate(signal, impulse_response)

    n_ir = impulse_response.length
    n_signal = signal.length

    if block_size < n_ir:
        block_size = n_ir

    n_fft = 1
    while n_fft < block_size + n_ir - 1:
        n_fft *= 2

    from scipy.fft import fft, ifft

    ir_padded = np.pad(impulse_response.time_data, (0, n_fft - n_ir))
    ir_fft = fft(ir_padded)

    signal_padded = np.pad(signal.time_data, (n_ir - 1, 0))
    n_output = n_signal + n_ir - 1
    output = np.zeros(n_output)

    for i in range(0, n_signal, block_size):
        block = signal_padded[i : i + n_fft]
        if len(block) < n_fft:
            block = np.pad(block, (0, n_fft - len(block)))

        block_fft = fft(block)
        conv_fft = block_fft * ir_fft
        conv_block = np.real(ifft(conv_fft))

        output[i : i + block_size] = conv_block[n_ir - 1 : n_ir - 1 + block_size]

    return Signal(
        time_data=output,
        sampling_rate=signal.sampling_rate,
    )


def validate_same_sampling_rate(signal1: Signal, signal2: Signal) -> None:
    if signal1.sampling_rate != signal2.sampling_rate:
        raise ValueError(
            f"Sampling rate mismatch: {signal1.sampling_rate} vs {signal2.sampling_rate}"
        )
