from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

import numpy as np


class QFormat(StrEnum):
    Q7 = "q7"
    Q15 = "q15"
    Q31 = "q31"

    @property
    def bits(self) -> int:
        return int(self.value[1:])

    @property
    def scale(self) -> int:
        return 1 << self.bits

    @property
    def limits(self) -> tuple[int, int]:
        return -(1 << self.bits), (1 << self.bits) - 1

    @property
    def storage_bits(self) -> int:
        return self.bits + 1


class RoundingMode(StrEnum):
    NEAREST = "nearest"
    FLOOR = "floor"
    CEIL = "ceil"
    TRUNCATE = "truncate"


class OverflowMode(StrEnum):
    SATURATE = "saturate"
    WRAP = "wrap"
    RAISE = "raise"


@dataclass(frozen=True)
class FixedPointConfig:
    """Rules used by the simulator and emitted as export metadata."""

    format: QFormat = QFormat.Q15
    rounding: RoundingMode = RoundingMode.NEAREST
    overflow: OverflowMode = OverflowMode.SATURATE

    def __post_init__(self) -> None:
        object.__setattr__(self, "format", QFormat(self.format))
        object.__setattr__(self, "rounding", RoundingMode(self.rounding))
        object.__setattr__(self, "overflow", OverflowMode(self.overflow))


@dataclass(frozen=True)
class FixedPointResult:
    integer: np.ndarray
    values: np.ndarray
    config: FixedPointConfig
    clipped: int = 0


def _round(values: np.ndarray, mode: RoundingMode) -> np.ndarray:
    if mode == RoundingMode.NEAREST:
        return np.floor(values + 0.5)
    if mode == RoundingMode.FLOOR:
        return np.floor(values)
    if mode == RoundingMode.CEIL:
        return np.ceil(values)
    return np.trunc(values)


def quantize(values: np.ndarray, config: FixedPointConfig) -> tuple[np.ndarray, int]:
    values = np.asarray(values, dtype=np.float64)
    if not np.all(np.isfinite(values)):
        raise ValueError("fixed-point conversion requires finite values")
    low, high = config.format.limits
    raw = _round(values * config.format.scale, config.rounding).astype(np.int64)
    clipped = int(np.count_nonzero((raw < low) | (raw > high)))
    if config.overflow == OverflowMode.RAISE and clipped:
        raise OverflowError(f"{clipped} values exceed {config.format.value} range")
    if config.overflow == OverflowMode.SATURATE:
        raw = np.clip(raw, low, high)
    elif config.overflow == OverflowMode.WRAP:
        modulus = 1 << config.format.bits
        raw = ((raw - low) % modulus) + low
    return raw, clipped


def simulate_fixed(values: np.ndarray, config: FixedPointConfig | None = None) -> FixedPointResult:
    """Quantize and dequantize values using explicit embedded arithmetic rules."""
    config = config or FixedPointConfig()
    integer, clipped = quantize(values, config)
    return FixedPointResult(
        integer, integer.astype(np.float64) / config.format.scale, config, clipped
    )


def quantized_multiply(a: int, b: int, config: FixedPointConfig) -> int:
    """Multiply two Q values and return a Q value with configured overflow rules."""
    scaled = _round(np.asarray([a * b / config.format.scale]), config.rounding)
    integer, _ = quantize(scaled / config.format.scale, config)
    return int(integer[0])
