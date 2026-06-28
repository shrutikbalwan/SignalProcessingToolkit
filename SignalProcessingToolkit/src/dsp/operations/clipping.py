from __future__ import annotations

import numpy as np

from src.dsp.operations.base import BaseOperation
from src.models.signal import Signal


class HardClippingOperation(BaseOperation):
    def apply(self, signal: Signal, threshold: float = 1.0, **kwargs) -> Signal:
        clipped_data = np.clip(signal.time_data, -threshold, threshold)
        return Signal(
            time_data=clipped_data,
            sampling_rate=signal.sampling_rate,
            metadata=signal.metadata,
        )


class SoftClippingOperation(BaseOperation):
    def apply(self, signal: Signal, threshold: float = 1.0, **kwargs) -> Signal:
        x = signal.time_data / threshold
        clipped_data = threshold * np.tanh(x)
        return Signal(
            time_data=clipped_data,
            sampling_rate=signal.sampling_rate,
            metadata=signal.metadata,
        )


class AsymmetricClippingOperation(BaseOperation):
    def apply(
        self, signal: Signal, lower_threshold: float = -1.0, upper_threshold: float = 1.0, **kwargs
    ) -> Signal:
        clipped_data = np.clip(signal.time_data, lower_threshold, upper_threshold)
        return Signal(
            time_data=clipped_data,
            sampling_rate=signal.sampling_rate,
            metadata=signal.metadata,
        )
