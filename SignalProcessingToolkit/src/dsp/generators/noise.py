from __future__ import annotations

from src.dsp.generators.base import BaseGenerator
from src.models.enums import NoiseType, WaveformType
from src.models.signal import Signal


class NoiseGenerator(BaseGenerator):
    def __init__(self, waveform_type: WaveformType = WaveformType.NOISE) -> None:
        super().__init__(waveform_type)

    def generate(  # type: ignore[override]
        self,
        sampling_rate: float = 44100.0,
        duration: float = 1.0,
        frequency: float = 0.0,
        amplitude: float = 1.0,
        phase: float = 0.0,
        noise_type: str = "white",
        **kwargs,
    ) -> Signal:
        length = int(sampling_rate * duration)
        nt = (
            NoiseType(noise_type) if noise_type in {t.value for t in NoiseType} else NoiseType.WHITE
        )
        from src.dsp.noise.generators import generate_noise

        data = generate_noise(nt, length, std=amplitude)
        return Signal(time_data=data, sampling_rate=sampling_rate)
