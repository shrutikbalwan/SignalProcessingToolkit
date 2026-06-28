from __future__ import annotations

import numpy as np

from src.dsp.generators.base import BaseGenerator
from src.models.enums import WaveformType
from src.models.signal import Signal


class DCGenerator(BaseGenerator):
    def __init__(self, waveform_type: WaveformType = WaveformType.DC) -> None:
        super().__init__(waveform_type)

    def generate(
        self,
        sampling_rate: float = 44100.0,
        duration: float = 1.0,
        frequency: float = 0.0,
        amplitude: float = 1.0,
        phase: float = 0.0,
        **kwargs,
    ) -> Signal:
        length = int(sampling_rate * duration)
        data = amplitude * np.ones(length)
        return Signal(
            time_data=data,
            sampling_rate=sampling_rate,
            frequency=0.0,
            amplitude=amplitude,
            phase=0.0,
        )
