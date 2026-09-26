from __future__ import annotations

import threading
import time

import numpy as np
import pytest
from scipy import signal as sp_signal

from signal_processing_toolkit.streaming import (
    BoundedRingBuffer,
    CallbackSink,
    ChannelMetadata,
    DCRemovalNode,
    FeatureExtractionNode,
    FFTNode,
    GainNode,
    OverflowPolicy,
    PipelineState,
    PSDNode,
    RecordedSession,
    RecorderSink,
    ReplaySource,
    ResamplerNode,
    SOSFilterNode,
    StreamChunk,
    StreamPipeline,
    SyntheticSource,
)


def make_chunk(samples: np.ndarray, sequence: int, *, rate: float = 1000.0) -> StreamChunk:
    channel_count = 1 if samples.ndim == 1 else samples.shape[1]
    return StreamChunk(
        samples,
        rate,
        tuple(ChannelMetadata(f"channel-{index}", "V") for index in range(channel_count)),
        sequence,
        10.0 + sequence * len(samples) / rate,
        100.0 + sequence,
        {"session": "test"},
    )


def test_chunk_validation_and_node_timestamp_propagation() -> None:
    chunk = make_chunk(np.arange(8.0), 7)
    result = GainNode(2.5).process(chunk)
    np.testing.assert_array_equal(result.samples, chunk.samples * 2.5)
    assert result.sequence == 7
    assert result.device_timestamp == chunk.device_timestamp
    assert result.host_timestamp == chunk.host_timestamp
    assert result.channels == chunk.channels
    assert result.attributes["session"] == "test"
    with pytest.raises(ValueError, match="metadata"):
        StreamChunk(np.zeros((4, 2)), 1000, (ChannelMetadata("one"),), 0, 0, 0)


def test_ring_buffer_overflow_policies_are_explicit() -> None:
    oldest = BoundedRingBuffer[int](2, OverflowPolicy.DROP_OLDEST)
    assert oldest.put(1) and oldest.put(2) and oldest.put(3)
    assert oldest.get() == 2
    assert oldest.get() == 3
    assert oldest.snapshot.dropped == 1

    newest = BoundedRingBuffer[int](1, OverflowPolicy.DROP_NEWEST)
    assert newest.put(1)
    assert not newest.put(2)
    assert newest.get() == 1
    assert newest.snapshot.dropped == 1

    strict = BoundedRingBuffer[int](1, OverflowPolicy.RAISE)
    strict.put(1)
    with pytest.raises(BufferError, match="full"):
        strict.put(2)

    blocking = BoundedRingBuffer[int](1, OverflowPolicy.BLOCK)
    blocking.put(1)
    consumed: list[int | None] = []
    consumer = threading.Thread(target=lambda: (time.sleep(0.02), consumed.append(blocking.get())))
    consumer.start()
    assert blocking.put(2, timeout=0.5)
    consumer.join()
    assert consumed == [1]
    assert blocking.get() == 2


def test_stateful_nodes_are_continuous_across_chunk_boundaries() -> None:
    rng = np.random.default_rng(12)
    samples = rng.standard_normal(2048) + 2.0
    chunks = [make_chunk(part, index) for index, part in enumerate(np.array_split(samples, 8))]

    dc_stream = DCRemovalNode(4.0)
    streamed_dc = np.concatenate([dc_stream.process(chunk).samples for chunk in chunks])
    alpha = np.exp(-2 * np.pi * 4.0 / 1000.0)
    expected_dc = sp_signal.lfilter([1.0, -1.0], [1.0, -alpha], samples)
    np.testing.assert_allclose(streamed_dc, expected_dc, rtol=1e-12, atol=1e-12)

    sos = sp_signal.butter(8, 100, fs=1000, output="sos")
    filter_node = SOSFilterNode(sos)
    streamed = np.concatenate([filter_node.process(chunk).samples for chunk in chunks])
    expected = sp_signal.sosfilt(sos, samples)
    np.testing.assert_allclose(streamed, expected, rtol=1e-12, atol=1e-12)


