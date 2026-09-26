import threading
from pathlib import Path

import numpy as np
from PyQt6.QtWidgets import QApplication

from signal_processing_toolkit.audio.streaming import AudioStreamConfig, SoundDeviceAudioSource
from signal_processing_toolkit.dashboard.controller import DashboardController
from signal_processing_toolkit.dashboard.state import SourceType
from signal_processing_toolkit.hardware import (
    SensorPacket,
    SerialSensorSource,
    SerialSourceConfig,
    encode_binary_packet,
)
from signal_processing_toolkit.hardware.simulated import (
    SimulatedSerialBackend,
    SimulatedSerialConnection,
)
from signal_processing_toolkit.streaming.sinks import RecordedSession
from signal_processing_toolkit.streaming.sources import SyntheticSource


class _FakeStream:
    def __init__(self, callback) -> None:
        self.callback = callback

    def start(self) -> None:
        values = np.ones((8, 2), dtype=np.float32)
        self.callback(values, 8, {"inputBufferAdcTime": 1.0}, None)

    def stop(self) -> None:
        return

    def close(self) -> None:
        return


class _FakeAudioBackend:
    def create_input_stream(self, **kwargs):
        return _FakeStream(kwargs["callback"])


def test_replay_session_uses_dashboard_source_path(qapp: QApplication) -> None:
    source = SyntheticSource(real_time=False, chunk_size=8)
    cancel = threading.Event()
    chunks = [source.read(cancel), source.read(cancel)]
    session = RecordedSession(tuple(chunk for chunk in chunks if chunk is not None))
    path = Path(".tmp") / "dashboard-session.npz"
    path.parent.mkdir(exist_ok=True)
    session.save(path)
    controller = DashboardController()
    controller.load_replay(str(path))
    for _ in range(10):
        controller._tick()
        if controller.viewmodel.state.signal_samples:
            break
    assert controller.viewmodel.state.source.source_type is SourceType.REPLAY
    assert controller.viewmodel.state.signal_samples
    controller.cleanup()
    path.unlink(missing_ok=True)


def test_fake_audio_source_reaches_dashboard(qapp: QApplication) -> None:
    source = SoundDeviceAudioSource(
        AudioStreamConfig(channels=2, block_size=8), backend=_FakeAudioBackend()
    )
    controller = DashboardController()
    controller.attach_source(source, SourceType.AUDIO, "fake microphone")
    controller.start_source()
    controller._tick()
    assert controller.viewmodel.state.source.channels == 2
    assert controller.viewmodel.state.signal_samples
    controller.cleanup()


def test_simulated_serial_source_reaches_dashboard(qapp: QApplication) -> None:
    packet = encode_binary_packet(SensorPacket(0, 0.0, np.ones((4, 2), dtype=np.float32)))
    source = SerialSensorSource(
        SerialSourceConfig("SIM0", sampling_rate=1000, channel_names=("x", "y")),
        backend=SimulatedSerialBackend([SimulatedSerialConnection([packet])]),
    )
    controller = DashboardController()
    controller.attach_source(source, SourceType.SERIAL, "simulated sensor")
    controller.start_source()
    for _ in range(10):
        controller._tick()
        if controller.viewmodel.state.signal_samples:
            break
    assert controller.viewmodel.state.source.source_type is SourceType.SERIAL
    assert controller.viewmodel.state.signal_samples
    controller.cleanup()
