from __future__ import annotations

import numpy as np

from src.dsp.operations.base import BinaryOperation, align_signals
from src.models.signal import Signal


class AddOperation(BinaryOperation):
    def apply(self, signal1: Signal, signal2: Signal, **kwargs) -> Signal:  # type: ignore[override]
        data1, data2 = align_signals(signal1, signal2)
        return Signal(
            time_data=data1 + data2,
            sampling_rate=signal1.sampling_rate,
            metadata=signal1.metadata,
        )


class SubtractOperation(BinaryOperation):
    def apply(self, signal1: Signal, signal2: Signal, **kwargs) -> Signal:  # type: ignore[override]
        data1, data2 = align_signals(signal1, signal2)
        return Signal(
            time_data=data1 - data2,
            sampling_rate=signal1.sampling_rate,
            metadata=signal1.metadata,
        )


class MultiplyOperation(BinaryOperation):
    def apply(self, signal1: Signal, signal2: Signal, **kwargs) -> Signal:  # type: ignore[override]
        data1, data2 = align_signals(signal1, signal2)
        return Signal(
            time_data=data1 * data2,
            sampling_rate=signal1.sampling_rate,
            metadata=signal1.metadata,
        )


class DivideOperation(BinaryOperation):
    def apply(self, signal1: Signal, signal2: Signal, **kwargs) -> Signal:  # type: ignore[override]
        data1, data2 = align_signals(signal1, signal2)
        with np.errstate(divide="ignore", invalid="ignore"):
            result = np.divide(data1, data2, out=np.zeros_like(data1), where=data2 != 0)
        return Signal(
            time_data=result,
            sampling_rate=signal1.sampling_rate,
            metadata=signal1.metadata,
        )
