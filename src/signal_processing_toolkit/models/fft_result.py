from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np


@dataclass(frozen=True, slots=True)
class SpectrumPeak:
    frequency: float
    magnitude: float
    magnitude_db: float
    phase: float
    index: int
    channel: int = 0


@dataclass
class FFTResult:
    """Calibrated spectral arrays plus the raw transform needed for inversion."""

    frequencies: np.ndarray
    magnitude: np.ndarray
    phase: np.ndarray
    n_points: int = 0
    sampling_rate: float = 0.0
    spectrum: np.ndarray | None = None
    invertible: bool = False
    power: np.ndarray | None = None
    psd: np.ndarray | None = None
    one_sided: bool = False
    input_was_real: bool = True
    window_coherent_gain: float = 1.0
    peaks: list[SpectrumPeak] = field(default_factory=list)
    db_reference: float = 1.0
    db_floor: float = -300.0

    def __post_init__(self) -> None:
        self.frequencies = np.asarray(self.frequencies, dtype=float)
        self.magnitude = np.asarray(self.magnitude, dtype=float)
        self.phase = np.asarray(self.phase, dtype=float)
        self.spectrum = (
            self.magnitude * np.exp(1j * self.phase)
            if self.spectrum is None
            else np.asarray(self.spectrum)
        )
        self.power = (
            self.magnitude**2 if self.power is None else np.asarray(self.power, dtype=float)
        )
        self.psd = None if self.psd is None else np.asarray(self.psd, dtype=float)
        if self.db_reference <= 0 or not np.isfinite(self.db_reference):
            raise ValueError("dB reference must be finite and positive")
        if self.n_points < 0:
            raise ValueError("n_points cannot be negative")

    @property
    def magnitude_db(self) -> np.ndarray:
        return self.to_db(self.magnitude, reference=self.db_reference)

    def to_db(
        self,
        values: np.ndarray | None = None,
        *,
        reference: float = 1.0,
        floor_db: float | None = None,
        power: bool = False,
    ) -> np.ndarray:
        """Convert amplitude (20 log10) or power (10 log10) relative to a reference."""
        if reference <= 0 or not np.isfinite(reference):
            raise ValueError("dB reference must be finite and positive")
        floor = self.db_floor if floor_db is None else float(floor_db)
        if not np.isfinite(floor):
            raise ValueError("dB floor must be finite")
        array = self.magnitude if values is None else np.asarray(values)
        with np.errstate(divide="ignore"):
            result = (10.0 if power else 20.0) * np.log10(np.abs(array) / reference)
        return np.maximum(result, floor)

    @property
    def nyquist_frequency(self) -> float:
        return self.sampling_rate / 2.0

    @property
    def frequency_resolution(self) -> float:
        return self.sampling_rate / self.n_points if self.n_points > 0 else 0.0

    @property
    def bin_count(self) -> int:
        return int(self.frequencies.size)

    @property
    def has_nyquist_bin(self) -> bool:
        return self.one_sided and self.n_points > 0 and self.n_points % 2 == 0

    @property
    def dominant_frequency(self) -> float:
        if self.magnitude.size == 0:
            return 0.0
        values = self.magnitude[:, 0] if self.magnitude.ndim == 2 else self.magnitude
        return float(self.frequencies[int(np.argmax(values))])

    @property
    def total_power(self) -> float:
        power = self.power
        assert power is not None
        return float(np.sum(power))

    @property
    def positive_spectrum(self) -> FFTResult:
        if self.one_sided:
            return self
        mask = self.frequencies >= 0
        spectrum = self.spectrum
        power = self.power
        assert spectrum is not None and power is not None
        return FFTResult(
            frequencies=self.frequencies[mask],
            magnitude=self.magnitude[mask],
            phase=self.phase[mask],
            n_points=self.n_points,
            sampling_rate=self.sampling_rate,
            spectrum=spectrum[mask],
            # Removing negative-frequency bins from a genuinely two-sided
            # transform discards information and cannot remain invertible.
            invertible=False,
            power=power[mask],
            psd=None if self.psd is None else self.psd[mask],
            input_was_real=self.input_was_real,
            window_coherent_gain=self.window_coherent_gain,
        )

    def find_peaks(self, min_height: float = 0.1, min_distance: int = 5) -> list[SpectrumPeak]:
        from scipy.signal import find_peaks

        magnitude = self.magnitude[:, np.newaxis] if self.magnitude.ndim == 1 else self.magnitude
        phase = self.phase[:, np.newaxis] if self.phase.ndim == 1 else self.phase
        magnitude_db = self.magnitude_db
        magnitude_db = magnitude_db[:, np.newaxis] if magnitude_db.ndim == 1 else magnitude_db
        peaks: list[SpectrumPeak] = []
        for channel in range(magnitude.shape[1]):
            indices, _ = find_peaks(magnitude[:, channel], height=min_height, distance=min_distance)
            peaks.extend(
                SpectrumPeak(
                    float(self.frequencies[index]),
                    float(magnitude[index, channel]),
                    float(magnitude_db[index, channel]),
                    float(phase[index, channel]),
                    int(index),
                    channel,
                )
                for index in indices
            )
        self.peaks = peaks
        return peaks
