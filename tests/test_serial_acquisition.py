from __future__ import annotations

import threading
import time

import numpy as np
import pytest

from signal_processing_toolkit.hardware import (
    BinaryPacketParser,
    CSVPacketParser,
    SensorPacket,
    SerialSensorSource,
    SerialSourceConfig,
    encode_binary_packet,
    encode_csv_packet,
    enumerate_serial_ports,
)
from signal_processing_toolkit.hardware.simulated import (
    SimulatedSerialBackend,
    SimulatedSerialConnection,
)
from signal_processing_toolkit.streaming import (
    GainNode,
    RecordedSession,
    RecorderSink,
    StreamPipeline,
)


def packet(sequence: int, values: np.ndarray | None = None) -> SensorPacket:
    samples = np.asarray(
        values if values is not None else [[sequence, -sequence]], dtype=np.float32
    )
    return SensorPacket(sequence, sequence / 1000.0, samples)


def test_binary_parser_handles_partial_and_fragmented_packets() -> None:
    encoded = encode_binary_packet(packet(4, np.arange(12, dtype=np.float32).reshape(4, 3)))
    parser = BinaryPacketParser()
    decoded = []
    for fragment in (encoded[:2], encoded[2:11], encoded[11:29], encoded[29:]):
        decoded.extend(parser.feed(fragment))
    assert len(decoded) == 1
    assert decoded[0].sequence == 4
    np.testing.assert_array_equal(decoded[0].samples, np.arange(12).reshape(4, 3))


def test_binary_parser_rejects_corruption_and_resynchronizes() -> None:
    corrupted = bytearray(encode_binary_packet(packet(1)))
    corrupted[-5] ^= 0x40
    parser = BinaryPacketParser()
    decoded = parser.feed(b"noise" + bytes(corrupted) + encode_binary_packet(packet(2)))
    assert [item.sequence for item in decoded] == [2]
    assert parser.corrupted_packets == 1
    assert parser.discarded_bytes >= 5


def test_csv_parser_handles_fragmentation_and_bad_rows() -> None:
    parser = CSVPacketParser(2)
    encoded = encode_csv_packet(packet(3))
    assert parser.feed(encoded[:5]) == ()
    decoded = parser.feed(encoded[5:] + b"bad,row\n")
    assert decoded[0].sequence == 3
    np.testing.assert_array_equal(decoded[0].samples, [[3, -3]])
    assert parser.corrupted_packets == 1


def test_serial_discovery_disconnect_reconnect_loss_and_order_reporting() -> None:
    first = SimulatedSerialConnection(
        [encode_binary_packet(packet(0)), ConnectionError("cable removed")]
    )
    second = SimulatedSerialConnection(
        [encode_binary_packet(packet(2)), encode_binary_packet(packet(1))]
    )
    backend = SimulatedSerialBackend([first, second])
    assert enumerate_serial_ports(backend)[0].device == "SIM0"
    source = SerialSensorSource(
        SerialSourceConfig(
            "SIM0",
            sampling_rate=1000,
            channel_names=("x", "y"),
            units=("m/s^2", "m/s^2"),
            reconnect_initial_delay=0,
        ),
        backend=backend,
    )
    cancel = threading.Event()
    chunks = [source.read(cancel), source.read(cancel), source.read(cancel)]
    assert [item.sequence for item in chunks if item is not None] == [0, 2, 1]
    assert chunks[1] is not None and chunks[1].attributes["missing_before"] == 1
    assert chunks[2] is not None and chunks[2].attributes["out_of_order"] is True
    assert chunks[0] is not None and chunks[0].samples.shape == (1, 2)
    assert source.metrics.missing_packets == 1
    assert source.metrics.out_of_order_packets == 1
    assert source.metrics.disconnects == 1
    assert source.metrics.reconnects == 1
    kinds = [event.kind for event in source.drain_events()]
    assert kinds == ["connected", "disconnected", "reconnected"]


def test_serial_reconnect_attempts_are_bounded() -> None:
    backend = SimulatedSerialBackend(
        [ConnectionError("one"), ConnectionError("two"), ConnectionError("unused")]
    )
    source = SerialSensorSource(
        SerialSourceConfig("SIM0", reconnect_attempts=1, reconnect_initial_delay=0),
        backend=backend,
    )
    with pytest.raises(ConnectionError, match="after 2 attempt"):
        source.read(threading.Event())
    assert backend.open_count == 2


def test_session_records_serial_events_configuration_and_replays_pipeline(tmp_path) -> None:
    connection = SimulatedSerialConnection(
        [encode_binary_packet(packet(0)), ConnectionError("done")]
    )
    backend = SimulatedSerialBackend([connection, SimulatedSerialConnection([])])
    source = SerialSensorSource(
        SerialSourceConfig(
            "SIM0",
            channel_names=("accelerometer_x", "accelerometer_y"),
            reconnect_initial_delay=0,
        ),
        backend=backend,
    )
    recorder = RecorderSink(stream_name="raw_sensor")
    pipeline = StreamPipeline()
    pipeline.configure(source, sinks=[recorder])
    pipeline.start()
    deadline = time.monotonic() + 2
    while len(recorder.session.chunks) < 1 and time.monotonic() < deadline:
        time.sleep(0.005)
    pipeline.stop()
    pipeline.close()
    session = recorder.session
    assert session.pipeline_configuration["source"] == "SerialSensorSource"
    assert {event.kind for event in session.connection_events} >= {
        "connected",
        "disconnected",
        "reconnected",
        "closed",
    }
    path = tmp_path / "sensor-session.npz"
    session.save(path)
    restored = RecordedSession.load(path)
    assert restored.stream_name == "raw_sensor"
    assert restored.pipeline_configuration == session.pipeline_configuration
    assert [event.kind for event in restored.connection_events] == [
        event.kind for event in session.connection_events
    ]
    assert restored.chunks[0].device_timestamp == session.chunks[0].device_timestamp
    assert restored.chunks[0].host_timestamp == session.chunks[0].host_timestamp

    replayed = RecorderSink()
    replay = StreamPipeline()
    replay.configure(restored.replay_source(), [GainNode(3)], [replayed])
    replay.start()
    assert replay.wait_until_stopped()
    replay.close()
    np.testing.assert_array_equal(
        replayed.session.chunks[0].samples,
        session.chunks[0].samples * 3,
    )
