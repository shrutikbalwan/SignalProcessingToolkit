from __future__ import annotations

import numpy as np

from src.dsp.operations.base import BaseOperation
from src.models.signal import Signal


class HalfWaveRectifyOperation(BaseOperation):
    def apply(self, signal: Signal, **kwargs) -> Signal:
        rectified = np.maximum(signal.time_data, 0)
        return Signal(
            time_data=rectified,
            sampling_rate=signal.sampling_rate,
            metadata=signal.metadata,
        )


class FullWaveRectifyOperation(BaseOperation):
    def apply(self, signal: Signal, **kwargs) -> Signal:
        rectified = np.abs(signal.time_data)
        return Signal(
            time_data=rectified,
            sampling_rate=signal.sampling_rate,
            metadata=signal.metadata,
        )
