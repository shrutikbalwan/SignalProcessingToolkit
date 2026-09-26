from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Literal

import numpy as np
from scipy import ndimage
from scipy import signal as sp_signal

from signal_processing_toolkit.dsp.analysis.analytic import signal_envelope
from signal_processing_toolkit.models.signal import Signal


@dataclass(frozen=True, slots=True)
class EventDetectionConfig:
    threshold: float
    direction: Literal["above", "below", "absolute"] = "above"
    minimum_duration: float = 0.0
    minimum_distance: float = 0.0
    hysteresis: float = 0.0
    smoothing: float = 0.0

    def __post_init__(self) -> None:
        if not np.isfinite(self.threshold):
            raise ValueError("threshold must be finite")
        if self.minimum_duration < 0 or self.minimum_distance < 0 or self.smoothing < 0:
            raise ValueError("Durations, distances, and smoothing cannot be negative")
        if self.hysteresis < 0:
            raise ValueError("hysteresis cannot be negative")


@dataclass(frozen=True, slots=True)
class DetectedEvent:
    start_index: int
    end_index: int
    peak_index: int
    start_time: float
    end_time: float
    peak_time: float
    peak_value: float
    channel: int


@dataclass(frozen=True, slots=True)
class EventDetectionResult:
    events: tuple[DetectedEvent, ...]
    parameters: dict[str, object]


def _event_values(data: np.ndarray, direction: str) -> np.ndarray:
    if direction == "absolute":
        return np.abs(data)
    return data if direction == "above" else -data


def detect_events(signal: Signal, config: EventDetectionConfig) -> EventDetectionResult:
    """Detect threshold regions with duration, distance, smoothing, and hysteresis controls."""
    if signal.n_samples == 0:
        return EventDetectionResult((), asdict(config))
    data = signal.time_data[:, np.newaxis] if signal.is_mono else signal.time_data
    sigma = config.smoothing * signal.sampling_rate
    minimum_samples = max(1, int(np.ceil(config.minimum_duration * signal.sampling_rate)))
    distance_samples = max(0, int(np.ceil(config.minimum_distance * signal.sampling_rate)))
    events: list[DetectedEvent] = []
    for channel in range(signal.n_channels):
        values = _event_values(data[:, channel], config.direction)
        if sigma > 0:
            values = ndimage.gaussian_filter1d(values, sigma)
        trigger = config.threshold if config.direction != "below" else -config.threshold
        release = trigger - config.hysteresis
        active = False
        start = 0
        candidates: list[tuple[int, int]] = []
        for index, value in enumerate(values):
            if not active and value >= trigger:
                start, active = index, True
            elif active and value < release:
                if index - start >= minimum_samples:
                    candidates.append((start, index - 1))
                active = False
        if active and signal.n_samples - start >= minimum_samples:
            candidates.append((start, signal.n_samples - 1))
        accepted: list[tuple[int, int]] = []
        for start, end in candidates:
            if accepted and start - accepted[-1][1] <= distance_samples:
                accepted[-1] = (accepted[-1][0], end)
            else:
                accepted.append((start, end))
        for start, end in accepted:
            peak = start + int(np.argmax(values[start : end + 1]))
            events.append(
                DetectedEvent(
                    start,
                    end,
                    peak,
                    float(signal.time_vector[start]),
                    float(signal.time_vector[end]),
                    float(signal.time_vector[peak]),
                    float(data[peak, channel]),
                    channel,
                )
            )
    events.sort(key=lambda event: (event.start_index, event.channel))
    return EventDetectionResult(tuple(events), asdict(config))


def detect_transients(
    signal: Signal,
    *,
    prominence: float,
    minimum_distance: float = 0.0,
    smoothing: float = 0.001,
) -> EventDetectionResult:
    """Detect positive envelope-slope peaks as transient onsets."""
    if prominence <= 0 or not np.isfinite(prominence):
        raise ValueError("prominence must be finite and positive")
    envelope = signal_envelope(signal).time_data
    data = envelope[:, np.newaxis] if signal.is_mono else envelope
    sigma = smoothing * signal.sampling_rate
    distance = max(1, int(np.ceil(minimum_distance * signal.sampling_rate)))
    events: list[DetectedEvent] = []
    for channel in range(signal.n_channels):
        values = data[:, channel]
        if sigma > 0:
            values = ndimage.gaussian_filter1d(values, sigma)
        slope = np.gradient(values) * signal.sampling_rate
        peaks, _ = sp_signal.find_peaks(slope, prominence=prominence, distance=distance)
        for peak in peaks:
            events.append(
                DetectedEvent(
                    int(peak),
                    int(peak),
                    int(peak),
                    float(signal.time_vector[peak]),
                    float(signal.time_vector[peak]),
                    float(signal.time_vector[peak]),
                    float(data[peak, channel]),
                    channel,
                )
            )
    events.sort(key=lambda event: (event.peak_index, event.channel))
    return EventDetectionResult(
        tuple(events),
        {
            "detector": "envelope_slope",
            "prominence": prominence,
            "minimum_distance": minimum_distance,
            "smoothing": smoothing,
        },
    )
