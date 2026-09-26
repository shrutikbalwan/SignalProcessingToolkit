from __future__ import annotations

import numpy as np

from signal_processing_toolkit.dsp.operations.base import BaseOperation
from signal_processing_toolkit.models.signal import Signal


class MinMaxNormalizeOperation(BaseOperation):
    def apply(
        self, signal: Signal, min_val: float = -1.0, max_val: float = 1.0, **kwargs
    ) -> Signal:
        if signal.is_complex:
            raise TypeError("Min-max normalization is undefined for complex-valued samples")
        data = signal.time_data
        data_min, data_max = np.min(data), np.max(data)
        if data_max == data_min:
            return signal.copy()
        normalized = (data - data_min) / (data_max - data_min)
        scaled = normalized * (max_val - min_val) + min_val
        return signal.updated(
            time_data=scaled,
            operation="normalize_min_max",
            parameters={"minimum": min_val, "maximum": max_val},
        )


class ZScoreNormalizeOperation(BaseOperation):
    def apply(self, signal: Signal, **kwargs) -> Signal:
        data = signal.time_data
        mean = np.mean(data)
        std = np.std(data)
        if std == 0:
            return signal.copy()
        normalized = (data - mean) / std
        return signal.updated(
            time_data=normalized,
            operation="normalize_z_score",
        )


class UnitNormalizeOperation(BaseOperation):
    def apply(self, signal: Signal, **kwargs) -> Signal:
        norm = np.linalg.norm(signal.time_data)
        if norm == 0:
            return signal.copy()
        return signal.updated(
            time_data=signal.time_data / norm,
            operation="normalize_unit",
        )