def test_streaming_resampler_is_chunk_boundary_invariant() -> None:
    samples = np.sin(2 * np.pi * 40 * np.arange(1200) / 1000)
    whole = ResamplerNode(1500).process(make_chunk(samples, 0)).samples
    chunked_node = ResamplerNode(1500)
    chunked = np.concatenate(
        [
            chunked_node.process(make_chunk(part, index)).samples
            for index, part in enumerate(np.array_split(samples, 7))
        ]
    )
    np.testing.assert_allclose(chunked, whole, rtol=1e-12, atol=1e-12)
    assert len(chunked) == 1800


def test_fft_psd_and_feature_nodes_attach_typed_results() -> None:
    samples = np.sin(2 * np.pi * 128 * np.arange(256) / 1024)
    chunk = make_chunk(samples, 3, rate=1024)
    fft = FFTNode(256).process(chunk)
    assert fft.attributes["domain"] == "frequency"
    assert fft.samples.shape == (129,)
    assert fft.sequence == chunk.sequence
    psd = PSDNode(128).process(chunk)
    assert psd.attributes["domain"] == "psd"
    assert np.all(psd.samples >= 0)
    featured = FeatureExtractionNode().process(chunk)
    features = featured.attributes["features"]
    assert np.asarray(features["rms"]).item() == pytest.approx(1 / np.sqrt(2))


def test_recorded_session_round_trip_and_deterministic_replay(tmp_path) -> None:
    original = tuple(make_chunk(np.arange(5.0) + index, index) for index in range(4))
    session = RecordedSession(original)
    path = tmp_path / "session.npz"
    session.save(path)
    restored = RecordedSession.load(path)
    assert [chunk.sequence for chunk in restored.chunks] == [0, 1, 2, 3]
    for expected, actual in zip(original, restored.chunks, strict=True):
        np.testing.assert_array_equal(actual.samples, expected.samples)
        assert actual.device_timestamp == expected.device_timestamp
        assert actual.host_timestamp == expected.host_timestamp

    recorder = RecorderSink()
    pipeline = StreamPipeline(queue_capacity=2, overflow_policy=OverflowPolicy.BLOCK)
    pipeline.configure(ReplaySource(restored.chunks), [GainNode(2)], [recorder])
    pipeline.start()
    assert pipeline.wait_until_stopped()
    assert [chunk.sequence for chunk in recorder.session.chunks] == [0, 1, 2, 3]
    assert [chunk.device_timestamp for chunk in recorder.session.chunks] == [
        chunk.device_timestamp for chunk in original
    ]
    assert [chunk.host_timestamp for chunk in recorder.session.chunks] == [
        chunk.host_timestamp for chunk in original
    ]
    pipeline.close()


def test_pipeline_start_stop_reset_and_restart() -> None:
    chunks = tuple(make_chunk(np.ones(16), index) for index in range(10))
    recorder = RecorderSink()
    pipeline = StreamPipeline(queue_capacity=3, overflow_policy=OverflowPolicy.BLOCK)
    pipeline.configure(ReplaySource(chunks), sinks=[recorder])

    for _ in range(3):
        pipeline.start()
        assert pipeline.wait_until_stopped()
        assert pipeline.state is PipelineState.STOPPED
        assert len(recorder.session.chunks) == len(chunks)
        pipeline.reset()
    pipeline.close()
    assert pipeline.state is PipelineState.CLOSED


def test_pipeline_reports_overflow_and_sustained_load() -> None:
    chunks = tuple(make_chunk(np.ones(64), index) for index in range(1500))

    def slow_sink(chunk: StreamChunk) -> None:
        del chunk
        time.sleep(0.0002)

    pipeline = StreamPipeline(queue_capacity=2, overflow_policy=OverflowPolicy.DROP_OLDEST)
    pipeline.configure(
        ReplaySource(chunks),
        [GainNode(0.5), FeatureExtractionNode()],
        [CallbackSink(slow_sink)],
    )
    started = time.perf_counter()
    pipeline.start()
    assert pipeline.wait_until_stopped(timeout=10)
    elapsed = time.perf_counter() - started
    metrics = pipeline.metrics
    assert metrics.produced_frames == len(chunks)
    assert metrics.dropped_frames > 0
    assert metrics.processed_frames + metrics.dropped_frames == metrics.produced_frames
    assert metrics.maximum_queue_depth <= 2
    assert metrics.maximum_processing_latency_seconds > 0
    assert elapsed < 10
    pipeline.close()


