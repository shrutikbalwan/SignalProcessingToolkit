from __future__ import annotations

import logging
import threading
import time
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from enum import StrEnum
from typing import Any

from signal_processing_toolkit.streaming.buffer import (
    BoundedRingBuffer,
    BufferClosedError,
    OverflowPolicy,
)
from signal_processing_toolkit.streaming.interfaces import ProcessingNode, StreamSink, StreamSource
from signal_processing_toolkit.streaming.model import StreamChunk

logger = logging.getLogger(__name__)


class PipelineState(StrEnum):
    CREATED = "created"
    CONFIGURED = "configured"
    RUNNING = "running"
    PAUSED = "paused"
    STOPPED = "stopped"
    CLOSED = "closed"
    FAILED = "failed"


@dataclass(frozen=True, slots=True)
class PipelineMetrics:
    produced_frames: int
    processed_frames: int
    dropped_frames: int
    queue_depth: int
    maximum_queue_depth: int
    mean_processing_latency_seconds: float
    maximum_processing_latency_seconds: float
    last_processing_latency_seconds: float


class StreamPipeline:
    """Source → bounded ring buffer → processing nodes → sinks.

    A producer thread owns source reads and a separate worker thread owns every
    node and sink call. No Qt object is touched by either thread.
    """

    def __init__(
        self,
        *,
        queue_capacity: int = 8,
        overflow_policy: OverflowPolicy = OverflowPolicy.DROP_OLDEST,
    ) -> None:
        self._buffer: BoundedRingBuffer[StreamChunk] = BoundedRingBuffer(
            queue_capacity, overflow_policy
        )
        self._source: StreamSource | None = None
        self._nodes: tuple[ProcessingNode, ...] = ()
        self._sinks: tuple[StreamSink, ...] = ()
        self._state = PipelineState.CREATED
        self._state_lock = threading.RLock()
        self._metrics_lock = threading.Lock()
        self._cancel = threading.Event()
        self._run_gate = threading.Event()
        self._source_done = threading.Event()
        self._producer: threading.Thread | None = None
        self._worker: threading.Thread | None = None
        self._produced = 0
        self._processed = 0
        self._latency_sum = 0.0
        self._latency_max = 0.0
        self._latency_last = 0.0
        self._error: BaseException | None = None
        self._configuration: dict[str, Any] = {}

    def configure(
        self,
        source: StreamSource,
        nodes: Sequence[ProcessingNode] = (),
        sinks: Sequence[StreamSink] = (),
        *,
        source_settings: Mapping[str, Any] | None = None,
        node_settings: Sequence[Mapping[str, Any] | None] | None = None,
    ) -> None:
        with self._state_lock:
            if self._state in {PipelineState.RUNNING, PipelineState.PAUSED, PipelineState.CLOSED}:
                raise RuntimeError(f"Cannot configure a {self._state.value} pipeline")
            if not sinks:
                raise ValueError("A streaming pipeline requires at least one sink")
            if node_settings is not None and len(node_settings) != len(nodes):
                raise ValueError("node_settings must contain one entry per processing node")
            old_source = self._source
            settings = node_settings or (None,) * len(nodes)
            try:
                source.configure(source_settings)
                for node, node_config in zip(nodes, settings, strict=True):
                    node.configure(node_config)
            except BaseException:
                if source is not old_source:
                    source.close()
                raise
            if old_source is not None and old_source is not source:
                old_source.close()
            replacement_sink_ids = {id(sink) for sink in sinks}
            for old_sink in self._sinks:
                if id(old_sink) not in replacement_sink_ids:
                    old_sink.close()
            self._source = source
            self._nodes = tuple(nodes)
            self._sinks = tuple(sinks)
            self._configuration = {
                "source": type(source).__name__,
                "source_settings": dict(source_settings or {}),
                "nodes": [type(node).__name__ for node in nodes],
                "node_settings": [dict(item or {}) for item in settings],
                "sinks": [type(sink).__name__ for sink in sinks],
                "queue_capacity": self._buffer.capacity,
                "overflow_policy": self._buffer.policy.value,
            }
            for recorder in self._session_recorders():
                setter = getattr(recorder, "set_pipeline_configuration", None)
                if setter is not None:
                    setter(self._configuration)
            self._state = PipelineState.CONFIGURED
            self._error = None

    def start(self) -> None:
        with self._state_lock:
            if self._state is PipelineState.PAUSED:
                self.resume()
                return
            if self._state is PipelineState.RUNNING:
                return
            if self._state not in {PipelineState.CONFIGURED, PipelineState.STOPPED}:
                raise RuntimeError(f"Cannot start a {self._state.value} pipeline")
            if self._source is None:
                raise RuntimeError("Pipeline has no configured source")
            self._cancel.clear()
            self._source_done.clear()
            self._run_gate.set()
            self._buffer.reopen()
            self._buffer.clear()
            self._error = None
            self._state = PipelineState.RUNNING
            self._producer = threading.Thread(
                target=self._source_loop, name="spt-stream-source", daemon=True
            )
            self._worker = threading.Thread(
                target=self._worker_loop, name="spt-stream-worker", daemon=True
            )
            self._producer.start()
            self._worker.start()

    def pause(self) -> None:
        with self._state_lock:
            if self._state is not PipelineState.RUNNING:
                raise RuntimeError("Only a running pipeline can be paused")
            self._run_gate.clear()
            self._state = PipelineState.PAUSED

    def resume(self) -> None:
        with self._state_lock:
            if self._state is not PipelineState.PAUSED:
                raise RuntimeError("Only a paused pipeline can be resumed")
            self._state = PipelineState.RUNNING
            self._run_gate.set()

    def stop(self, timeout: float = 5.0) -> None:
        with self._state_lock:
            if self._state in {
                PipelineState.CREATED,
                PipelineState.CONFIGURED,
                PipelineState.STOPPED,
                PipelineState.CLOSED,
            }:
                if self._state is PipelineState.CONFIGURED:
                    self._state = PipelineState.STOPPED
                return
            self._cancel.set()
            self._run_gate.set()
            self._buffer.close()
            producer, worker = self._producer, self._worker
        deadline = time.monotonic() + timeout
        for thread in (producer, worker):
            if thread is not None and thread is not threading.current_thread():
                thread.join(max(0.0, deadline - time.monotonic()))
        alive = [
            thread.name for thread in (producer, worker) if thread is not None and thread.is_alive()
        ]
        if alive:
            raise TimeoutError(f"Streaming workers did not stop: {', '.join(alive)}")
        with self._state_lock:
            if self._state is not PipelineState.FAILED:
                self._state = PipelineState.STOPPED
            self._buffer.clear()

    def reset(self) -> None:
        with self._state_lock:
            if self._state in {PipelineState.RUNNING, PipelineState.PAUSED, PipelineState.CLOSED}:
                raise RuntimeError(f"Cannot reset a {self._state.value} pipeline")
            if self._source is not None:
                self._source.reset()
            for node in self._nodes:
                node.reset()
            for sink in self._sinks:
                sink.reset()
            self._buffer.reopen()
            self._buffer.clear(reset_metrics=True)
            with self._metrics_lock:
                self._produced = self._processed = 0
                self._latency_sum = self._latency_max = self._latency_last = 0.0
            self._source_done.clear()
            self._cancel.clear()
            self._error = None
            self._state = PipelineState.CONFIGURED

    def close(self, timeout: float = 5.0) -> None:
        if self.state in {PipelineState.RUNNING, PipelineState.PAUSED, PipelineState.FAILED}:
            self.stop(timeout)
        with self._state_lock:
            if self._state is PipelineState.CLOSED:
                return
            if self._source is not None:
                self._source.close()
                self._capture_source_events()
            for sink in self._sinks:
                sink.close()
            for node in self._nodes:
                close = getattr(node, "close", None)
                if close is not None:
                    close()
            self._buffer.close()
            self._state = PipelineState.CLOSED

    def _wait_until_running(self) -> bool:
        while not self._cancel.is_set():
            if self._run_gate.wait(0.05):
                return True
        return False

    def _source_loop(self) -> None:
        assert self._source is not None
        try:
            while not self._cancel.is_set():
                if not self._wait_until_running():
                    break
                chunk = self._source.read(self._cancel)
                self._capture_source_events()
                if chunk is None:
                    if self._source.exhausted or self._cancel.is_set():
                        break
                    continue
                with self._metrics_lock:
                    self._produced += 1
                while not self._cancel.is_set():
                    try:
                        accepted = self._buffer.put(chunk, timeout=0.05)
                    except BufferClosedError:
                        return
                    if accepted or self._buffer.policy is not OverflowPolicy.BLOCK:
                        break
        except BaseException as exc:
            self._fail(exc)
        finally:
            self._capture_source_events()
            self._source_done.set()

    def _session_recorders(self) -> tuple[object, ...]:
        recorders: list[object] = list(self._sinks)
        for node in self._nodes:
            recorder = getattr(node, "recorder", None)
            if recorder is not None:
                recorders.append(recorder)
        unique: dict[int, object] = {id(recorder): recorder for recorder in recorders}
        return tuple(unique.values())

    def _capture_source_events(self) -> None:
        if self._source is None:
            return
        drain = getattr(self._source, "drain_events", None)
        if drain is None:
            return
        events = drain()
        if not events:
            return
        for recorder in self._session_recorders():
            record = getattr(recorder, "record_events", None)
            if record is not None:
                record(events)

    def _worker_loop(self) -> None:
        try:
            while not self._cancel.is_set():
                if not self._wait_until_running():
                    break
                chunk = self._buffer.get(timeout=0.05)
                if chunk is None:
                    if self._source_done.is_set() and self._buffer.snapshot.depth == 0:
                        break
                    continue
                started = time.perf_counter()
                output: StreamChunk | None = chunk
                for node in self._nodes:
                    if output is None:
                        break
                    output = node.process(output)
                if output is not None:
                    for sink in self._sinks:
                        sink.consume(output)
                latency = time.perf_counter() - started
                with self._metrics_lock:
                    self._processed += 1
                    self._latency_last = latency
                    self._latency_sum += latency
                    self._latency_max = max(self._latency_max, latency)
            if self._source_done.is_set() and not self._cancel.is_set():
                self._flush_nodes()
        except BaseException as exc:
            self._fail(exc)
        finally:
            if self._source_done.is_set() and not self._cancel.is_set():
                with self._state_lock:
                    if self._state in {PipelineState.RUNNING, PipelineState.PAUSED}:
                        self._state = PipelineState.STOPPED

    def _flush_nodes(self) -> None:
        """Propagate finite node tails through every downstream node and sink."""
        for index, node in enumerate(self._nodes):
            flush = getattr(node, "flush", None)
            output = None if flush is None else flush()
            if output is None:
                continue
            for downstream in self._nodes[index + 1 :]:
                output = downstream.process(output)
                if output is None:
                    break
            if output is not None:
                for sink in self._sinks:
                    sink.consume(output)

    def _fail(self, error: BaseException) -> None:
        logger.exception("Streaming pipeline failed", exc_info=error)
        with self._state_lock:
            self._error = error
            self._state = PipelineState.FAILED
            self._cancel.set()
            self._run_gate.set()
            self._buffer.close()

    def wait_until_stopped(self, timeout: float = 5.0) -> bool:
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            if self.state in {PipelineState.STOPPED, PipelineState.FAILED}:
                return True
            time.sleep(0.005)
        return False

    @property
    def state(self) -> PipelineState:
        with self._state_lock:
            return self._state

    @property
    def error(self) -> BaseException | None:
        with self._state_lock:
            return self._error

    @property
    def metrics(self) -> PipelineMetrics:
        buffer = self._buffer.snapshot
        with self._metrics_lock:
            mean = self._latency_sum / self._processed if self._processed else 0.0
            return PipelineMetrics(
                self._produced,
                self._processed,
                buffer.dropped,
                buffer.depth,
                buffer.maximum_depth,
                mean,
                self._latency_max,
                self._latency_last,
            )
