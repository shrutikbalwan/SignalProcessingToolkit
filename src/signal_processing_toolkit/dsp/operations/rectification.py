from __future__ import annotations

import numpy as np

from signal_processing_toolkit.dsp.operations.base import BaseOperation
from signal_processing_toolkit.models.signal import Signal


class HalfWaveRectifyOperation(BaseOperation):
    def apply(self, signal: Signal, **kwargs) -> Signal:
        rectified = np.maximum(signal.time_data, 0)
        return signal.updated(
            time_data=rectified,
            operation="half_wave_rectify",
        )


class FullWaveRectifyOperation(BaseOperation):
    def apply(self, signal: Signal, **kwargs) -> Signal:
        rectified = np.abs(signal.time_data)
        return signal.updated(
            time_data=rectified,
            operation="full_wave_rectify",
        )
