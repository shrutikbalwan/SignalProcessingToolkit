from __future__ import annotations

from abc import ABC, abstractmethod

from src.models.enums import WaveformType
from src.models.signal import Signal


class BaseGenerator(ABC):
    def __init__(self, waveform_type: WaveformType) -> None:
        self.waveform_type = waveform_type

    @abstractmethod
    def generate(
        self,
        sampling_rate: float = 44100.0,
        duration: float = 1.0,
        frequency: float = 440.0,
        amplitude: float = 1.0,
        phase: float = 0.0,
        **kwargs: object,
    ) -> Signal: ...


def create_generator(waveform: WaveformType) -> BaseGenerator:
    mapping = {
        WaveformType.SINE: "src.dsp.generators.sine.SineGenerator",
        WaveformType.COSINE: "src.dsp.generators.cosine.CosineGenerator",
        WaveformType.SQUARE: "src.dsp.generators.square.SquareGenerator",
        WaveformType.TRIANGLE: "src.dsp.generators.triangle.TriangleGenerator",
        WaveformType.SAWTOOTH: "src.dsp.generators.sawtooth.SawtoothGenerator",
        WaveformType.PULSE: "src.dsp.generators.pulse.PulseGenerator",
        WaveformType.CHIRP: "src.dsp.generators.chirp.ChirpGenerator",
        WaveformType.GAUSSIAN: "src.dsp.generators.gaussian.GaussianGenerator",
        WaveformType.NOISE: "src.dsp.generators.noise.NoiseGenerator",
        WaveformType.DC: "src.dsp.generators.dc.DCGenerator",
    }
    import importlib
    from typing import cast

    module_path, class_name = mapping[waveform].rsplit(".", 1)
    module = importlib.import_module(module_path)
    cls = getattr(module, class_name)
    return cast("BaseGenerator", cls(waveform))
