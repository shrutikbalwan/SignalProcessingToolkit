from __future__ import annotations

import numpy as np

from signal_processing_toolkit.dsp.operations.base import BaseOperation
from signal_processing_toolkit.models.signal import Signal


class HardClippingOperation(BaseOperation):
    def apply(self, signal: Signal, threshold: float = 1.0, **kwargs) -> Signal:
        clipped_data = np.clip(signal.time_data, -threshold, threshold)
        return signal.updated(
            time_data=clipped_data,
            operation="hard_clip",
            parameters={"threshold": threshold},
        )


class SoftClippingOperation(BaseOperation):
    def apply(self, signal: Signal, threshold: float = 1.0, **kwargs) -> Signal:
        x = signal.time_data / threshold
        clipped_data = threshold * np.tanh(x)
        return signal.updated(
            time_data=clipped_data,
            operation="soft_clip",
            parameters={"threshold": threshold},
        )


class AsymmetricClippingOperation(BaseOperation):
    def apply(
        self, signal: Signal, lower_threshold: float = -1.0, upper_threshold: float = 1.0, **kwargs
    ) -> Signal:
        clipped_data = np.clip(signal.time_data, lower_threshold, upper_threshold)
        return signal.updated(
            time_data=clipped_data,
            operation="asymmetric_clip",
            parameters={"lower": lower_threshold, "upper": upper_threshold},
        )
