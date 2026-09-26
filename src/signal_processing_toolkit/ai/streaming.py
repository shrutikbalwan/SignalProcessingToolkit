"""Sliding-window inference, probability smoothing, and contextual events."""

from __future__ import annotations

import json
from collections import deque
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Protocol

import numpy as np

from signal_processing_toolkit.ai.model import InferenceBatch
from signal_processing_toolkit.streaming.model import ChannelMetadata, StreamChunk


class WindowModel(Protocol):
    def predict(self, windows: np.ndarray) -> InferenceBatch: ...


@dataclass(frozen=True, slots=True)
class InferencePoint:
    sequence: int
    device_timestamp: float
    host_timestamp: float
    labels: tuple[str, ...]
    probabilities: tuple[float, ...]
    confidence: float
    predicted_label: str
    latency_seconds: float


@dataclass(frozen=True, slots=True)
class DetectionSettings:
    threshold: float = 0.8
    smoothing_window: int = 1
    cooldown_seconds: float = 0.0
    enabled_labels: tuple[str, ...] | None = None

    def __post_init__(self) -> None:
        if not 0 <= self.threshold <= 1:
            raise ValueError("threshold must be between zero and one")
        if self.smoothing_window <= 0:
            raise ValueError("smoothing_window must be positive")
        if not np.isfinite(self.cooldown_seconds) or self.cooldown_seconds < 0:
            raise ValueError("cooldown_seconds must be finite and non-negative")


@dataclass(frozen=True, slots=True)
class DetectedEvent:
    label: str
    confidence: float
    sequence: int
    device_timestamp: float
    host_timestamp: float
    probabilities: Mapping[str, float]
    context_samples: np.ndarray | None = None
    sampling_rate: float | None = None
    channels: tuple[ChannelMetadata, ...] = ()

    def with_context(
        self,
        samples: np.ndarray,
        *,
        sampling_rate: float,
        channels: tuple[ChannelMetadata, ...],
        trigger_sample: int,
        before_samples: int,
        after_samples: int,
    ) -> DetectedEvent:
        """Attach a bounded sample-major region surrounding the trigger."""
        data = np.asarray(samples)
        if data.ndim not in (1, 2):
            raise ValueError("Context must be sample-major mono or multichannel data")
        if not 0 <= trigger_sample < data.shape[0]:
            raise ValueError("trigger_sample is outside the available signal")
        if before_samples < 0 or after_samples < 0:
            raise ValueError("Context sizes cannot be negative")
        start = max(0, trigger_sample - before_samples)
        stop = min(data.shape[0], trigger_sample + after_samples + 1)
        return DetectedEvent(
            label=self.label,
            confidence=self.confidence,
            sequence=self.sequence,
            device_timestamp=self.device_timestamp,
            host_timestamp=self.host_timestamp,
            probabilities=self.probabilities,
            context_samples=data[start:stop].copy(),
            sampling_rate=sampling_rate,
            channels=channels,
        )

    def save(self, directory: str | Path) -> tuple[Path, Path]:
        """Persist event metadata and signal context without pickled objects."""
        target = Path(directory)
        target.mkdir(parents=True, exist_ok=True)
        stem = f"event_{self.sequence}_{self.label}"
        metadata_path = target / f"{stem}.json"
        samples_path = target / f"{stem}.npz"
        metadata_path.write_text(
            json.dumps(
                {
                    "label": self.label,
                    "confidence": self.confidence,
                    "sequence": self.sequence,
                    "device_timestamp": self.device_timestamp,
                    "host_timestamp": self.host_timestamp,
                    "probabilities": dict(self.probabilities),
                    "sampling_rate": self.sampling_rate,
                    "channels": [
                        {"name": channel.name, "unit": channel.unit} for channel in self.channels
                    ],
                },
                indent=2,
            ),
            encoding="utf-8",
        )
        np.savez_compressed(
            samples_path,
            samples=np.empty(0) if self.context_samples is None else self.context_samples,
        )
        return metadata_path, samples_path


