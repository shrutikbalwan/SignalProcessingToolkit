from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TypeVar

import numpy as np

from src.models.signal import Signal

T = TypeVar("T", bound="BaseOperation")


class BaseOperation(ABC):
    @abstractmethod
    def apply(self, signal: Signal, **kwargs) -> Signal:
        pass

    def __call__(self, signal: Signal, **kwargs) -> Signal:
        return self.apply(signal, **kwargs)


class UnaryOperation(BaseOperation):
    @abstractmethod
    def apply(self, signal: Signal, **kwargs) -> Signal:
        pass


class BinaryOperation(BaseOperation):
    @abstractmethod
    def apply(self, signal1: Signal, signal2: Signal, **kwargs) -> Signal:  # type: ignore[override]
        pass


def validate_same_sampling_rate(signal1: Signal, signal2: Signal) -> None:
    if signal1.sampling_rate != signal2.sampling_rate:
        raise ValueError(
            f"Sampling rate mismatch: {signal1.sampling_rate} vs {signal2.sampling_rate}"
        )


def validate_same_length(signal1: Signal, signal2: Signal) -> None:
    if signal1.length != signal2.length:
        raise ValueError(f"Signal length mismatch: {signal1.length} vs {signal2.length}")


def align_signals(signal1: Signal, signal2: Signal) -> tuple[np.ndarray, np.ndarray]:
    validate_same_sampling_rate(signal1, signal2)

    len1, len2 = signal1.length, signal2.length
    if len1 == len2:
        return signal1.time_data, signal2.time_data

    min_len = min(len1, len2)
    return signal1.time_data[:min_len], signal2.time_data[:min_len]
