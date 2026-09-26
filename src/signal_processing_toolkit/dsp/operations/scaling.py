from __future__ import annotations

import numpy as np

from signal_processing_toolkit.dsp.operations.base import BaseOperation
from signal_processing_toolkit.models.signal import Signal


class ScaleOperation(BaseOperation):
    def apply(self, signal: Signal, factor: float = 1.0, **kwargs) -> Signal:
        return signal.updated(
            time_data=signal.time_data * factor,
            amplitude=signal.amplitude * factor,
            operation="scale",
            parameters={"factor": factor},
        )


class OffsetOperation(BaseOperation):
    def apply(self, signal: Signal, offset: float = 0.0, **kwargs) -> Signal:
        return signal.updated(
            time_data=signal.time_data + offset,
            operation="offset",
            parameters={"offset": offset},
        )


class AmplitudeNormalizeOperation(BaseOperation):
    def apply(self, signal: Signal, target_amplitude: float = 1.0, **kwargs) -> Signal:
        peak = np.max(np.abs(signal.time_data))
        if peak == 0:
            return signal.copy()
        factor = target_amplitude / peak
        return signal.updated(
            time_data=signal.time_data * factor,
            amplitude=signal.amplitude * factor,
            operation="normalize_amplitude",
            parameters={"target": target_amplitude},
        )


class RMSNormalizeOperation(BaseOperation):
    def apply(self, signal: Signal, target_rms: float = 1.0, **kwargs) -> Signal:
        current_rms = signal.rms
        if current_rms == 0:
            return signal.copy()
        factor = target_rms / current_rms
        return signal.updated(
            time_data=signal.time_data * factor,
            amplitude=signal.amplitude * factor,
            operation="normalize_rms",
            parameters={"target": target_rms},
        )
