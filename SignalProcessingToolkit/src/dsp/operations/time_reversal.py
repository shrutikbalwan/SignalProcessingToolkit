from __future__ import annotations

import numpy as np

from src.dsp.operations.base import BaseOperation
from src.models.signal import Signal


class TimeReversalOperation(BaseOperation):
    def apply(self, signal: Signal, **kwargs) -> Signal:
        return Signal(
            time_data=signal.time_data[::-1].copy(),
            sampling_rate=signal.sampling_rate,
            frequency=-signal.frequency,
            phase=signal.phase + np.pi if signal.frequency != 0 else signal.phase,
            metadata=signal.metadata,
        )
