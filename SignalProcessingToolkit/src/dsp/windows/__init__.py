from __future__ import annotations

import numpy as np

from src.models.enums import WindowType


def rectangular(n: int, **kwargs) -> np.ndarray:
    if n < 1:
        raise ValueError(f"Window length must be >= 1, got {n}")
    return np.ones(n, dtype=np.float64)


def hamming(n: int, **kwargs) -> np.ndarray:
    if n < 1:
        raise ValueError(f"Window length must be >= 1, got {n}")
    return np.hamming(n)


def hanning(n: int, **kwargs) -> np.ndarray:
    if n < 1:
        raise ValueError(f"Window length must be >= 1, got {n}")
    return np.hanning(n)


def blackman(n: int, **kwargs) -> np.ndarray:
    if n < 1:
        raise ValueError(f"Window length must be >= 1, got {n}")
    return np.blackman(n)


def bartlett(n: int, **kwargs) -> np.ndarray:
    if n < 1:
        raise ValueError(f"Window length must be >= 1, got {n}")
    return np.bartlett(n)


def kaiser(n: int, beta: float = 14.0, **kwargs) -> np.ndarray:
    if n < 1:
        raise ValueError(f"Window length must be >= 1, got {n}")
    return np.kaiser(n, beta)


def gaussian(n: int, std: float = 0.5, **kwargs) -> np.ndarray:
    if n < 1:
        raise ValueError(f"Window length must be >= 1, got {n}")
    x = np.linspace(-1, 1, n)
    return np.exp(-0.5 * (x / std) ** 2)


def blackman_harris(n: int, **kwargs) -> np.ndarray:
    if n < 1:
        raise ValueError(f"Window length must be >= 1, got {n}")
    a0, a1, a2, a3 = 0.35875, 0.48829, 0.14128, 0.01168
    k = np.arange(n)
    return (
        a0
        - a1 * np.cos(2 * np.pi * k / n)
        + a2 * np.cos(4 * np.pi * k / n)
        - a3 * np.cos(6 * np.pi * k / n)
    )


def nuttall(n: int, **kwargs) -> np.ndarray:
    if n < 1:
        raise ValueError(f"Window length must be >= 1, got {n}")
    a0, a1, a2, a3 = 0.355768, 0.487396, 0.144232, 0.012604
    k = np.arange(n)
    return (
        a0
        - a1 * np.cos(2 * np.pi * k / n)
        + a2 * np.cos(4 * np.pi * k / n)
        - a3 * np.cos(6 * np.pi * k / n)
    )


def flat_top(n: int, **kwargs) -> np.ndarray:
    if n < 1:
        raise ValueError(f"Window length must be >= 1, got {n}")
    a0, a1, a2, a3, a4 = 0.21557895, 0.41663158, 0.277263158, 0.083578947, 0.006947368
    k = np.arange(n)
    return (
        a0
        - a1 * np.cos(2 * np.pi * k / n)
        + a2 * np.cos(4 * np.pi * k / n)
        - a3 * np.cos(6 * np.pi * k / n)
        + a4 * np.cos(8 * np.pi * k / n)
    )


def chebyshev(n: int, attenuation: float = 100.0, **kwargs) -> np.ndarray:
    from scipy.signal import chebwin

    if n < 1:
        raise ValueError(f"Window length must be >= 1, got {n}")
    result: np.ndarray = chebwin(n, attenuation)
    return result


def tukey(n: int, alpha: float = 0.5, **kwargs) -> np.ndarray:
    from scipy.signal import tukey as sp_tukey

    if n < 1:
        raise ValueError(f"Window length must be >= 1, got {n}")
    result: np.ndarray = sp_tukey(n, alpha)
    return result


def bohman(n: int, **kwargs) -> np.ndarray:
    if n < 1:
        raise ValueError(f"Window length must be >= 1, got {n}")
    x = np.linspace(-1, 1, n)
    return (1 - np.abs(x)) * np.cos(np.pi * x) + np.sin(np.pi * np.abs(x)) / np.pi


def parzen(n: int, **kwargs) -> np.ndarray:
    if n < 1:
        raise ValueError(f"Window length must be >= 1, got {n}")
    k = (n - 1) / 2
    x = np.arange(n) - k
    x = np.abs(x) / k
    y = np.ones(n)
    mask1 = x <= 0.5
    mask2 = (x > 0.5) & (x <= 1.0)
    y[mask1] = 1 - 6 * x[mask1] ** 2 + 6 * x[mask1] ** 3
    y[mask2] = 2 * (1 - x[mask2]) ** 3
    return y


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
    "chebyshev": chebyshev,
    "tukey": tukey,
    "bohman": bohman,
    "parzen": parzen,
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


def get_window_properties(window: np.ndarray) -> dict:
    n = len(window)
    energy = np.sum(window**2)
    cg = np.mean(window)
    enbw = n * energy / (cg**2) if cg != 0 else float("inf")

    freq_response = np.abs(np.fft.rfft(window, n * 10))
    max_resp = np.max(freq_response)

    first_sidelobe_idx = (
        np.argmax(freq_response[len(freq_response) // n :]) + len(freq_response) // n
    )
    if first_sidelobe_idx < len(freq_response):
        sidelobe_db = 20 * np.log10(freq_response[first_sidelobe_idx] / max_resp)
    else:
        sidelobe_db = -np.inf

    return {
        "length": n,
        "energy": float(energy),
        "coherent_gain": float(cg),
        "equivalent_noise_bandwidth": float(enbw),
        "peak_sidelobe_level_db": float(sidelobe_db),
    }
