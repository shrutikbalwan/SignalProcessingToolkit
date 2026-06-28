from __future__ import annotations

import numpy as np

from src.models.signal import Signal


class ConvolutionService:
    def linear(self, signal: Signal, kernel: Signal) -> Signal:
        result = np.convolve(signal.time_data, kernel.time_data, mode="full")
        return Signal(
            time_data=result,
            sampling_rate=min(signal.sampling_rate, kernel.sampling_rate),
        )

    def circular(self, signal: Signal, kernel: Signal) -> Signal:
        n = max(len(signal.time_data), len(kernel.time_data))
        result = np.fft.ifft(np.fft.fft(signal.time_data, n) * np.fft.fft(kernel.time_data, n)).real
        return Signal(
            time_data=result,
            sampling_rate=min(signal.sampling_rate, kernel.sampling_rate),
        )

    def same(self, signal: Signal, kernel: Signal) -> Signal:
        result = np.convolve(signal.time_data, kernel.time_data, mode="same")
        return Signal(
            time_data=result,
            sampling_rate=signal.sampling_rate,
        )

    def valid(self, signal: Signal, kernel: Signal) -> Signal:
        result = np.convolve(signal.time_data, kernel.time_data, mode="valid")
        return Signal(
            time_data=result,
            sampling_rate=signal.sampling_rate,
        )
