from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np

from src.models.enums import DesignMethod, FilterType, ResponseType


@dataclass
class FilterCoefficients:
    b: np.ndarray
    a: np.ndarray
    order: int = 0

    def __post_init__(self) -> None:
        if self.order == 0:
            self.order = max(len(self.b), len(self.a)) - 1


@dataclass
class FrequencyResponse:
    frequencies: np.ndarray
    magnitude: np.ndarray
    phase: np.ndarray
    magnitude_db: np.ndarray = field(init=False)

    def __post_init__(self) -> None:
        self.magnitude_db = 20 * np.log10(np.maximum(self.magnitude, 1e-10))


@dataclass
class PoleZeroMap:
    poles: np.ndarray
    zeros: np.ndarray


@dataclass
class FilterDesign:
    filter_type: FilterType
    response_type: ResponseType
    design_method: DesignMethod
    order: int
    cutoff_frequency: float | tuple[float, float]
    sampling_rate: float
    passband_ripple: float = 1.0
    stopband_attenuation: float = 40.0

    def __post_init__(self) -> None:
        if self.order < 1:
            raise ValueError(f"Invalid filter order: {self.order}")
        if self.sampling_rate <= 0:
            raise ValueError(f"Invalid sampling rate: {self.sampling_rate}")

    @property
    def nyquist(self) -> float:
        return self.sampling_rate / 2.0

    @property
    def normalized_cutoff(self) -> float | tuple[float, float]:
        if isinstance(self.cutoff_frequency, tuple):
            return (
                self.cutoff_frequency[0] / self.nyquist,
                self.cutoff_frequency[1] / self.nyquist,
            )
        return self.cutoff_frequency / self.nyquist
