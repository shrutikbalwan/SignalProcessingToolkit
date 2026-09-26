from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from .fixed import FixedPointConfig, quantize


@dataclass(frozen=True)
class FilterSimulation:
    output: np.ndarray
    floating_output: np.ndarray
    error: np.ndarray
    config: FixedPointConfig
    coefficient_memory_bytes: int
    state_memory_bytes: int
    macs: int

    @property
    def rms_error(self) -> float:
        return float(np.sqrt(np.mean(self.error**2))) if self.error.size else 0.0


def _q(value: float, config: FixedPointConfig) -> int:
    return int(quantize(np.asarray([value]), config)[0][0])


def _mul(a: int, b: int, config: FixedPointConfig) -> int:
    product = a * b / config.format.scale
    return _q(product / config.format.scale, config)


def simulate_fir(
    samples: np.ndarray,
    coefficients: np.ndarray,
    config: FixedPointConfig | None = None,
) -> FilterSimulation:
    """Simulate a quantized FIR using a saturating fixed-point accumulator."""
    config = config or FixedPointConfig()
    x = np.asarray(samples, dtype=np.float64).reshape(-1)
    b = np.asarray(coefficients, dtype=np.float64).reshape(-1)
    if not b.size:
        raise ValueError("FIR coefficients cannot be empty")
    qi, _ = quantize(x, config)
    qb, _ = quantize(b, config)
    low, high = config.format.limits
    out = np.zeros(len(qi), dtype=np.int64)
    history = np.zeros(len(qb), dtype=np.int64)
    for index, sample in enumerate(qi):
        history[1:] = history[:-1]
        history[0] = sample
        acc = sum(int(a) * int(c) for a, c in zip(history, qb, strict=True))
        scaled = (
            np.floor(acc / config.format.scale + 0.5)
            if config.rounding.value == "nearest"
            else acc / config.format.scale
        )
        value, _ = quantize(np.asarray([scaled / config.format.scale]), config)
        out[index] = value[0]
    floating = np.convolve(x, b, mode="full")[: len(x)]
    result = out.astype(np.float64) / config.format.scale
    storage = config.format.storage_bits // 8
    return FilterSimulation(
        result,
        floating,
        result - floating,
        config,
        len(qb) * storage,
        len(history) * storage,
        len(x) * len(b),
    )


def simulate_sos(
    samples: np.ndarray,
    sos: np.ndarray,
    config: FixedPointConfig | None = None,
) -> FilterSimulation:
    """Simulate cascaded biquads using quantized direct-form-II state."""
    config = config or FixedPointConfig()
    x = np.asarray(samples, dtype=np.float64).reshape(-1)
    sections = np.asarray(sos, dtype=np.float64)
    if sections.ndim != 2 or sections.shape[1] != 6 or not len(sections):
        raise ValueError("SOS must have shape (sections, 6)")
    qsections, _ = quantize(sections, config)
    states = np.zeros((len(sections), 2), dtype=np.int64)
    out = np.zeros(len(x), dtype=np.int64)
    qx, _ = quantize(x, config)
    for i, sample in enumerate(qx):
        value = int(sample)
        for section, coeff in enumerate(qsections):
            b0, b1, b2, a0, a1, a2 = (int(v) for v in coeff)
            if a0 == 0:
                raise ValueError("SOS a0 cannot be zero")
            y = (b0 * value + states[section, 0]) // a0
            states[section, 0] = b1 * value - a1 * y + states[section, 1]
            states[section, 1] = b2 * value - a2 * y
            value = int(np.clip(y, *config.format.limits))
        out[i] = value
    floating = x.copy()
    for section in sections:
        b0, b1, b2, a0, a1, a2 = section
        zi = np.zeros(2)
        y = np.empty_like(floating)
        for i, value in enumerate(floating):
            y[i], zi = (
                (b0 * value + zi[0]) / a0,
                np.array(
                    [
                        (b1 * value - a1 * ((b0 * value + zi[0]) / a0) + zi[1]),
                        b2 * value - a2 * ((b0 * value + zi[0]) / a0),
                    ]
                ),
            )
        floating = y
    result = out.astype(np.float64) / config.format.scale
    storage = config.format.storage_bits // 8
    return FilterSimulation(
        result,
        floating,
        result - floating,
        config,
        sections.size * storage,
        states.size * storage,
        len(x) * len(sections) * 5,
    )
