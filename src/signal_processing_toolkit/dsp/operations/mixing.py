from __future__ import annotations

import numpy as np

from signal_processing_toolkit.dsp.operations.base import BinaryOperation, align_signals
from signal_processing_toolkit.models.signal import Signal


class MixOperation(BinaryOperation):
    def apply(  # type: ignore[override]
        self, signal1: Signal, signal2: Signal, weight1: float = 0.5, weight2: float = 0.5, **kwargs
    ) -> Signal:
        data1, data2 = align_signals(signal1, signal2)
        mixed = weight1 * data1 + weight2 * data2
        return signal1.updated(
            time_data=mixed,
            operation="mix",
            parameters={
                "other_signal_id": signal2.metadata.id,
                "weight1": weight1,
                "weight2": weight2,
            },
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
        if data1.ndim == 2:
            fade_in = fade_in[:, np.newaxis]
            fade_out = fade_out[:, np.newaxis]

        result = np.zeros_like(data1)
        result[: length - fade_len] = data1[: length - fade_len]
        result[length - fade_len :] = (
            data1[length - fade_len :] * fade_out + data2[length - fade_len :] * fade_in
        )

        return signal1.updated(
            time_data=result,
            operation="crossfade",
            parameters={
                "other_signal_id": signal2.metadata.id,
                "position": crossfade_position,
            },
        )
