from __future__ import annotations

from dataclasses import dataclass

from signal_processing_toolkit.models.signal import Signal


@dataclass
class AliasingReport:
    original_frequency: float
    sampling_rate: float
    nyquist: float
    aliased: bool
    aliased_frequency: float | None = None
    aliased_magnitude: float | None = None


class SamplingService:
    def sample(self, signal: Signal, new_rate: float) -> Signal:
        from signal_processing_toolkit.dsp.sampling.sampler import resample_signal

        return resample_signal(signal, new_rate)

    def reconstruct(self, signal: Signal, original_rate: float) -> Signal:
        return self.sample(signal, original_rate)

    def downsample(self, signal: Signal, factor: int) -> Signal:
        from signal_processing_toolkit.dsp.sampling.sampler import decimate_signal

        return decimate_signal(signal, factor)

    def upsample(self, signal: Signal, factor: int) -> Signal:
        from signal_processing_toolkit.dsp.sampling.sampler import interpolate_signal

        return interpolate_signal(signal, factor)

    def convert_rate(self, signal: Signal, up: int, down: int) -> Signal:
        from signal_processing_toolkit.dsp.sampling.sampler import rational_resample

        return rational_resample(signal, up, down)

    def detect_aliasing(self, signal: Signal, target_rate: float) -> AliasingReport:
        nyquist = target_rate / 2.0
        freq = signal.frequency
        aliased = freq > nyquist
        aliased_freq = None
        if aliased:
            aliased_freq = abs(freq % target_rate)
            if aliased_freq > nyquist:
                aliased_freq = target_rate - aliased_freq
        return AliasingReport(
            original_frequency=freq,
            sampling_rate=target_rate,
            nyquist=nyquist,
            aliased=aliased,
            aliased_frequency=aliased_freq,
        )

    def demo_aliasing(self, signal: Signal, target_rate: float) -> dict:
        report = self.detect_aliasing(signal, target_rate)
        aliased_signal = self.sample(signal, target_rate)
        return {"report": report, "aliased_signal": aliased_signal}
