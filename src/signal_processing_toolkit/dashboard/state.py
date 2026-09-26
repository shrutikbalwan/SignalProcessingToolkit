"""Typed state models used by the dashboard."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import StrEnum


class SessionStatus(StrEnum):
    IDLE = "idle"
    RUNNING = "running"
    PAUSED = "paused"
    STOPPED = "stopped"
    ERROR = "error"


class SourceType(StrEnum):
    NONE = "none"
    DEMO = "demo"
    AUDIO = "audio"
    SERIAL = "serial"
    REPLAY = "replay"


class ConnectionStatus(StrEnum):
    DISCONNECTED = "disconnected"
    CONNECTING = "connecting"
    CONNECTED = "connected"
    ERROR = "error"


class EventSeverity(StrEnum):
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class AIStatus(StrEnum):
    UNAVAILABLE = "unavailable"
    READY = "ready"
    RUNNING = "running"
    DETECTION = "detection"
    ERROR = "error"


@dataclass(slots=True)
class SessionState:
    status: SessionStatus = SessionStatus.IDLE
    started_at: datetime | None = None
    elapsed_seconds: float = 0.0
    project_name: str = "Untitled session"


@dataclass(slots=True)
class SourceState:
    source_type: SourceType = SourceType.NONE
    device_name: str = "No source"
    connected: bool = False
    connection_status: ConnectionStatus = ConnectionStatus.DISCONNECTED
    sampling_rate: float = 0.0
    channels: int = 0
    frame_rate: float = 0.0


@dataclass(slots=True)
class SignalMetrics:
    rms: float | None = None
    peak: float | None = None
    peak_to_peak: float | None = None
    crest_factor: float | None = None
    dominant_frequency: float | None = None
    band_power: float | None = None
    snr: float | None = None
    thd: float | None = None


@dataclass(slots=True)
class ProcessingHealth:
    processing_latency_ms: float = 0.0
    inference_latency_ms: float = 0.0
    queue_depth: int = 0
    dropped_frames: int = 0
    packet_loss: float = 0.0
    cpu_percent: float = 0.0
    memory_mb: float = 0.0


@dataclass(slots=True)
class AIState:
    model_loaded: bool = False
    model_name: str = "No model loaded"
    predicted_class: str = "—"
    confidence: float | None = None
    status: AIStatus = AIStatus.UNAVAILABLE


@dataclass(slots=True)
class RecordingState:
    active: bool = False
    output_path: str = ""
    samples_written: int = 0
    duration_seconds: float = 0.0


@dataclass(slots=True)
class DashboardEvent:
    timestamp: datetime = field(default_factory=datetime.now)
    severity: EventSeverity = EventSeverity.INFO
    event_type: str = "system"
    description: str = ""
    confidence: float | None = None


@dataclass(slots=True)
class DashboardState:
    session: SessionState = field(default_factory=SessionState)
    source: SourceState = field(default_factory=SourceState)
    metrics: SignalMetrics = field(default_factory=SignalMetrics)
    health: ProcessingHealth = field(default_factory=ProcessingHealth)
    ai: AIState = field(default_factory=AIState)
    recording: RecordingState = field(default_factory=RecordingState)
    events: list[DashboardEvent] = field(default_factory=list)
    signal_samples: list[float] = field(default_factory=list)
    spectrum: list[float] = field(default_factory=list)

    def copy(self) -> DashboardState:
        """Return a detached snapshot suitable for observers and tests."""
        import copy

        return copy.deepcopy(self)
