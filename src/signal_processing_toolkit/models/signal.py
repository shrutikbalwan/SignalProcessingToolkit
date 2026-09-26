from __future__ import annotations

import copy
import uuid
import warnings
from dataclasses import dataclass, field, replace
from datetime import UTC, datetime
from typing import Any, ClassVar, cast

import numpy as np

from signal_processing_toolkit.models.enums import WindowType


def _new_id() -> str:
    return uuid.uuid4().hex[:12]


@dataclass(frozen=True, slots=True)
class ProcessingStep:
    """One immutable processing event in a signal's provenance."""

    operation: str
    parameters: dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=lambda: datetime.now(UTC))


@dataclass(slots=True)
class SignalMetadata:
    """Descriptive and structured metadata carried with signal samples."""

    id: str = field(default_factory=_new_id)
    name: str = "Untitled Signal"
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    modified_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    description: str = ""
    tags: list[str] = field(default_factory=list)
    source: str = ""
    attributes: dict[str, Any] = field(default_factory=dict)
    provenance: tuple[ProcessingStep, ...] = ()
    parent_id: str | None = None

    def derived(self, operation: str, parameters: dict[str, Any] | None = None) -> SignalMetadata:
        step = ProcessingStep(operation, copy.deepcopy(parameters or {}))
        return SignalMetadata(
            name=self.name,
            created_at=self.created_at,
            modified_at=datetime.now(UTC),
            description=self.description,
            tags=self.tags.copy(),
            source=self.source,
            attributes=copy.deepcopy(self.attributes),
            provenance=(*self.provenance, step),
            parent_id=self.id,
        )

    def clone(self, *, preserve_id: bool = True) -> SignalMetadata:
        result = copy.deepcopy(self)
        if not preserve_id:
            result.id = _new_id()
            result.parent_id = self.id
            result.modified_at = datetime.now(UTC)
        return result


_UNSET = object()


