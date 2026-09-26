from __future__ import annotations

import numpy as np

from signal_processing_toolkit.dsp.operations.base import BaseOperation
from signal_processing_toolkit.models.signal import Signal


class TimeReversalOperation(BaseOperation):
    def apply(self, signal: Signal, **kwargs) -> Signal:
        return signal.updated(
            time_data=signal.time_data[::-1].copy(),
            frequency=-signal.frequency,
            phase=signal.phase + np.pi if signal.frequency != 0 else signal.phase,
            operation="time_reverse",
        )
