from __future__ import annotations

import numpy as np
from scipy import signal as sp_signal

from src.dsp.generators.base import BaseGenerator
from src.models.enums import WaveformType
from src.models.signal import Signal


class SawtoothGenerator(BaseGenerator):
    def __init__(self, waveform_type: WaveformType = WaveformType.SAWTOOTH) -> None:
        super().__init__(waveform_type)

    def generate(  # type: ignore[override]
        self,
        sampling_rate: float = 44100.0,
        duration: float = 1.0,
        frequency: float = 440.0,
        amplitude: float = 1.0,
        phase: float = 0.0,
        width: float = 1.0,
        **kwargs,
    ) -> Signal:
        t = np.linspace(0, duration, int(sampling_rate * duration), endpoint=False)
        data = amplitude * sp_signal.sawtooth(2 * np.pi * frequency * t + phase, width=width)
        return Signal(
            time_data=data,
            sampling_rate=sampling_rate,
            frequency=frequency,
            amplitude=amplitude,
            phase=phase,
        )
