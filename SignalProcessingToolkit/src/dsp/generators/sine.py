from __future__ import annotations

import numpy as np

from src.dsp.generators.base import BaseGenerator
from src.models.enums import WaveformType
from src.models.signal import Signal


class SineGenerator(BaseGenerator):
    def __init__(self, waveform_type: WaveformType = WaveformType.SINE) -> None:
        super().__init__(waveform_type)

    def generate(
        self,
        sampling_rate: float = 44100.0,
        duration: float = 1.0,
        frequency: float = 440.0,
        amplitude: float = 1.0,
        phase: float = 0.0,
        **kwargs: object,
    ) -> Signal:
        t = np.linspace(0, duration, int(sampling_rate * duration), endpoint=False)
        data = amplitude * np.sin(2 * np.pi * frequency * t + phase)
        return Signal(
            time_data=data,
            sampling_rate=sampling_rate,
            frequency=frequency,
            amplitude=amplitude,
            phase=phase,
        )
