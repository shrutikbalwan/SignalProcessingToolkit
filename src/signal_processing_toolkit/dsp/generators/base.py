from __future__ import annotations

from abc import ABC, abstractmethod

from signal_processing_toolkit.models.enums import WaveformType
from signal_processing_toolkit.models.signal import Signal


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
        WaveformType.SINE: "signal_processing_toolkit.dsp.generators.sine.SineGenerator",
        WaveformType.COSINE: "signal_processing_toolkit.dsp.generators.cosine.CosineGenerator",
        WaveformType.SQUARE: "signal_processing_toolkit.dsp.generators.square.SquareGenerator",
        WaveformType.TRIANGLE: (
            "signal_processing_toolkit.dsp.generators.triangle.TriangleGenerator"
        ),
        WaveformType.SAWTOOTH: (
            "signal_processing_toolkit.dsp.generators.sawtooth.SawtoothGenerator"
        ),
        WaveformType.PULSE: "signal_processing_toolkit.dsp.generators.pulse.PulseGenerator",
        WaveformType.CHIRP: "signal_processing_toolkit.dsp.generators.chirp.ChirpGenerator",
        WaveformType.GAUSSIAN: (
            "signal_processing_toolkit.dsp.generators.gaussian.GaussianGenerator"
        ),
        WaveformType.NOISE: "signal_processing_toolkit.dsp.generators.noise.NoiseGenerator",
        WaveformType.DC: "signal_processing_toolkit.dsp.generators.dc.DCGenerator",
    }
    import importlib
    from typing import cast

    module_path, class_name = mapping[waveform].rsplit(".", 1)
    module = importlib.import_module(module_path)
    cls = getattr(module, class_name)
    return cast("BaseGenerator", cls(waveform))
