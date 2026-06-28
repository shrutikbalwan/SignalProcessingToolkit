from __future__ import annotations

import numpy as np

from src.models.enums import NoiseType


def generate_white_noise(length: int, std: float = 1.0, seed: int | None = None) -> np.ndarray:
    if seed is not None:
        np.random.seed(seed)
    return np.random.normal(0, std, length)


def generate_pink_noise(length: int, std: float = 1.0, seed: int | None = None) -> np.ndarray:
    if seed is not None:
        np.random.seed(seed)

    white = np.random.normal(0, 1, length)
    n = len(white)

    fft_white = np.fft.rfft(white)
    freqs = np.fft.rfftfreq(n)

    with np.errstate(divide="ignore", invalid="ignore"):
        pink_filter = 1.0 / np.sqrt(np.maximum(freqs, 1e-10))
        pink_filter[0] = 0

    fft_pink = fft_white * pink_filter
    pink = np.fft.irfft(fft_pink, n)

    return pink * std / np.std(pink)


def generate_brownian_noise(length: int, std: float = 1.0, seed: int | None = None) -> np.ndarray:
    if seed is not None:
        np.random.seed(seed)

    white = np.random.normal(0, 1, length)
    brownian = np.cumsum(white)

    return brownian * std / np.std(brownian)


def generate_impulse_noise(
    length: int, density: float = 0.01, amplitude: float = 5.0, seed: int | None = None
) -> np.ndarray:
    if seed is not None:
        np.random.seed(seed)

    noise = np.zeros(length)
    n_impulses = int(length * density)
    indices = np.random.choice(length, n_impulses, replace=False)
    noise[indices] = np.random.choice([-amplitude, amplitude], n_impulses)

    return noise


def generate_blue_noise(length: int, std: float = 1.0, seed: int | None = None) -> np.ndarray:
    if seed is not None:
        np.random.seed(seed)

    white = np.random.normal(0, 1, length)
    n = len(white)

    fft_white = np.fft.rfft(white)
    freqs = np.fft.rfftfreq(n)

    blue_filter = np.sqrt(np.maximum(freqs, 1e-10))
    blue_filter[0] = 0

    fft_blue = fft_white * blue_filter
    blue = np.fft.irfft(fft_blue, n)

    return blue * std / np.std(blue)


def generate_violet_noise(length: int, std: float = 1.0, seed: int | None = None) -> np.ndarray:
    if seed is not None:
        np.random.seed(seed)

    white = np.random.normal(0, 1, length)
    n = len(white)

    fft_white = np.fft.rfft(white)
    freqs = np.fft.rfftfreq(n)

    violet_filter = np.maximum(freqs, 1e-10)
    violet_filter[0] = 0

    fft_violet = fft_white * violet_filter
    violet = np.fft.irfft(fft_violet, n)

    return violet * std / np.std(violet)


def generate_noise(
    noise_type: NoiseType | str, length: int, std: float = 1.0, seed: int | None = None, **kwargs
) -> np.ndarray:
    if isinstance(noise_type, str):
        noise_type = NoiseType(noise_type)

    generators = {
        NoiseType.WHITE: generate_white_noise,
        NoiseType.PINK: generate_pink_noise,
        NoiseType.BROWNIAN: generate_brownian_noise,
        NoiseType.IMPULSE: generate_impulse_noise,
    }

    generator = generators.get(noise_type)
    if generator is None:
        raise ValueError(f"Unknown noise type: {noise_type}")

    result: np.ndarray = generator(length, std, seed)  # type: ignore[operator]
    return result
