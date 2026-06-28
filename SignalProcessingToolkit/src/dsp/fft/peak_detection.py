from __future__ import annotations

import numpy as np
from scipy.signal import find_peaks, peak_prominences

from src.models.fft_result import FFTResult, SpectrumPeak


def find_spectrum_peaks(
    fft_result: FFTResult,
    min_height: float = 0.1,
    min_distance: int = 5,
    prominence: float | None = None,
    width: float | None = None,
) -> list[SpectrumPeak]:
    magnitude = fft_result.magnitude[: len(fft_result.magnitude) // 2]
    frequencies = fft_result.frequencies[: len(fft_result.frequencies) // 2]
    phase = fft_result.phase[: len(fft_result.phase) // 2]

    height = min_height * np.max(magnitude) if min_height < 1 else min_height

    peak_indices, properties = find_peaks(
        magnitude,
        height=height,
        distance=min_distance,
        prominence=prominence,
        width=width,
    )

    peaks = []
    for idx in peak_indices:
        peaks.append(
            SpectrumPeak(
                frequency=float(frequencies[idx]),
                magnitude=float(magnitude[idx]),
                magnitude_db=float(20 * np.log10(max(magnitude[idx], 1e-10))),
                phase=float(phase[idx]),
                index=int(idx),
            )
        )

    return peaks


def find_peaks_by_prominence(
    fft_result: FFTResult,
    min_prominence: float = 0.1,
    min_distance: int = 5,
) -> list[SpectrumPeak]:
    magnitude = fft_result.magnitude[: len(fft_result.magnitude) // 2]
    frequencies = fft_result.frequencies[: len(fft_result.frequencies) // 2]
    phase = fft_result.phase[: len(fft_result.phase) // 2]

    peak_indices, properties = find_peaks(
        magnitude,
        distance=min_distance,
        prominence=min_prominence * np.max(magnitude),
    )

    prominences = peak_prominences(magnitude, peak_indices)[0]

    peaks = []
    for idx, _prom in zip(peak_indices, prominences, strict=False):
        peaks.append(
            SpectrumPeak(
                frequency=float(frequencies[idx]),
                magnitude=float(magnitude[idx]),
                magnitude_db=float(20 * np.log10(max(magnitude[idx], 1e-10))),
                phase=float(phase[idx]),
                index=int(idx),
            )
        )

    return peaks


def find_harmonic_peaks(
    fft_result: FFTResult,
    fundamental_freq: float,
    max_harmonics: int = 10,
    tolerance: float = 0.02,
) -> list[SpectrumPeak]:
    peaks = find_spectrum_peaks(fft_result, min_height=0.05)

    harmonic_peaks = []
    for h in range(1, max_harmonics + 1):
        expected_freq = fundamental_freq * h
        matching = [
            p for p in peaks if abs(p.frequency - expected_freq) / expected_freq < tolerance
        ]

        if matching:
            best = max(matching, key=lambda p: p.magnitude)
            harmonic_peaks.append(best)

    return harmonic_peaks


def estimate_fundamental_frequency(
    fft_result: FFTResult,
    min_freq: float = 20.0,
    max_freq: float = 5000.0,
) -> float:
    peaks = find_spectrum_peaks(fft_result, min_height=0.05)

    candidates = [p for p in peaks if min_freq <= p.frequency <= max_freq]

    if not candidates:
        return 0.0

    candidates.sort(key=lambda p: p.magnitude, reverse=True)
    return candidates[0].frequency


def peak_interpolation(
    fft_result: FFTResult,
    peak_index: int,
) -> tuple[float, float]:
    magnitude = fft_result.magnitude

    if peak_index <= 0 or peak_index >= len(magnitude) - 1:
        freq = fft_result.frequencies[peak_index]
        mag = magnitude[peak_index]
        return freq, mag

    y1 = magnitude[peak_index - 1]
    y2 = magnitude[peak_index]
    y3 = magnitude[peak_index + 1]

    x = (y3 - y1) / (2 * (2 * y2 - y1 - y3)) if (2 * y2 - y1 - y3) != 0 else 0
    x = np.clip(x, -0.5, 0.5)

    freq_res = fft_result.frequency_resolution
    interpolated_freq = fft_result.frequencies[peak_index] + x * freq_res

    if y2 != 0 and y1 != 0 and y3 != 0:
        a = 0.5 * (y1 - 2 * y2 + y3)
        b = 0.5 * (y3 - y1)
        c = y2
        if a != 0:
            interpolated_mag = c - b * b / (4 * a)
        else:
            interpolated_mag = c
    else:
        interpolated_mag = y2

    return float(interpolated_freq), float(interpolated_mag)


def refine_peak_locations(
    fft_result: FFTResult,
    peaks: list[SpectrumPeak],
) -> list[SpectrumPeak]:
    refined = []
    for peak in peaks:
        if peak.index < len(fft_result.magnitude) - 1:
            freq, mag = peak_interpolation(fft_result, peak.index)
            refined.append(
                SpectrumPeak(
                    frequency=freq,
                    magnitude=mag,
                    magnitude_db=20 * np.log10(max(mag, 1e-10)),
                    phase=fft_result.phase[peak.index],
                    index=peak.index,
                )
            )
        else:
            refined.append(peak)
    return refined