class EventDetector:
    """Moving-average threshold detector with per-class event cooldown."""

    def __init__(self, labels: tuple[str, ...], settings: DetectionSettings | None = None) -> None:
        self.labels = labels
        self.settings = settings or DetectionSettings()
        self._history: deque[np.ndarray] = deque(maxlen=self.settings.smoothing_window)
        self._last_event: dict[str, float] = {}

    def reset(self) -> None:
        self._history.clear()
        self._last_event.clear()

    def update(self, point: InferencePoint) -> DetectedEvent | None:
        if point.labels != self.labels:
            raise ValueError("Inference labels changed within a detector")
        self._history.append(np.asarray(point.probabilities, dtype=float))
        smoothed = np.mean(self._history, axis=0)
        index = int(np.argmax(smoothed))
        label = self.labels[index]
        confidence = float(smoothed[index])
        enabled = self.settings.enabled_labels
        if confidence < self.settings.threshold or (enabled is not None and label not in enabled):
            return None
        last = self._last_event.get(label, -np.inf)
        if point.device_timestamp - last < self.settings.cooldown_seconds:
            return None
        self._last_event[label] = point.device_timestamp
        return DetectedEvent(
            label=label,
            confidence=confidence,
            sequence=point.sequence,
            device_timestamp=point.device_timestamp,
            host_timestamp=point.host_timestamp,
            probabilities=dict(zip(self.labels, smoothed.tolist(), strict=True)),
        )


class SlidingWindowInference:
    """Incrementally produce overlapping inference windows across chunk boundaries."""

    def __init__(self, model: WindowModel, window_samples: int, hop_samples: int) -> None:
        if window_samples <= 0 or not 0 < hop_samples <= window_samples:
            raise ValueError("Require 0 < hop_samples <= window_samples")
        self.model = model
        self.window_samples = window_samples
        self.hop_samples = hop_samples
        self._samples: np.ndarray | None = None
        self._buffer_start_timestamp: float | None = None
        self._sampling_rate: float | None = None

    def reset(self) -> None:
        self._samples = None
        self._buffer_start_timestamp = None
        self._sampling_rate = None

    def process(self, chunk: StreamChunk) -> list[InferencePoint]:
        if self._sampling_rate is None:
            self._sampling_rate = chunk.sampling_rate
        elif not np.isclose(chunk.sampling_rate, self._sampling_rate, rtol=0, atol=0):
            raise ValueError("Stream sampling rate changed during inference")
        values = chunk.samples[:, np.newaxis] if chunk.samples.ndim == 1 else chunk.samples
        if self._samples is not None and values.shape[1] != self._samples.shape[1]:
            raise ValueError("Stream channel count changed during inference")
        if self._samples is None:
            self._samples = values.copy()
            self._buffer_start_timestamp = chunk.device_timestamp
        else:
            self._samples = np.concatenate((self._samples, values), axis=0)
        points: list[InferencePoint] = []
        while self._samples.shape[0] >= self.window_samples:
            window = self._samples[: self.window_samples]
            result = self.model.predict(window[np.newaxis, ...])
            probabilities = result.probabilities[0]
            index = int(np.argmax(probabilities))
            timestamp = float(self._buffer_start_timestamp or 0.0)
            points.append(
                InferencePoint(
                    sequence=chunk.sequence,
                    device_timestamp=timestamp,
                    host_timestamp=chunk.host_timestamp,
                    labels=result.labels,
                    probabilities=tuple(float(value) for value in probabilities),
                    confidence=float(probabilities[index]),
                    predicted_label=result.labels[index],
                    latency_seconds=result.latency_seconds,
                )
            )
            self._samples = self._samples[self.hop_samples :]
            self._buffer_start_timestamp = timestamp + self.hop_samples / chunk.sampling_rate
        return points


class EdgeAINode:
    """Streaming node that attaches serializable inference results to a chunk."""

    def __init__(
        self,
        inference: SlidingWindowInference,
        detector: EventDetector | None = None,
    ) -> None:
        self.inference = inference
        self.detector = detector

    def configure(self, settings: Mapping[str, Any] | None = None) -> None:
        del settings

    def reset(self) -> None:
        self.inference.reset()
        if self.detector is not None:
            self.detector.reset()

    def process(self, chunk: StreamChunk) -> StreamChunk:
        points = self.inference.process(chunk)
        events = [] if self.detector is None else [self.detector.update(point) for point in points]
        return chunk.with_samples(
            chunk.samples,
            attributes={
                "ai_inference": tuple(points),
                "ai_events": tuple(event for event in events if event is not None),
            },
        )