def test_pipeline_stop_joins_both_workers() -> None:
    pipeline = StreamPipeline(queue_capacity=2)
    pipeline.configure(
        SyntheticSource(chunk_size=32, sampling_rate=1000, real_time=True),
        sinks=[RecorderSink(maximum_chunks=10)],
    )
    pipeline.start()
    time.sleep(0.03)
    pipeline.stop()
    assert pipeline._producer is not None and not pipeline._producer.is_alive()
    assert pipeline._worker is not None and not pipeline._worker.is_alive()
    pipeline.close()


def test_pipeline_reconfigure_closes_replaced_resources() -> None:
    class TrackingSource(ReplaySource):
        closed = False

        def close(self) -> None:
            self.closed = True

    class TrackingSink(RecorderSink):
        closed = False

        def close(self) -> None:
            self.closed = True

    first_source = TrackingSource([make_chunk(np.ones(4), 0)])
    first_sink = TrackingSink()
    pipeline = StreamPipeline()
    pipeline.configure(first_source, sinks=[first_sink])
    pipeline.configure(
        TrackingSource([make_chunk(np.ones(4), 1)]),
        sinks=[TrackingSink()],
    )
    assert first_source.closed
    assert first_sink.closed
    pipeline.close()


def test_failed_reconfiguration_closes_replacement_and_retains_previous_source() -> None:
    class FailingSource(ReplaySource):
        closed = False

        def configure(self, settings=None) -> None:
            del settings
            raise ValueError("invalid device settings")

        def close(self) -> None:
            self.closed = True

    recorder = RecorderSink()
    original = ReplaySource([make_chunk(np.ones(4), 0)])
    replacement = FailingSource([make_chunk(np.zeros(4), 1)])
    pipeline = StreamPipeline()
    pipeline.configure(original, sinks=[recorder])

    with pytest.raises(ValueError, match="invalid device settings"):
        pipeline.configure(replacement, sinks=[recorder])

    assert replacement.closed
    pipeline.start()
    assert pipeline.wait_until_stopped()
    np.testing.assert_array_equal(recorder.session.chunks[0].samples, np.ones(4))
    pipeline.close()


def test_pipeline_failure_is_reported_and_can_be_closed() -> None:
    def fail(chunk: StreamChunk) -> None:
        del chunk
        raise RuntimeError("sink failed")

    pipeline = StreamPipeline(overflow_policy=OverflowPolicy.BLOCK)
    pipeline.configure(ReplaySource([make_chunk(np.ones(8), 0)]), sinks=[CallbackSink(fail)])
    pipeline.start()
    assert pipeline.wait_until_stopped()
    assert pipeline.state is PipelineState.FAILED
    assert isinstance(pipeline.error, RuntimeError)
    pipeline.close()
    assert pipeline.state is PipelineState.CLOSED


def test_multichannel_nodes_and_resampler_tail() -> None:
    samples = np.column_stack((np.arange(12.0), -np.arange(12.0)))
    chunk = make_chunk(samples, 0, rate=1000)
    gained = GainNode(2).process(chunk)
    assert gained.samples.shape == samples.shape
    sos = sp_signal.butter(4, 100, fs=1000, output="sos")
    filtered = SOSFilterNode(sos).process(gained)
    assert filtered.samples.shape == samples.shape

    recorder = RecorderSink()
    pipeline = StreamPipeline(overflow_policy=OverflowPolicy.BLOCK)
    pipeline.configure(ReplaySource([chunk]), [ResamplerNode(1500)], [recorder])
    pipeline.start()
    assert pipeline.wait_until_stopped()
    recorded = recorder.session.chunks
    assert len(recorded) == 2
    assert recorded[0].samples.shape == (18, 2)
    assert recorded[1].attributes["resampler_flush"] is True
    assert recorded[1].channel_count == 2
    pipeline.close()
