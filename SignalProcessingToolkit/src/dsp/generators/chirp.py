from __future__ import annotations

import numpy as np
from scipy import signal as sp_signal

from src.dsp.generators.base import BaseGenerator
from src.models.enums import WaveformType
from src.models.signal import Signal


class ChirpGenerator(BaseGenerator):
    def __init__(self, waveform_type: WaveformType = WaveformType.CHIRP) -> None:
        super().__init__(waveform_type)

    def generate(  # type: ignore[override]
        self,
        sampling_rate: float = 44100.0,
        duration: float = 1.0,
        frequency: float = 100.0,
        amplitude: float = 1.0,
        phase: float = 0.0,
        f1: float = 1000.0,
        method: str = "linear",
        **kwargs,
    ) -> Signal:
        t = np.linspace(0, duration, int(sampling_rate * duration), endpoint=False)
        data = amplitude * sp_signal.chirp(
            t, f0=frequency, t1=duration, f1=f1, method=method, phi=phase
        )
        return Signal(
            time_data=data,
            sampling_rate=sampling_rate,
            frequency=frequency,
            amplitude=amplitude,
            phase=phase,
        )
