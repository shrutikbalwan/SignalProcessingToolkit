from __future__ import annotations

import numpy as np

from signal_processing_toolkit.models.enums import WaveformType
from signal_processing_toolkit.models.signal import Signal


class SignalService:
    def generate(self, waveform: WaveformType, **params: object) -> Signal:
        from signal_processing_toolkit.dsp.generators.base import create_generator

        generator = create_generator(waveform)
        return generator.generate(**params)  # type: ignore[arg-type]

    def add(self, s1: Signal, s2: Signal) -> Signal:
        s1.validate_compatibility(s2)
        min_len = min(len(s1.time_data), len(s2.time_data))
        return s1.updated(
            time_data=s1.time_data[:min_len] + s2.time_data[:min_len],
            operation="add",
            parameters={"other_signal_id": s2.metadata.id},
        )

    def subtract(self, s1: Signal, s2: Signal) -> Signal:
        s1.validate_compatibility(s2)
        min_len = min(len(s1.time_data), len(s2.time_data))
        return s1.updated(
            time_data=s1.time_data[:min_len] - s2.time_data[:min_len],
            operation="subtract",
            parameters={"other_signal_id": s2.metadata.id},
        )

    def multiply(self, s1: Signal, s2: Signal) -> Signal:
        s1.validate_compatibility(s2)
        min_len = min(len(s1.time_data), len(s2.time_data))
        return s1.updated(
            time_data=s1.time_data[:min_len] * s2.time_data[:min_len],
            operation="multiply",
            parameters={"other_signal_id": s2.metadata.id},
        )

    def scale(self, signal: Signal, factor: float) -> Signal:
        return signal.updated(
            time_data=signal.time_data * factor,
            amplitude=signal.amplitude * factor,
            operation="scale",
            parameters={"factor": factor},
        )

    def normalize(self, signal: Signal) -> Signal:
        max_val = np.max(np.abs(signal.time_data))
        if max_val == 0:
            return signal.copy()
        return signal.updated(
            time_data=signal.time_data / max_val,
            amplitude=1.0,
            operation="normalize_peak",
        )

    def time_shift(self, signal: Signal, shift_samples: int) -> Signal:
        from signal_processing_toolkit.dsp.operations.time_shift import TimeShiftOperation

        return TimeShiftOperation().apply(signal, shift_samples=shift_samples)

    def circular_shift(self, signal: Signal, shift_samples: int) -> Signal:
        from signal_processing_toolkit.dsp.operations.time_shift import CircularShiftOperation

        return CircularShiftOperation().apply(signal, shift_samples=shift_samples)

    def time_reverse(self, signal: Signal) -> Signal:
        return signal.updated(
            time_data=signal.time_data[::-1].copy(),
            operation="time_reverse",
        )

    def clip(self, signal: Signal, min_val: float = -1.0, max_val: float = 1.0) -> Signal:
        if signal.is_complex:
            raise TypeError("Clipping is undefined for complex-valued samples")
        return signal.updated(
            time_data=np.clip(signal.time_data, min_val, max_val),
            operation="clip",
            parameters={"minimum": min_val, "maximum": max_val},
        )

    def rectify(self, signal: Signal, half: str = "full") -> Signal:
        if signal.is_complex and half != "full":
            raise TypeError("Half-wave rectification is undefined for complex-valued samples")
        if half == "full":
            data = np.abs(signal.time_data)
        elif half == "positive":
            data = np.maximum(signal.time_data, 0)
        elif half == "negative":
            data = np.minimum(signal.time_data, 0)
        else:
            raise ValueError(f"Unknown rectification mode: {half}")
        return signal.updated(
            time_data=data,
            units=signal.units,
            operation="rectify",
            parameters={"mode": half},
        )

    def mix(self, signals: list[Signal], weights: list[float] | None = None) -> Signal:
        if not signals:
            raise ValueError("At least one signal required for mixing")
        n_weights = weights or [1.0 / len(signals)] * len(signals)
        if len(signals) != len(n_weights):
            raise ValueError("Number of signals and weights must match")
        min_len = min(len(s.time_data) for s in signals)
        for signal in signals[1:]:
            signals[0].validate_compatibility(signal)
        mixed = np.zeros_like(
            signals[0].time_data[:min_len], dtype=np.result_type(*[s.time_data for s in signals])
        )
        for signal, weight in zip(signals, n_weights, strict=False):
            mixed += signal.time_data[:min_len] * weight
        return signals[0].updated(
            time_data=mixed,
            operation="mix",
            parameters={
                "signal_ids": [signal.metadata.id for signal in signals],
                "weights": n_weights,
            },
        )
