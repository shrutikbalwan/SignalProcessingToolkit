from __future__ import annotations

import numpy as np

from src.models.enums import WindowType


def rectangular(n: int, **kwargs) -> np.ndarray:
    return np.ones(n, dtype=np.float64)


def hamming(n: int, **kwargs) -> np.ndarray:
    return np.hamming(n)


def hanning(n: int, **kwargs) -> np.ndarray:
    return np.hanning(n)


def blackman(n: int, **kwargs) -> np.ndarray:
    return np.blackman(n)


def bartlett(n: int, **kwargs) -> np.ndarray:
    return np.bartlett(n)


def kaiser(n: int, beta: float = 14.0, **kwargs) -> np.ndarray:
    return np.kaiser(n, beta)


def gaussian(n: int, std: float = 0.5, **kwargs) -> np.ndarray:
    return np.exp(-0.5 * (np.linspace(-1, 1, n) / std) ** 2)


def blackman_harris(n: int, **kwargs) -> np.ndarray:
    a0, a1, a2, a3 = 0.35875, 0.48829, 0.14128, 0.01168
    k = np.arange(n)
    return (
        a0
        - a1 * np.cos(2 * np.pi * k / n)
        + a2 * np.cos(4 * np.pi * k / n)
        - a3 * np.cos(6 * np.pi * k / n)
    )


def nuttall(n: int, **kwargs) -> np.ndarray:
    a0, a1, a2, a3 = 0.355768, 0.487396, 0.144232, 0.012604
    k = np.arange(n)
    return (
        a0
        - a1 * np.cos(2 * np.pi * k / n)
        + a2 * np.cos(4 * np.pi * k / n)
        - a3 * np.cos(6 * np.pi * k / n)
    )


def flat_top(n: int, **kwargs) -> np.ndarray:
    a0, a1, a2, a3, a4 = 0.21557895, 0.41663158, 0.277263158, 0.083578947, 0.006947368
    k = np.arange(n)
    return (
        a0
        - a1 * np.cos(2 * np.pi * k / n)
        + a2 * np.cos(4 * np.pi * k / n)
        - a3 * np.cos(6 * np.pi * k / n)
        + a4 * np.cos(8 * np.pi * k / n)
    )


WINDOW_FUNCTIONS = {
    WindowType.RECTANGULAR: rectangular,
    WindowType.HAMMING: hamming,
    WindowType.HANNING: hanning,
    WindowType.BLACKMAN: blackman,
    WindowType.BARTLETT: bartlett,
    WindowType.KAISER: kaiser,
    "gaussian": gaussian,
    "blackman_harris": blackman_harris,
    "nuttall": nuttall,
    "flat_top": flat_top,
}


def create_window(window_type: WindowType | str, n: int, **kwargs) -> np.ndarray:
    if isinstance(window_type, str):
        try:
            window_type = WindowType(window_type)
        except ValueError:
            pass

    func = WINDOW_FUNCTIONS.get(window_type)
    if func is None:
        raise ValueError(f"Unknown window type: {window_type}")

    return func(n, **kwargs)


def window_energy(window: np.ndarray) -> float:
    return float(np.sum(window**2))


def coherent_gain(window: np.ndarray) -> float:
    return float(np.mean(window))


def equivalent_noise_bandwidth(window: np.ndarray, sampling_rate: float = 1.0) -> float:
    n = len(window)
    window_energy = np.sum(window**2)
    coherent_gain = np.mean(window)
    return float(sampling_rate * window_energy / (n * coherent_gain**2))


def scalloping_loss(window: np.ndarray) -> float:
    n = len(window)
    if n % 2 == 0:
        np.pi / n
    else:
        np.pi * (n - 1) / (2 * n)

    freq_response = np.abs(np.fft.rfft(window, n * 10))
    max_response = np.max(freq_response)
    response_at_half_bin = (
        freq_response[len(freq_response) // (2 * n)] if n * 2 < len(freq_response) else max_response
    )

    if max_response > 0:
        return float(1 - response_at_half_bin / max_response)
    return 0.0
