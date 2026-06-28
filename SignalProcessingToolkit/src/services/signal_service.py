from __future__ import annotations

import numpy as np

from src.models.enums import WaveformType
from src.models.signal import Signal


class SignalService:
    def generate(self, waveform: WaveformType, **params: object) -> Signal:
        from src.dsp.generators.base import create_generator

        generator = create_generator(waveform)
        return generator.generate(**params)  # type: ignore[arg-type]

    def add(self, s1: Signal, s2: Signal) -> Signal:
        min_len = min(len(s1.time_data), len(s2.time_data))
        return Signal(
            time_data=s1.time_data[:min_len] + s2.time_data[:min_len],
            sampling_rate=min(s1.sampling_rate, s2.sampling_rate),
        )

    def subtract(self, s1: Signal, s2: Signal) -> Signal:
        min_len = min(len(s1.time_data), len(s2.time_data))
        return Signal(
            time_data=s1.time_data[:min_len] - s2.time_data[:min_len],
            sampling_rate=min(s1.sampling_rate, s2.sampling_rate),
        )

    def multiply(self, s1: Signal, s2: Signal) -> Signal:
        min_len = min(len(s1.time_data), len(s2.time_data))
        return Signal(
            time_data=s1.time_data[:min_len] * s2.time_data[:min_len],
            sampling_rate=min(s1.sampling_rate, s2.sampling_rate),
        )

    def scale(self, signal: Signal, factor: float) -> Signal:
        return Signal(
            time_data=signal.time_data * factor,
            sampling_rate=signal.sampling_rate,
            frequency=signal.frequency,
            amplitude=signal.amplitude * factor,
            phase=signal.phase,
        )

    def normalize(self, signal: Signal) -> Signal:
        max_val = np.max(np.abs(signal.time_data))
        if max_val == 0:
            return signal.copy()
        return Signal(
            time_data=signal.time_data / max_val,
            sampling_rate=signal.sampling_rate,
            frequency=signal.frequency,
            amplitude=1.0,
            phase=signal.phase,
        )

    def time_shift(self, signal: Signal, shift_samples: int) -> Signal:
        return Signal(
            time_data=np.roll(signal.time_data, shift_samples),
            sampling_rate=signal.sampling_rate,
            frequency=signal.frequency,
            amplitude=signal.amplitude,
            phase=signal.phase,
        )

    def time_reverse(self, signal: Signal) -> Signal:
        return Signal(
            time_data=signal.time_data[::-1].copy(),
            sampling_rate=signal.sampling_rate,
            frequency=signal.frequency,
            amplitude=signal.amplitude,
            phase=signal.phase,
        )

    def clip(self, signal: Signal, min_val: float = -1.0, max_val: float = 1.0) -> Signal:
        return Signal(
            time_data=np.clip(signal.time_data, min_val, max_val),
            sampling_rate=signal.sampling_rate,
            frequency=signal.frequency,
            amplitude=signal.amplitude,
            phase=signal.phase,
        )

    def rectify(self, signal: Signal, half: str = "full") -> Signal:
        if half == "full":
            data = np.abs(signal.time_data)
        elif half == "positive":
            data = np.maximum(signal.time_data, 0)
        elif half == "negative":
            data = np.minimum(signal.time_data, 0)
        else:
            raise ValueError(f"Unknown rectification mode: {half}")
        return Signal(
            time_data=data,
            sampling_rate=signal.sampling_rate,
            frequency=signal.frequency,
            amplitude=signal.amplitude,
            phase=signal.phase,
        )

    def mix(self, signals: list[Signal], weights: list[float] | None = None) -> Signal:
        if not signals:
            raise ValueError("At least one signal required for mixing")
        n_weights = weights or [1.0 / len(signals)] * len(signals)
        if len(signals) != len(n_weights):
            raise ValueError("Number of signals and weights must match")
        min_len = min(len(s.time_data) for s in signals)
        min_rate = min(s.sampling_rate for s in signals)
        mixed = np.zeros(min_len)
        for signal, weight in zip(signals, n_weights, strict=False):
            mixed += signal.time_data[:min_len] * weight
        return Signal(time_data=mixed, sampling_rate=min_rate)