@dataclass
class Signal:
    """A sampled signal using a sample-major array convention.

    Mono data has shape ``(n_samples,)``. Multichannel data has shape
    ``(n_samples, n_channels)``. Axis 0 is always time and axis 1 is always
    channel. Boolean, object, NaN, and infinite sample values are rejected.
    Integer input is converted to float64; floating and complex dtypes are
    retained.
    """

    SAMPLE_AXIS: ClassVar[int] = 0
    CHANNEL_AXIS: ClassVar[int] = 1

    time_data: np.ndarray
    sampling_rate: float
    frequency: float = 0.0
    amplitude: float = 1.0
    phase: float = 0.0
    metadata: SignalMetadata = field(default_factory=SignalMetadata)
    channel_names: tuple[str, ...] | None = None
    units: str | tuple[str, ...] = ""
    start_time: float = 0.0

    def __post_init__(self) -> None:
        if not np.isfinite(self.sampling_rate) or self.sampling_rate <= 0:
            raise ValueError(f"Sampling rate must be finite and positive, got {self.sampling_rate}")
        if not np.isfinite(self.start_time):
            raise ValueError(f"Start time must be finite, got {self.start_time}")

        data = np.asarray(self.time_data)
        if data.ndim not in (1, 2):
            raise ValueError(
                "Signal samples must have shape (samples,) or (samples, channels); "
                f"received {data.shape}"
            )
        if data.ndim == 2 and data.shape[1] == 0:
            raise ValueError("A multichannel signal must contain at least one channel")
        if np.issubdtype(data.dtype, np.bool_) or not (
            np.issubdtype(data.dtype, np.integer)
            or np.issubdtype(data.dtype, np.floating)
            or np.issubdtype(data.dtype, np.complexfloating)
        ):
            raise TypeError(
                f"Signal samples must have a real or complex numeric dtype, got {data.dtype}"
            )
        if np.issubdtype(data.dtype, np.integer):
            data = data.astype(np.float64)
        else:
            data = np.array(data, copy=True)
        if not np.all(np.isfinite(data)):
            raise ValueError(
                "Signal samples must contain only finite values; NaN and infinity are invalid"
            )
        self.time_data = data

        names = self.channel_names
        if names is None:
            names = (
                ("channel_1",)
                if self.n_channels == 1
                else tuple(f"channel_{index + 1}" for index in range(self.n_channels))
            )
        else:
            names = tuple(names)
        if len(names) != self.n_channels or any(not name for name in names):
            raise ValueError(f"Expected {self.n_channels} non-empty channel name(s), got {names!r}")
        if len(set(names)) != len(names):
            raise ValueError("Channel names must be unique")
        self.channel_names = names

        if isinstance(self.units, str):
            normalized_units = (self.units,) * self.n_channels
        else:
            normalized_units = tuple(self.units)
        if len(normalized_units) != self.n_channels:
            raise ValueError(f"Expected {self.n_channels} unit value(s), got {normalized_units!r}")
        self.units = normalized_units
        self.metadata = self.metadata.clone()

    @property
    def n_samples(self) -> int:
        return int(self.time_data.shape[self.SAMPLE_AXIS])

    @property
    def n_channels(self) -> int:
        return 1 if self.time_data.ndim == 1 else self.time_data.shape[self.CHANNEL_AXIS]

    @property
    def is_mono(self) -> bool:
        return self.n_channels == 1

    @property
    def is_complex(self) -> bool:
        return bool(np.iscomplexobj(self.time_data))

    @property
    def duration(self) -> float:
        return self.n_samples / self.sampling_rate

    @property
    def nyquist_frequency(self) -> float:
        return self.sampling_rate / 2.0

    @property
    def time_vector(self) -> np.ndarray:
        return self.start_time + np.arange(self.n_samples, dtype=np.float64) / self.sampling_rate

    @property
    def rms(self) -> float:
        if self.n_samples == 0:
            raise ValueError("RMS is undefined for an empty signal")
        return float(np.sqrt(np.mean(np.abs(self.time_data) ** 2)))

    @property
    def peak_to_peak(self) -> float:
        if self.n_samples == 0:
            raise ValueError("Peak-to-peak is undefined for an empty signal")
        values = np.abs(self.time_data) if self.is_complex else self.time_data
        return float(np.max(values) - np.min(values))

    @property
    def shape(self) -> tuple[int, ...]:
        return self.time_data.shape

    @property
    def length(self) -> int:
        warnings.warn(
            "Signal.length is deprecated because it was ambiguous for multichannel data; "
            "use Signal.n_samples",
            DeprecationWarning,
            stacklevel=2,
        )
        return self.n_samples

    def copy(self, *, preserve_id: bool = True) -> Signal:
        return replace(
            self,
            time_data=self.time_data.copy(),
            metadata=self.metadata.clone(preserve_id=preserve_id),
            channel_names=tuple(self.channel_names or ()),
            units=tuple(self.units),
        )

    def updated(
        self,
        *,
        time_data: np.ndarray | object = _UNSET,
        sampling_rate: float | object = _UNSET,
        frequency: float | object = _UNSET,
        amplitude: float | object = _UNSET,
        phase: float | object = _UNSET,
        channel_names: tuple[str, ...] | None | object = _UNSET,
        units: str | tuple[str, ...] | object = _UNSET,
        start_time: float | object = _UNSET,
        operation: str = "update",
        parameters: dict[str, Any] | None = None,
    ) -> Signal:
        return Signal(
            time_data=self.time_data if time_data is _UNSET else np.asarray(time_data),
            sampling_rate=(
                self.sampling_rate if sampling_rate is _UNSET else float(cast(float, sampling_rate))
            ),
            frequency=(self.frequency if frequency is _UNSET else float(cast(float, frequency))),
            amplitude=(self.amplitude if amplitude is _UNSET else float(cast(float, amplitude))),
            phase=self.phase if phase is _UNSET else float(cast(float, phase)),
            metadata=self.metadata.derived(operation, parameters),
            channel_names=(
                self.channel_names if channel_names is _UNSET else channel_names  # type: ignore[arg-type]
            ),
            units=self.units if units is _UNSET else units,  # type: ignore[arg-type]
            start_time=(
                self.start_time if start_time is _UNSET else float(cast(float, start_time))
            ),
        )

    def validate_compatibility(
        self,
        other: Signal,
        *,
        require_same_length: bool = False,
        require_same_start: bool = True,
        require_same_units: bool = True,
    ) -> None:
        if not np.isclose(self.sampling_rate, other.sampling_rate, rtol=0.0, atol=1e-12):
            raise ValueError(
                "Sampling rate mismatch; explicitly resample before combining signals: "
                f"{self.sampling_rate} Hz vs {other.sampling_rate} Hz"
            )
        if self.n_channels != other.n_channels:
            raise ValueError(f"Channel count mismatch: {self.n_channels} vs {other.n_channels}")
        if self.channel_names != other.channel_names:
            raise ValueError(
                f"Channel ordering mismatch: {self.channel_names!r} vs {other.channel_names!r}"
            )
        if require_same_units and self.units != other.units:
            raise ValueError(f"Physical unit mismatch: {self.units!r} vs {other.units!r}")
        if require_same_start and not np.isclose(self.start_time, other.start_time):
            raise ValueError(
                f"Start-time mismatch: {self.start_time} s vs {other.start_time} s; align first"
            )
        if require_same_length and self.n_samples != other.n_samples:
            raise ValueError(f"Signal length mismatch: {self.n_samples} vs {other.n_samples}")

    def resample(self, new_rate: float) -> Signal:
        from signal_processing_toolkit.dsp.sampling.sampler import resample_signal

        return resample_signal(self, new_rate)

    def apply_window(self, window_type: WindowType, **kwargs: float) -> Signal:
        from signal_processing_toolkit.dsp.windows.base import create_window

        window = create_window(window_type, self.n_samples, **kwargs)
        if self.time_data.ndim == 2:
            window = window[:, np.newaxis]
        return self.updated(
            time_data=self.time_data * window,
            operation="apply_window",
            parameters={"window": window_type.value, **kwargs},
        )
