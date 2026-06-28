from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from scipy.fft import fft, fftfreq

from src.models.enums import WindowType
from src.models.signal import Signal


@dataclass
class WindowMetrics:
    energy: float
    coherent_gain: float
    enbw: float
    scalloping_loss: float
    max_sidelobe_db: float
    mainlobe_width: float


class WindowService:
    def apply(self, signal: Signal, window_type: WindowType, **kwargs: float) -> Signal:
        return signal.apply_window(window_type, **kwargs)

    def create(self, window_type: WindowType, n_points: int, **kwargs: float) -> np.ndarray:
        from src.dsp.windows.base import create_window

        return create_window(window_type, n_points, **kwargs)

    def compare(self, types: list[WindowType], n_points: int) -> dict[WindowType, np.ndarray]:
        return {wt: self.create(wt, n_points) for wt in types}

    def frequency_response(
        self, window: np.ndarray, n_fft: int = 8192
    ) -> tuple[np.ndarray, np.ndarray]:
        H = fft(window, n=n_fft)  # noqa: N806
        H = np.fft.fftshift(H)  # noqa: N806
        freqs = fftfreq(n_fft)
        freqs = np.fft.fftshift(freqs)
        magnitude_db = 20 * np.log10(np.maximum(np.abs(H) / np.max(np.abs(H)), 1e-10))
        return freqs, magnitude_db

    def compute_metrics(
        self, window: np.ndarray | Signal, sampling_rate: float = 1.0
    ) -> WindowMetrics:
        if isinstance(window, Signal):
            window = window.time_data
        from src.dsp.windows.base import (
            coherent_gain,
            equivalent_noise_bandwidth,
            scalloping_loss,
            window_energy,
        )

        _, mag_db = self.frequency_response(window)
        len(window)
        half = len(mag_db) // 2
        pos_mag_db = mag_db[half:]
        (pos_mag_db < -3) & (pos_mag_db >= -100)
        max_sidelobe = float(np.max(pos_mag_db[1:]) if len(pos_mag_db) > 1 else -float("inf"))

        mainlobe_edges = np.where(pos_mag_db <= -3)[0]
        mainlobe_width = 0.0
        if len(mainlobe_edges) > 1:
            mainlobe_width = float(
                (mainlobe_edges[-1] - mainlobe_edges[0]) * sampling_rate / len(mag_db)
            )

        return WindowMetrics(
            energy=window_energy(window),
            coherent_gain=coherent_gain(window),
            enbw=equivalent_noise_bandwidth(window, sampling_rate),
            scalloping_loss=scalloping_loss(window),
            max_sidelobe_db=max_sidelobe,
            mainlobe_width=mainlobe_width,
        )
