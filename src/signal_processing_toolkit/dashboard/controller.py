"""Translate dashboard actions into service calls and state updates."""

from __future__ import annotations

from datetime import datetime
from typing import cast

from PyQt6.QtCore import QObject, QTimer, pyqtSignal

from signal_processing_toolkit.dashboard.events import DashboardAction, DashboardCommand
from signal_processing_toolkit.dashboard.services import (
    AcquisitionService,
    DemoSource,
    MetricsService,
    MonitoringService,
    SessionService,
)
from signal_processing_toolkit.dashboard.state import (
    AIState,
    ConnectionStatus,
    DashboardEvent,
    EventSeverity,
    SourceState,
    SourceType,
)
from signal_processing_toolkit.dashboard.viewmodel import DashboardViewModel
from signal_processing_toolkit.streaming.model import StreamChunk


class DashboardController(QObject):
    state_changed = pyqtSignal()
    error = pyqtSignal(str)
    devices_changed = pyqtSignal(list)

    def __init__(
        self, viewmodel: DashboardViewModel | None = None, parent: QObject | None = None
    ) -> None:
        super().__init__(parent)
        self.viewmodel = viewmodel or DashboardViewModel()
        self.demo_source = DemoSource()
        self._acquisition: AcquisitionService | None = None
        self._source_settings: dict[str, object] = {}
        self.metrics = MetricsService()
        self.monitoring = MonitoringService()
        self.sessions = SessionService()
        self._timer = QTimer(self)
        self._timer.setInterval(100)
        self._timer.timeout.connect(self._tick)
        self.demo_source.subscribe(self._on_chunk)
        self._closed = False

    def dispatch(self, action: DashboardAction | DashboardCommand) -> None:
        command = action.command if isinstance(action, DashboardAction) else action
        handlers = {
            DashboardCommand.START: self.start,
            DashboardCommand.DEMO_MODE: self.start_demo,
            DashboardCommand.PAUSE: self.pause,
            DashboardCommand.RESUME: self.resume,
            DashboardCommand.STOP: self.stop,
            DashboardCommand.TOGGLE_RECORDING: self.toggle_recording,
        }
        handlers[command]()

    def start_demo(self) -> None:
        self.stop_source()
        self.viewmodel.update_source(
            SourceState(
                source_type=SourceType.DEMO,
                device_name="Deterministic demo source",
                connected=True,
                connection_status=ConnectionStatus.CONNECTED,
                sampling_rate=self.demo_source.sampling_rate,
                channels=1,
                frame_rate=10.0,
            )
        )
        self.start()

    def select_source(self, source_name: str) -> None:
        """Construct and start an optional source selected by the dashboard."""
        if source_name == "demo":
            self.start_demo()
            return
        try:
            if source_name == "serial":
                from signal_processing_toolkit.hardware.serial_source import (
                    SerialSensorSource,
                    SerialSourceConfig,
                    enumerate_serial_ports,
                )

                ports = enumerate_serial_ports()
                configured_port = str(self._source_settings.get("port", "")) or str(
                    self._source_settings.get("device", "")
                )
                if configured_port:
                    port = next((item for item in ports if item.device == configured_port), None)
                    if port is None:
                        raise RuntimeError(f"Serial port not found: {configured_port}")
                elif not ports:
                    raise RuntimeError("No serial sensor ports were found")
                else:
                    port = ports[0]
                source: object = SerialSensorSource(
                    SerialSourceConfig(
                        port=port.device,
                        sampling_rate=float(
                            cast(float, self._source_settings.get("sampling_rate", 1000.0))
                        ),
                    )
                )
                self.attach_source(source, SourceType.SERIAL, port.description or port.device)
            elif source_name == "audio":
                from signal_processing_toolkit.audio.streaming import (
                    SoundDeviceAudioSource,
                    enumerate_audio_devices,
                )

                devices = tuple(
                    device for device in enumerate_audio_devices() if device.supports_input
                )
                if not devices:
                    raise RuntimeError("No audio input devices were found")
                selected = str(self._source_settings.get("device", ""))
                device = next(
                    (
                        item
                        for item in devices
                        if str(item.index) == selected or item.name == selected
                    ),
                    devices[0],
                )
                source = SoundDeviceAudioSource()
                source.configure(
                    {
                        "device": device.index,
                        "sampling_rate": float(
                            cast(
                                float,
                                self._source_settings.get(
                                    "sampling_rate", device.default_sampling_rate
                                ),
                            )
                        ),
                        "channels": min(
                            device.maximum_input_channels,
                            cast(int, self._source_settings.get("channels", 1)),
                        ),
                    }
                )
                self.attach_source(source, SourceType.AUDIO, device.name)
            else:
                raise RuntimeError("Replay selection requires a recorded session")
            self.start_source()
        except (ImportError, RuntimeError, OSError, ValueError) as exc:
            self._on_source_error(str(exc))

    def load_replay(self, path: str) -> None:
        """Load a RecordedSession and replay it through the normal source path."""
        try:
            from signal_processing_toolkit.streaming.sinks import RecordedSession

            session = RecordedSession.load(path)
            self.attach_source(
                session.replay_source(paced=False), SourceType.REPLAY, f"Replay: {path}"
            )
            self.start_source()
        except (OSError, ValueError, KeyError, RuntimeError) as exc:
            self._on_source_error(str(exc))

    def refresh_sources(self) -> None:
        """Refresh hook for source pickers; discovery remains lazy and optional."""
        devices: list[tuple[str, str]] = []
        try:
            from signal_processing_toolkit.hardware.serial_source import enumerate_serial_ports

            devices.extend(
                (f"Serial: {item.description or item.device}", item.device)
                for item in enumerate_serial_ports()
            )
        except (ImportError, RuntimeError, OSError):
            pass
        try:
            from signal_processing_toolkit.audio.streaming import enumerate_audio_devices

            devices.extend(
                (f"Audio: {item.name}", str(item.index))
                for item in enumerate_audio_devices()
                if item.supports_input
            )
        except (ImportError, RuntimeError, OSError):
            pass
        self.devices_changed.emit(devices)
        self.viewmodel.add_event(
            DashboardEvent(event_type="source", description="Source list refreshed")
        )

    def configure_source(self, sampling_rate: float, channels: int, port: str, device: str) -> None:
        self._source_settings = {
            "sampling_rate": sampling_rate,
            "channels": channels,
            "port": port,
            "device": device,
        }

    def attach_source(self, source: object, source_type: SourceType, device_name: str) -> None:
        """Attach an audio, serial or replay StreamSource without importing its backend."""
        self.stop_source()
        self._acquisition = AcquisitionService(source)
        self._acquisition.subscribe_events(self._on_source_error)
        self.viewmodel.update_source(
            SourceState(
                source_type=source_type,
                device_name=device_name,
                connection_status=ConnectionStatus.CONNECTING,
            )
        )

    def start_source(self) -> None:
        if self._acquisition is None:
            raise RuntimeError("No external source is attached")
        self._acquisition.start()
        source = self.viewmodel.state.source
        source.connected = True
        source.connection_status = ConnectionStatus.CONNECTED
        self.viewmodel.update_source(source)
        self.start()

    def stop_source(self) -> None:
        if self._acquisition is not None:
            self._acquisition.stop()
            self._acquisition = None

    def _on_source_error(self, message: str) -> None:
        self.error.emit(message)
        source = self.viewmodel.state.source
        source.connected = False
        source.connection_status = ConnectionStatus.ERROR
        self.viewmodel.update_source(source)

    def start(self) -> None:
        if self.viewmodel.state.session.status.value == "running":
            return
        session = self.sessions.start(self.viewmodel.state.session)
        self.viewmodel.update_session(session)
        if self._acquisition is None:
            self.demo_source.start()
        self._timer.start()
        self.viewmodel.add_event(
            DashboardEvent(event_type="session", description="Session started")
        )
        self.state_changed.emit()

    def pause(self) -> None:
        self.viewmodel.update_session(self.sessions.pause(self.viewmodel.state.session))
        self._timer.stop()
        if self._acquisition is not None:
            self._acquisition.stop()
        self.viewmodel.add_event(DashboardEvent(event_type="session", description="Session paused"))
        self.state_changed.emit()

    def resume(self) -> None:
        self.viewmodel.update_session(self.sessions.resume(self.viewmodel.state.session))
        if self.viewmodel.state.session.status.value == "running":
            if self._acquisition is None:
                self.demo_source.start()
            elif not self._acquisition.running:
                self._acquisition.start()
            self._timer.start()
        self.state_changed.emit()

    def stop(self) -> None:
        self._timer.stop()
        self.demo_source.stop()
        if self._acquisition is not None:
            self._acquisition.stop()
        self.viewmodel.update_session(self.sessions.stop(self.viewmodel.state.session))
        source = self.viewmodel.state.source
        source.connected = False
        source.connection_status = ConnectionStatus.DISCONNECTED
        self.viewmodel.update_source(source)
        self.viewmodel.add_event(
            DashboardEvent(event_type="session", description="Session stopped")
        )
        self.state_changed.emit()

    def toggle_recording(self) -> None:
        recording = self.sessions.toggle_recording(self.viewmodel.state.recording)
        self.viewmodel.update_recording(recording)

    def set_ai_prediction(self, class_name: str, confidence: float) -> None:
        self.viewmodel.update_ai(
            AIState(
                model_loaded=True,
                model_name=self.viewmodel.state.ai.model_name
                if self.viewmodel.state.ai.model_loaded
                else "Dashboard model",
                predicted_class=class_name,
                confidence=confidence,
            )
        )
        self.viewmodel.add_event(
            DashboardEvent(
                severity=EventSeverity.WARNING if confidence < 0.8 else EventSeverity.INFO,
                event_type="ai_prediction",
                description=class_name,
                confidence=confidence,
            )
        )

    def _tick(self) -> None:
        if self._closed:
            return
        if self._acquisition is not None:
            for chunk in self._acquisition.poll():
                self._on_stream_chunk(chunk)
            if self._acquisition.error is not None:
                self._on_source_error(str(self._acquisition.error))
        else:
            self.demo_source.next_chunk()
        session = self.viewmodel.state.session
        if session.started_at:
            session.elapsed_seconds = (datetime.now() - session.started_at).total_seconds()
            self.viewmodel.update_session(session)

    def _on_chunk(
        self, chunk: list[float], sequence: int, sampling_rate: float | None = None
    ) -> None:
        del sequence
        rate = self.demo_source.sampling_rate if sampling_rate is None else sampling_rate
        samples = (self.viewmodel.state.signal_samples + chunk)[-2_000:]
        self.viewmodel.update("signal_samples", samples)
        self.viewmodel.update("spectrum", self.metrics.spectrum(samples))
        self.viewmodel.update_metrics(self.metrics.calculate(samples, rate))
        self.viewmodel.update_health(
            self.monitoring.update(processing_latency_ms=0.1, queue_depth=0)
        )
        if self.viewmodel.state.recording.active:
            recording = self.viewmodel.state.recording
            recording.samples_written += len(chunk)
            recording.duration_seconds = recording.samples_written / rate
            self.viewmodel.update_recording(recording)

    def _on_stream_chunk(self, chunk: StreamChunk) -> None:
        import numpy as np

        source = self.viewmodel.state.source
        source.connected = True
        source.connection_status = ConnectionStatus.CONNECTED
        source.sampling_rate = float(chunk.sampling_rate)
        source.channels = int(chunk.channel_count)
        source.frame_rate = source.sampling_rate / max(1, int(chunk.sample_count))
        self.viewmodel.update_source(source)
        samples = np.asarray(chunk.samples)
        mono = samples if samples.ndim == 1 else samples[:, 0]
        rate = float(chunk.sampling_rate)
        self._on_chunk(mono.astype(float).tolist(), int(chunk.sequence), rate)
        if self._acquisition is not None:
            health = self.viewmodel.state.health
            health.queue_depth = self._acquisition.queue_depth
            health.dropped_frames = self._acquisition.dropped_chunks
            missing = int(chunk.attributes.get("missing_before", 0))
            health.packet_loss += missing
            self.viewmodel.update_health(health)

    def cleanup(self) -> None:
        if self._closed:
            return
        self._closed = True
        self._timer.stop()
        self.stop_source()
        self.demo_source.stop()
        self.demo_source.unsubscribe(self._on_chunk)
        self.viewmodel.dispose()

    @property
    def timer_active(self) -> bool:
        return self._timer.isActive()
