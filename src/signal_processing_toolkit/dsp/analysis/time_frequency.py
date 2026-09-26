from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal

import numpy as np
from scipy import signal as sp_signal

from signal_processing_toolkit.models.signal import Signal

STFTScaling = Literal["spectrum", "psd"]
BoundaryMode = Literal["zeros", "even", "odd", "constant"] | None


@dataclass(frozen=True, slots=True)
class STFTConfig:
    """Configuration for framed Fourier analysis.

    ``overlap`` is a sample count and must be smaller than ``window_length``.
    Spectra use shape ``(frequency, frame)`` for mono and
    ``(frequency, frame, channel)`` for multichannel signals.
    """

    window: str | tuple[str, float] | np.ndarray = "hann"
    window_length: int = 256
    overlap: int = 128
    fft_length: int | None = None
    scaling: STFTScaling = "spectrum"
    boundary: BoundaryMode = "zeros"
    padded: bool = True
    detrend: bool | Literal["constant", "linear"] = False

    def __post_init__(self) -> None:
        if self.window_length < 1:
            raise ValueError("window_length must be positive")
        if not 0 <= self.overlap < self.window_length:
            raise ValueError("overlap must be in [0, window_length)")
        if self.fft_length is not None and self.fft_length < self.window_length:
            raise ValueError("fft_length cannot be smaller than window_length")

    @property
    def hop_length(self) -> int:
        return self.window_length - self.overlap

    @property
    def effective_fft_length(self) -> int:
        return self.window_length if self.fft_length is None else self.fft_length

    def parameters(self) -> dict[str, object]:
        return {
            "window": self.window,
            "window_length": self.window_length,
            "overlap": self.overlap,
            "hop_length": self.hop_length,
            "fft_length": self.effective_fft_length,
            "scaling": self.scaling,
            "boundary": self.boundary,
            "padded": self.padded,
            "detrend": self.detrend,
        }


@dataclass(slots=True)
class STFTResult:
    frequencies: np.ndarray
    times: np.ndarray
    spectrum: np.ndarray
    sampling_rate: float
    config: STFTConfig
    input_samples: int
    start_time: float = 0.0
    channel_names: tuple[str, ...] = ("channel_1",)
    units: tuple[str, ...] = ("",)
    parameters: dict[str, object] = field(default_factory=dict)

    @property
    def magnitude(self) -> np.ndarray:
        return np.abs(self.spectrum)

    @property
    def power(self) -> np.ndarray:
        return np.abs(self.spectrum) ** 2

    @property
    def magnitude_db(self) -> np.ndarray:
        with np.errstate(divide="ignore"):
            result: np.ndarray = np.maximum(20 * np.log10(self.magnitude), -300.0)
            return result


def stft(signal: Signal, config: STFTConfig | None = None) -> STFTResult:
    """Compute a configurable STFT without flattening channels."""
    config = config or STFTConfig()
    if signal.n_samples == 0:
        raise ValueError("STFT is undefined for an empty signal")
    if config.window_length > signal.n_samples and not config.padded:
        raise ValueError("window_length exceeds signal length while padding is disabled")
    frequencies, times, spectrum = sp_signal.stft(
        signal.time_data,
        fs=signal.sampling_rate,
        window=config.window,
        nperseg=config.window_length,
        noverlap=config.overlap,
        nfft=config.effective_fft_length,
        detrend=config.detrend,
        return_onesided=not signal.is_complex,
        boundary=config.boundary,
        padded=config.padded,
        axis=Signal.SAMPLE_AXIS,
        scaling=config.scaling,
    )
    if signal.time_data.ndim == 2:
        spectrum = np.moveaxis(spectrum, -1, 1)
    return STFTResult(
        frequencies=np.asarray(frequencies),
        times=signal.start_time + np.asarray(times),
        spectrum=np.asarray(spectrum),
        sampling_rate=signal.sampling_rate,
        config=config,
        input_samples=signal.n_samples,
        start_time=signal.start_time,
        channel_names=signal.channel_names or ("channel_1",),
        units=tuple(signal.units),
        parameters=config.parameters(),
    )


