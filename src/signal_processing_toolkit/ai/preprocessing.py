"""Serializable preprocessing shared by model training and inference."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any, Literal

import numpy as np
from scipy import signal as scipy_signal


@dataclass(frozen=True, slots=True)
class PreprocessingPipeline:
    """A deterministic, serializable preprocessing specification.

    Raw arrays are sample-major: ``(samples,)`` or ``(samples, channels)``.
    Time-domain output is ``(samples, channels)``. Spectrogram output is
    ``(frequency, frame, channel)``. Stored normalization values must come from
    training data and are reused unchanged for inference.
    """

    mode: Literal["time", "spectrogram"] = "time"
    sampling_rate: float = 1.0
    window_samples: int = 1
    channel_indices: tuple[int, ...] | None = None
    remove_dc: bool = False
    mean: tuple[float, ...] | None = None
    scale: tuple[float, ...] | None = None
    stft_window: str = "hann"
    stft_length: int = 256
    stft_overlap: int = 128
    fft_length: int | None = None
    spectrum: Literal["magnitude", "power", "log_power"] = "log_power"
    log_floor: float = 1e-12

    def __post_init__(self) -> None:
        if self.mode not in {"time", "spectrogram"}:
            raise ValueError("mode must be 'time' or 'spectrogram'")
        if not np.isfinite(self.sampling_rate) or self.sampling_rate <= 0:
            raise ValueError("sampling_rate must be finite and positive")
        if self.window_samples <= 0:
            raise ValueError("window_samples must be positive")
        if self.channel_indices is not None and (
            not self.channel_indices or min(self.channel_indices) < 0
        ):
            raise ValueError("channel_indices must contain non-negative channel indexes")
        if self.stft_length <= 0 or not 0 <= self.stft_overlap < self.stft_length:
            raise ValueError("STFT overlap must satisfy 0 <= overlap < length")
        if self.fft_length is not None and self.fft_length < self.stft_length:
            raise ValueError("fft_length cannot be shorter than stft_length")
        if not np.isfinite(self.log_floor) or self.log_floor <= 0:
            raise ValueError("log_floor must be finite and positive")
        if (self.mean is None) != (self.scale is None):
            raise ValueError("mean and scale must either both be set or both be omitted")
        if self.mean is not None:
            scale = self.scale
            if scale is None or len(self.mean) != len(scale) or not self.mean:
                raise ValueError("mean and scale must have the same non-zero length")
            if not np.all(np.isfinite(self.mean)) or not np.all(np.isfinite(scale)):
                raise ValueError("normalization values must be finite")
            if np.any(np.asarray(scale) <= 0):
                raise ValueError("normalization scales must be positive")

    @classmethod
    def fit(
        cls,
        samples: np.ndarray,
        *,
        mode: Literal["time", "spectrogram"] = "time",
        sampling_rate: float,
        window_samples: int,
        **settings: Any,
    ) -> PreprocessingPipeline:
        """Fit per-output-channel normalization once on training samples."""
        unscaled = cls(
            mode=mode,
            sampling_rate=sampling_rate,
            window_samples=window_samples,
            **settings,
        )
        training = np.asarray(samples)
        if training.ndim == 3:
            features = np.stack([unscaled._extract(window) for window in training], axis=0)
        else:
            features = unscaled._extract(training)
        axes = tuple(range(features.ndim - 1))
        mean = np.mean(features, axis=axes)
        scale = np.std(features, axis=axes)
        scale = np.where(scale > np.finfo(float).eps, scale, 1.0)
        data = unscaled.to_dict()
        data["mean"] = np.atleast_1d(mean).astype(float).tolist()
        data["scale"] = np.atleast_1d(scale).astype(float).tolist()
        return cls.from_dict(data)

    def transform(self, samples: np.ndarray) -> np.ndarray:
        """Apply the exact persisted training transformation to one window."""
        features = self._extract(samples)
        if self.mean is not None and self.scale is not None:
            if features.shape[-1] != len(self.mean):
                raise ValueError(
                    f"Expected {len(self.mean)} normalized channel(s), got {features.shape[-1]}"
                )
            features = (features - np.asarray(self.mean)) / np.asarray(self.scale)
        return np.asarray(features, dtype=np.float32)

    def transform_batch(self, windows: np.ndarray) -> np.ndarray:
        data = np.asarray(windows)
        if data.ndim not in (2, 3):
            raise ValueError("A window batch must have shape (batch, samples[, channels])")
        return np.stack([self.transform(window) for window in data], axis=0)

    def _extract(self, samples: np.ndarray) -> np.ndarray:
        data = np.asarray(samples)
        if data.ndim == 1:
            data = data[:, np.newaxis]
        if data.ndim != 2:
            raise ValueError("Samples must have shape (samples,) or (samples, channels)")
        if data.shape[0] != self.window_samples:
            raise ValueError(f"Expected {self.window_samples} samples, got {data.shape[0]}")
        if not np.issubdtype(data.dtype, np.number) or not np.all(np.isfinite(data)):
            raise ValueError("Samples must be finite numeric values")
        if np.iscomplexobj(data):
            raise ValueError("Edge-AI preprocessing currently requires real-valued samples")
        if self.channel_indices is not None:
            if max(self.channel_indices) >= data.shape[1]:
                raise ValueError("channel_indices references a missing input channel")
            data = data[:, self.channel_indices]
        data = data.astype(np.float64, copy=False)
        if self.remove_dc:
            data = data - np.mean(data, axis=0, keepdims=True)
        if self.mode == "time":
            return data
        channels: list[np.ndarray] = []
        for channel in range(data.shape[1]):
            _, _, stft = scipy_signal.stft(
                data[:, channel],
                fs=self.sampling_rate,
                window=self.stft_window,
                nperseg=self.stft_length,
                noverlap=self.stft_overlap,
                nfft=self.fft_length,
                boundary=None,
                padded=False,
            )
            magnitude = np.abs(stft)
            if self.spectrum == "magnitude":
                values = magnitude
            else:
                values = magnitude**2
                if self.spectrum == "log_power":
                    values = 10.0 * np.log10(np.maximum(values, self.log_floor))
            channels.append(values)
        return np.stack(channels, axis=-1)

    def to_dict(self) -> dict[str, Any]:
        result = asdict(self)
        result["channel_indices"] = (
            None if self.channel_indices is None else list(self.channel_indices)
        )
        result["mean"] = None if self.mean is None else list(self.mean)
        result["scale"] = None if self.scale is None else list(self.scale)
        return result

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> PreprocessingPipeline:
        values = dict(data)
        for name in ("channel_indices", "mean", "scale"):
            if values.get(name) is not None:
                values[name] = tuple(values[name])
        return cls(**values)
