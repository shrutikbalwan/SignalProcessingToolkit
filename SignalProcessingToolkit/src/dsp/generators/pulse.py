from __future__ import annotations

import numpy as np

from src.dsp.generators.base import BaseGenerator
from src.models.enums import WaveformType
from src.models.signal import Signal


class PulseGenerator(BaseGenerator):
    def __init__(self, waveform_type: WaveformType = WaveformType.PULSE) -> None:
        super().__init__(waveform_type)

    def generate(  # type: ignore[override]
        self,
        sampling_rate: float = 44100.0,
        duration: float = 1.0,
        frequency: float = 1.0,
        amplitude: float = 1.0,
        phase: float = 0.0,
        pulse_width: float = 0.01,
        **kwargs,
    ) -> Signal:
        t = np.linspace(0, duration, int(sampling_rate * duration), endpoint=False)
        period = 1.0 / frequency if frequency > 0 else duration
        data = np.zeros_like(t)
        trigger = np.mod(t, period) < pulse_width
        data[trigger] = amplitude
        return Signal(
            time_data=data,
            sampling_rate=sampling_rate,
            frequency=frequency,
            amplitude=amplitude,
            phase=phase,
        )
