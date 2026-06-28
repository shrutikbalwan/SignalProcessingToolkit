from __future__ import annotations

import numpy as np

from src.dsp.operations.base import BaseOperation
from src.models.signal import Signal


class ScaleOperation(BaseOperation):
    def apply(self, signal: Signal, factor: float = 1.0, **kwargs) -> Signal:
        return Signal(
            time_data=signal.time_data * factor,
            sampling_rate=signal.sampling_rate,
            amplitude=signal.amplitude * factor,
            metadata=signal.metadata,
        )


class OffsetOperation(BaseOperation):
    def apply(self, signal: Signal, offset: float = 0.0, **kwargs) -> Signal:
        return Signal(
            time_data=signal.time_data + offset,
            sampling_rate=signal.sampling_rate,
            metadata=signal.metadata,
        )


class AmplitudeNormalizeOperation(BaseOperation):
    def apply(self, signal: Signal, target_amplitude: float = 1.0, **kwargs) -> Signal:
        peak = np.max(np.abs(signal.time_data))
        if peak == 0:
            return signal.copy()
        factor = target_amplitude / peak
        return Signal(
            time_data=signal.time_data * factor,
            sampling_rate=signal.sampling_rate,
            amplitude=signal.amplitude * factor,
            metadata=signal.metadata,
        )


class RMSNormalizeOperation(BaseOperation):
    def apply(self, signal: Signal, target_rms: float = 1.0, **kwargs) -> Signal:
        current_rms = signal.rms
        if current_rms == 0:
            return signal.copy()
        factor = target_rms / current_rms
        return Signal(
            time_data=signal.time_data * factor,
            sampling_rate=signal.sampling_rate,
            amplitude=signal.amplitude * factor,
            metadata=signal.metadata,
        )
