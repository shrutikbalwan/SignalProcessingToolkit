from __future__ import annotations

import numpy as np

from signal_processing_toolkit.dsp.operations.base import BinaryOperation, align_signals
from signal_processing_toolkit.models.signal import Signal


class AddOperation(BinaryOperation):
    def apply(self, signal1: Signal, signal2: Signal, **kwargs) -> Signal:  # type: ignore[override]
        data1, data2 = align_signals(signal1, signal2)
        return signal1.updated(
            time_data=data1 + data2,
            operation="add",
            parameters={"other_signal_id": signal2.metadata.id},
        )


class SubtractOperation(BinaryOperation):
    def apply(self, signal1: Signal, signal2: Signal, **kwargs) -> Signal:  # type: ignore[override]
        data1, data2 = align_signals(signal1, signal2)
        return signal1.updated(
            time_data=data1 - data2,
            operation="subtract",
            parameters={"other_signal_id": signal2.metadata.id},
        )


class MultiplyOperation(BinaryOperation):
    def apply(self, signal1: Signal, signal2: Signal, **kwargs) -> Signal:  # type: ignore[override]
        data1, data2 = align_signals(signal1, signal2)
        return signal1.updated(
            time_data=data1 * data2,
            operation="multiply",
            parameters={"other_signal_id": signal2.metadata.id},
        )


class DivideOperation(BinaryOperation):
    def apply(self, signal1: Signal, signal2: Signal, **kwargs) -> Signal:  # type: ignore[override]
        data1, data2 = align_signals(signal1, signal2)
        with np.errstate(divide="ignore", invalid="ignore"):
            result = np.divide(data1, data2, out=np.zeros_like(data1), where=data2 != 0)
        return signal1.updated(
            time_data=result,
            operation="divide",
            parameters={"other_signal_id": signal2.metadata.id},
        )
