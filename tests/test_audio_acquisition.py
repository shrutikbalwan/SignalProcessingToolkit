from __future__ import annotations

import time
from dataclasses import dataclass

import numpy as np

from signal_processing_toolkit.audio import (
    AudioStreamConfig,
    SoundDeviceAudioSource,
    enumerate_audio_devices,
)
from signal_processing_toolkit.streaming import (
    GainNode,
    RecorderNode,
    RecorderSink,
    StreamPipeline,
)


@dataclass
class FakeStatus:
    input_overflow: bool = False
    output_underflow: bool = False


class FakeInputStream:
    def __init__(self, callback, blocks) -> None:
        self.callback = callback
        self.blocks = blocks
        self.started = False
        self.closed = False

    def start(self) -> None:
        self.started = True
        for index, (values, status) in enumerate(self.blocks):
            self.callback(
                values,
                values.shape[0],
                {"inputBufferAdcTime": 10.0 + index * 0.01},
                status,
            )

    def stop(self) -> None:
        self.started = False

    def close(self) -> None:
        self.closed = True


class FakeAudioBackend:
    def __init__(self, blocks=()) -> None:
        self.blocks = blocks
        self.arguments = None
        self.stream = None

    def query_devices(self):
        return (
            {
                "name": "Microphone",
                "max_input_channels": 2,
                "max_output_channels": 0,
                "default_samplerate": 48_000,
            },
            {
                "name": "Speakers",
                "max_input_channels": 0,
                "max_output_channels": 2,
                "default_samplerate": 48_000,
            },
        )

    def create_input_stream(self, **kwargs):
        self.arguments = kwargs
        self.stream = FakeInputStream(kwargs["callback"], self.blocks)
        return self.stream


def _wait_for(predicate, timeout: float = 2.0) -> None:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if predicate():
            return
        time.sleep(0.005)
    raise AssertionError("condition was not reached before timeout")


def test_audio_device_enumeration_includes_input_and_output_capabilities() -> None:
    devices = enumerate_audio_devices(FakeAudioBackend())
    assert devices[0].supports_input and not devices[0].supports_output
    assert devices[1].supports_output and not devices[1].supports_input
    assert devices[0].default_sampling_rate == 48_000


def test_audio_callback_preserves_channels_configuration_and_status() -> None:
    blocks = (
        (np.ones((4, 2), dtype=np.float32), FakeStatus(input_overflow=True)),
        (np.full((4, 2), 2, dtype=np.float32), FakeStatus(output_underflow=True)),
        (np.full((4, 2), 3, dtype=np.float32), FakeStatus()),
    )
    backend = FakeAudioBackend(blocks)
    source = SoundDeviceAudioSource(
        AudioStreamConfig(
            sampling_rate=48_000,
            channels=2,
            dtype="float32",
            block_size=4,
            device=7,
            queue_capacity=2,
            channel_names=("left", "right"),
        ),
        backend=backend,
    )
    import threading

    chunk = source.read(threading.Event())
    assert chunk is not None
    assert chunk.samples.shape == (4, 2)
    assert chunk.channels[0].name == "left"
    assert chunk.sequence == 1  # the oldest of three callback blocks was dropped
    assert backend.arguments["device"] == 7
    assert backend.arguments["block_size"] == 4
    assert source.metrics.input_overflows == 1
    assert source.metrics.output_underflows == 1
    assert source.metrics.dropped_blocks == 1
    source.close()
    assert backend.stream.closed


def test_pipeline_records_raw_and_processed_audio_separately() -> None:
    values = np.column_stack((np.arange(8, dtype=np.float32), -np.arange(8, dtype=np.float32)))
    source = SoundDeviceAudioSource(
        AudioStreamConfig(channels=2, block_size=8, queue_capacity=2),
        backend=FakeAudioBackend(((values, FakeStatus()),)),
    )
    raw = RecorderSink(stream_name="raw_audio")
    processed = RecorderSink(stream_name="processed_audio")
    pipeline = StreamPipeline()
    pipeline.configure(source, [RecorderNode(raw), GainNode(2.0)], [processed])
    pipeline.start()
    _wait_for(lambda: len(processed.session.chunks) == 1)
    pipeline.stop()
    pipeline.close()

    np.testing.assert_array_equal(raw.session.chunks[0].samples, values)
    np.testing.assert_array_equal(processed.session.chunks[0].samples, values * 2)
    assert raw.session.stream_name == "raw_audio"
    assert processed.session.stream_name == "processed_audio"
    assert raw.session.pipeline_configuration["source"] == "SoundDeviceAudioSource"
