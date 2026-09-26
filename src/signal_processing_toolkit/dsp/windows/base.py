from __future__ import annotations

from collections.abc import Callable

import numpy as np
from scipy.signal import windows

from signal_processing_toolkit.models.enums import WindowType


def _length(n: int) -> int:
    if isinstance(n, bool) or int(n) != n or n < 1:
        raise ValueError(f"Window length must be a positive integer, got {n!r}")
    return int(n)


def rectangular(n: int, **kwargs: float) -> np.ndarray:
    return np.asarray(windows.boxcar(_length(n), sym=True), dtype=float)


def hamming(n: int, **kwargs: float) -> np.ndarray:
    return np.asarray(windows.hamming(_length(n), sym=True), dtype=float)


def hanning(n: int, **kwargs: float) -> np.ndarray:
    return np.asarray(windows.hann(_length(n), sym=True), dtype=float)


def blackman(n: int, **kwargs: float) -> np.ndarray:
    return np.asarray(windows.blackman(_length(n), sym=True), dtype=float)


def bartlett(n: int, **kwargs: float) -> np.ndarray:
    return np.asarray(windows.bartlett(_length(n), sym=True), dtype=float)


def kaiser(n: int, beta: float = 14.0, **kwargs: float) -> np.ndarray:
    return np.asarray(windows.kaiser(_length(n), beta, sym=True), dtype=float)


def gaussian(n: int, std: float = 0.5, **kwargs: float) -> np.ndarray:
    length = _length(n)
    return np.asarray(
        windows.gaussian(length, std * max(1, (length - 1) / 2), sym=True), dtype=float
    )


def blackman_harris(n: int, **kwargs: float) -> np.ndarray:
    return np.asarray(windows.blackmanharris(_length(n), sym=True), dtype=float)


def nuttall(n: int, **kwargs: float) -> np.ndarray:
    return np.asarray(windows.nuttall(_length(n), sym=True), dtype=float)


def flat_top(n: int, **kwargs: float) -> np.ndarray:
    return np.asarray(windows.flattop(_length(n), sym=True), dtype=float)


def chebyshev(n: int, attenuation: float = 100.0, **kwargs: float) -> np.ndarray:
    return np.asarray(windows.chebwin(_length(n), attenuation, sym=True), dtype=float)


def tukey(n: int, alpha: float = 0.5, **kwargs: float) -> np.ndarray:
    return np.asarray(windows.tukey(_length(n), alpha, sym=True), dtype=float)


def bohman(n: int, **kwargs: float) -> np.ndarray:
    return np.asarray(windows.bohman(_length(n), sym=True), dtype=float)


def parzen(n: int, **kwargs: float) -> np.ndarray:
    return np.asarray(windows.parzen(_length(n), sym=True), dtype=float)


WindowFunction = Callable[..., np.ndarray]
WINDOW_FUNCTIONS: dict[WindowType | str, WindowFunction] = {
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


def create_window(window_type: WindowType | str, n: int, **kwargs: float) -> np.ndarray:
    if isinstance(window_type, str):
        try:
            window_type = WindowType(window_type)
        except ValueError:
            pass
    function = WINDOW_FUNCTIONS.get(window_type)
    if function is None:
        raise ValueError(f"Unknown window type: {window_type}")
    return function(n, **kwargs)


def window_energy(window: np.ndarray) -> float:
    return float(np.sum(np.abs(window) ** 2))


def coherent_gain(window: np.ndarray) -> float:
    if window.size == 0:
        raise ValueError("Window cannot be empty")
    return float(np.abs(np.sum(window)) / window.size)


def equivalent_noise_bandwidth(window: np.ndarray, sampling_rate: float = 1.0) -> float:
    """Equivalent noise bandwidth in Hz: fs * sum(w²) / |sum(w)|²."""
    total = np.abs(np.sum(window)) ** 2
    if total == 0:
        return float("inf")
    return float(sampling_rate * np.sum(np.abs(window) ** 2) / total)


def scalloping_loss(window: np.ndarray) -> float:
    """Half-bin amplitude loss as a fraction of the on-bin response."""
    if window.size == 0:
        raise ValueError("Window cannot be empty")
    indices = np.arange(window.size)
    on_bin = np.abs(np.sum(window))
    half_bin = np.abs(np.sum(window * np.exp(-1j * np.pi * indices / window.size)))
    return 0.0 if on_bin == 0 else float(1.0 - half_bin / on_bin)


def get_window_properties(window: np.ndarray) -> dict[str, float | int]:
    length = len(window)
    return {
        "length": length,
        "energy": window_energy(window),
        "coherent_gain": coherent_gain(window),
        "equivalent_noise_bandwidth": equivalent_noise_bandwidth(window) * length,
        "scalloping_loss": scalloping_loss(window),
    }
