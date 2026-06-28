from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np


@dataclass
class SpectrumPeak:
    frequency: float
    magnitude: float
    magnitude_db: float
    phase: float
    index: int


@dataclass
class FFTResult:
    frequencies: np.ndarray
    magnitude: np.ndarray
    phase: np.ndarray
    magnitude_db: np.ndarray = field(init=False)
    n_points: int = 0
    sampling_rate: float = 0.0
    peaks: list[SpectrumPeak] = field(default_factory=list)

    def __post_init__(self) -> None:
        eps = 1e-10
        self.magnitude_db = 20 * np.log10(np.maximum(self.magnitude, eps))

    @property
    def nyquist_frequency(self) -> float:
        return self.sampling_rate / 2.0

    @property
    def frequency_resolution(self) -> float:
        return self.sampling_rate / self.n_points if self.n_points > 0 else 0.0

    @property
    def dominant_frequency(self) -> float:
        if not self.peaks:
            return 0.0
        return max(self.peaks, key=lambda p: p.magnitude).frequency

    @property
    def total_power(self) -> float:
        return float(np.sum(self.magnitude**2))

    @property
    def positive_spectrum(self) -> FFTResult:
        if self.n_points == 0:
            return self
        mid = self.n_points // 2
        return FFTResult(
            frequencies=self.frequencies[:mid],
            magnitude=self.magnitude[:mid],
            phase=self.phase[:mid],
            n_points=mid,
            sampling_rate=self.sampling_rate,
        )

    def find_peaks(self, min_height: float = 0.1, min_distance: int = 5) -> list[SpectrumPeak]:
        from scipy.signal import find_peaks

        indices, properties = find_peaks(self.magnitude, height=min_height, distance=min_distance)
        return [
            SpectrumPeak(
                frequency=float(self.frequencies[i]),
                magnitude=float(self.magnitude[i]),
                magnitude_db=float(self.magnitude_db[i]),
                phase=float(self.phase[i]),
                index=int(i),
            )
            for i in indices
        ]
