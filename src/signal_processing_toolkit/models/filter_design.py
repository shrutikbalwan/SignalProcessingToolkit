from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np

from signal_processing_toolkit.models.enums import DesignMethod, FilterType, ResponseType


@dataclass
class FilterCoefficients:
    b: np.ndarray
    a: np.ndarray
    order: int = 0
    sos: np.ndarray | None = None

    def __post_init__(self) -> None:
        self.b = np.asarray(self.b, dtype=float)
        self.a = np.asarray(self.a, dtype=float)
        self.sos = None if self.sos is None else np.asarray(self.sos, dtype=float)
        if self.b.ndim != 1 or self.a.ndim != 1 or self.b.size == 0 or self.a.size == 0:
            raise ValueError("b and a must be non-empty one-dimensional coefficient arrays")
        if self.sos is not None and (self.sos.ndim != 2 or self.sos.shape[1] != 6):
            raise ValueError("SOS coefficients must have shape (sections, 6)")
        if self.order == 0:
            self.order = max(len(self.b), len(self.a)) - 1

    @property
    def is_sos(self) -> bool:
        return self.sos is not None

    @property
    def poles(self) -> np.ndarray:
        from scipy import signal as sp_signal

        return sp_signal.sos2zpk(self.sos)[1] if self.sos is not None else np.roots(self.a)

    @property
    def is_stable(self) -> bool:
        return bool(np.all(np.abs(self.poles) < 1.0))

    @property
    def maximum_pole_radius(self) -> float:
        poles = self.poles
        return float(np.max(np.abs(poles))) if poles.size else 0.0


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
    window: str | tuple[str, float] = "hamming"

    def __post_init__(self) -> None:
        if self.order < 1:
            raise ValueError(f"Invalid filter order: {self.order}")
        if self.sampling_rate <= 0:
            raise ValueError(f"Invalid sampling rate: {self.sampling_rate}")
        cutoff = (
            tuple(float(value) for value in self.cutoff_frequency)
            if isinstance(self.cutoff_frequency, tuple)
            else (float(self.cutoff_frequency),)
        )
        if any(not np.isfinite(value) or value <= 0 or value >= self.nyquist for value in cutoff):
            raise ValueError(f"Cutoff frequencies must be strictly between 0 and {self.nyquist} Hz")
        is_band = self.filter_type in (FilterType.BANDPASS, FilterType.BANDSTOP)
        if is_band != (len(cutoff) == 2):
            raise ValueError("Band filters require two cutoffs; low/high-pass filters require one")
        if len(cutoff) == 2 and cutoff[0] >= cutoff[1]:
            raise ValueError("Band cutoff frequencies must be strictly increasing")

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
