from __future__ import annotations

import numpy as np

from src.dsp.operations.base import BaseOperation
from src.models.signal import Signal


class MinMaxNormalizeOperation(BaseOperation):
    def apply(
        self, signal: Signal, min_val: float = -1.0, max_val: float = 1.0, **kwargs
    ) -> Signal:
        data = signal.time_data
        data_min, data_max = np.min(data), np.max(data)
        if data_max == data_min:
            return signal.copy()
        normalized = (data - data_min) / (data_max - data_min)
        scaled = normalized * (max_val - min_val) + min_val
        return Signal(
            time_data=scaled,
            sampling_rate=signal.sampling_rate,
            metadata=signal.metadata,
        )


class ZScoreNormalizeOperation(BaseOperation):
    def apply(self, signal: Signal, **kwargs) -> Signal:
        data = signal.time_data
        mean = np.mean(data)
        std = np.std(data)
        if std == 0:
            return signal.copy()
        normalized = (data - mean) / std
        return Signal(
            time_data=normalized,
            sampling_rate=signal.sampling_rate,
            metadata=signal.metadata,
        )


class UnitNormalizeOperation(BaseOperation):
    def apply(self, signal: Signal, **kwargs) -> Signal:
        norm = np.linalg.norm(signal.time_data)
        if norm == 0:
            return signal.copy()
        return Signal(
            time_data=signal.time_data / norm,
            sampling_rate=signal.sampling_rate,
            metadata=signal.metadata,
        )
