from __future__ import annotations

import numpy as np

from src.dsp.operations.base import BinaryOperation, align_signals
from src.models.signal import Signal


class MixOperation(BinaryOperation):
    def apply(  # type: ignore[override]
        self, signal1: Signal, signal2: Signal, weight1: float = 0.5, weight2: float = 0.5, **kwargs
    ) -> Signal:
        data1, data2 = align_signals(signal1, signal2)
        mixed = weight1 * data1 + weight2 * data2
        return Signal(
            time_data=mixed,
            sampling_rate=signal1.sampling_rate,
            metadata=signal1.metadata,
        )


class CrossfadeOperation(BinaryOperation):
    def apply(  # type: ignore[override]
        self, signal1: Signal, signal2: Signal, crossfade_position: float = 0.5, **kwargs
    ) -> Signal:
        data1, data2 = align_signals(signal1, signal2)
        length = len(data1)
        fade_len = int(length * crossfade_position)

        fade_in = np.linspace(0, 1, fade_len)
        fade_out = np.linspace(1, 0, fade_len)

        result = np.zeros_like(data1)
        result[: length - fade_len] = data1[: length - fade_len]
        result[length - fade_len :] = (
            data1[length - fade_len :] * fade_out + data2[length - fade_len :] * fade_in
        )

        return Signal(
            time_data=result,
            sampling_rate=signal1.sampling_rate,
            metadata=signal1.metadata,
        )
