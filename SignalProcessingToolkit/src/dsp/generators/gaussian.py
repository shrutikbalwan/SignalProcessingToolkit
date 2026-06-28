from __future__ import annotations

import numpy as np

from src.dsp.generators.base import BaseGenerator
from src.models.enums import WaveformType
from src.models.signal import Signal


class GaussianGenerator(BaseGenerator):
    def __init__(self, waveform_type: WaveformType = WaveformType.GAUSSIAN) -> None:
        super().__init__(waveform_type)

    def generate(  # type: ignore[override]
        self,
        sampling_rate: float = 44100.0,
        duration: float = 1.0,
        frequency: float = 0.0,
        amplitude: float = 1.0,
        phase: float = 0.0,
        mu: float = 0.5,
        sigma: float = 0.1,
        **kwargs,
    ) -> Signal:
        t = np.linspace(0, duration, int(sampling_rate * duration), endpoint=False)
        data = amplitude * np.exp(-0.5 * ((t - mu) / sigma) ** 2)
        return Signal(
            time_data=data,
            sampling_rate=sampling_rate,
            frequency=0.0,
            amplitude=amplitude,
            phase=0.0,
        )