def istft(result: STFTResult, *, length: int | None = None) -> Signal:
    """Invert an STFT using the exact analysis parameters."""
    spectrum = result.spectrum
    _, samples = sp_signal.istft(
        spectrum,
        fs=result.sampling_rate,
        window=result.config.window,
        nperseg=result.config.window_length,
        noverlap=result.config.overlap,
        nfft=result.config.effective_fft_length,
        input_onesided=(result.spectrum.shape[0] == result.config.effective_fft_length // 2 + 1),
        boundary=result.config.boundary is not None,
        time_axis=1,
        freq_axis=0,
        scaling=result.config.scaling,
    )
    target = result.input_samples if length is None else int(length)
    if target < 0:
        raise ValueError("length cannot be negative")
    samples = np.asarray(samples)[:target]
    if np.iscomplexobj(samples) and np.all(np.abs(samples.imag) < 1e-12):
        samples = samples.real
    return Signal(
        time_data=samples,
        sampling_rate=result.sampling_rate,
        channel_names=result.channel_names,
        units=result.units,
        start_time=result.start_time,
    )


class StreamingSpectrogram:
    """Incremental STFT with overlap state and no duplicated frames."""

    def __init__(self, sampling_rate: float, config: STFTConfig, n_channels: int = 1) -> None:
        if sampling_rate <= 0 or not np.isfinite(sampling_rate):
            raise ValueError("sampling_rate must be finite and positive")
        if n_channels < 1:
            raise ValueError("n_channels must be positive")
        self.sampling_rate = float(sampling_rate)
        self.config = STFTConfig(
            window=config.window,
            window_length=config.window_length,
            overlap=config.overlap,
            fft_length=config.fft_length,
            scaling=config.scaling,
            boundary=None,
            padded=False,
            detrend=config.detrend,
        )
        self.n_channels = n_channels
        shape = (0,) if n_channels == 1 else (0, n_channels)
        self._buffer = np.empty(shape)
        self._buffer_start_sample = 0
        self._received_samples = 0
        self._start_time: float | None = None
        self._channel_names = tuple(f"channel_{index + 1}" for index in range(n_channels))
        self._units = ("",) * n_channels

    def reset(self) -> None:
        shape = (0,) if self.n_channels == 1 else (0, self.n_channels)
        self._buffer = np.empty(shape)
        self._buffer_start_sample = 0
        self._received_samples = 0
        self._start_time = None

    def push(self, chunk: Signal) -> STFTResult | None:
        if chunk.n_channels != self.n_channels:
            raise ValueError(f"Expected {self.n_channels} channels, got {chunk.n_channels}")
        if not np.isclose(chunk.sampling_rate, self.sampling_rate, rtol=0, atol=1e-12):
            raise ValueError("Streaming chunk sampling rate mismatch")
        if chunk.n_samples == 0:
            return None
        if self._start_time is None:
            self._start_time = chunk.start_time
            self._channel_names = chunk.channel_names or self._channel_names
            self._units = tuple(chunk.units)
        self._buffer = np.concatenate((self._buffer, chunk.time_data), axis=Signal.SAMPLE_AXIS)
        self._received_samples += chunk.n_samples
        if len(self._buffer) < self.config.window_length:
            return None
        frame_count = 1 + (len(self._buffer) - self.config.window_length) // self.config.hop_length
        used = self.config.window_length + (frame_count - 1) * self.config.hop_length
        segment = Signal(
            self._buffer[:used],
            self.sampling_rate,
            channel_names=self._channel_names,
            units=self._units,
            start_time=(self._start_time or 0.0) + self._buffer_start_sample / self.sampling_rate,
        )
        result = stft(segment, self.config)
        consumed = frame_count * self.config.hop_length
        self._buffer = self._buffer[consumed:]
        self._buffer_start_sample += consumed
        return result
