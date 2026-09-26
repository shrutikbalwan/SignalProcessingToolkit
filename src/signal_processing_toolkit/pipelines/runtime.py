"""Execution adapters for graph nodes in offline and streaming contexts."""

from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Any

import numpy as np

from signal_processing_toolkit.pipelines.graph import Node, PipelineGraph
from signal_processing_toolkit.streaming.model import StreamChunk
from signal_processing_toolkit.streaming.nodes import (
    DCRemovalNode,
    FeatureExtractionNode,
    FFTNode,
    GainNode,
    PSDNode,
    ResamplerNode,
    SOSFilterNode,
)


@dataclass(frozen=True, slots=True)
class NodeRuntimeStatus:
    node_id: str
    state: str = "idle"
    latency_seconds: float = 0.0
    processed_chunks: int = 0
    error: str | None = None


class PipelineExecutionError(RuntimeError):
    pass


def create_processing_node(node: Node) -> Any:
    params = node.parameters
    factories = {
        "gain": lambda: GainNode(float(params.get("gain", 1.0))),
        "dc_removal": lambda: DCRemovalNode(float(params.get("cutoff_frequency", 5.0))),
        "sos_filter": lambda: SOSFilterNode(np.asarray(params.get("sos", [[1, 0, 0, 1, 0, 0]]))),
        "resampler": lambda: ResamplerNode(float(params.get("output_rate", 1000.0))),
        "fft": lambda: FFTNode(params.get("fft_length"), str(params.get("window", "hann"))),
        "psd": lambda: PSDNode(params.get("segment_length"), str(params.get("window", "hann"))),
        "feature": FeatureExtractionNode,
        "preview": lambda: _IdentityNode(),
        "edge_ai": lambda: _IdentityNode(),
        "input": lambda: _IdentityNode(),
        "output": lambda: _IdentityNode(),
    }
    try:
        return factories[node.kind]()
    except (KeyError, TypeError, ValueError) as error:
        raise PipelineExecutionError(f"Cannot create node {node.node_id}: {error}") from error


class _IdentityNode:
    def configure(self, settings: dict[str, Any] | None = None) -> None:
        del settings

    def process(self, chunk: StreamChunk) -> StreamChunk:
        return chunk

    def reset(self) -> None:
        return


class GraphExecutor:
    """Execute a validated graph one chunk at a time.

    Branches are supported. Nodes with multiple incoming ports are reserved for
    future typed join nodes; current definitions use one input port. The same
    executor is used for offline batches and for streaming chunks, so stateful
    nodes retain identical chunk-boundary behavior.
    """

    def __init__(self, graph: PipelineGraph) -> None:
        graph.assert_valid()
        self.graph = graph.copy()
        self._nodes = {
            node_id: create_processing_node(node) for node_id, node in self.graph.nodes.items()
        }
        self._statuses = {node_id: NodeRuntimeStatus(node_id) for node_id in self.graph.nodes}
        self._previews: dict[str, StreamChunk] = {}
        self.reset()

    def reset(self) -> None:
        for node in self._nodes.values():
            node.reset()
        self._previews.clear()
        self._statuses = {node_id: NodeRuntimeStatus(node_id) for node_id in self.graph.nodes}

    def process(self, chunk: StreamChunk) -> StreamChunk | None:
        values: dict[tuple[str, str], StreamChunk] = {}
        final: StreamChunk | None = None
        for node_id in self.graph.topological_order():
            node = self.graph.nodes[node_id]
            incoming = [edge for edge in self.graph.edges if edge.target_node == node_id]
            input_chunk = (
                chunk
                if not incoming
                else values[(incoming[0].source_node, incoming[0].source_port)]
            )
            if node.kind == "input" and incoming:
                raise PipelineExecutionError("Input nodes cannot have upstream connections")
            started = time.perf_counter()
            status = self._statuses[node_id]
            try:
                output = input_chunk
                if node.enabled and not node.bypass:
                    output = self._nodes[node_id].process(input_chunk)
                if node.mute:
                    output = output.with_samples(np.zeros_like(output.samples))
                self._previews[node_id] = output
                for edge in self.graph.edges:
                    if edge.source_node == node_id:
                        values[(node_id, edge.source_port)] = output
                if node.kind == "output" or not any(
                    edge.source_node == node_id for edge in self.graph.edges
                ):
                    final = output
                self._statuses[node_id] = NodeRuntimeStatus(
                    node_id,
                    "bypassed" if node.bypass else "disabled" if not node.enabled else "ok",
                    time.perf_counter() - started,
                    status.processed_chunks + 1,
                    None,
                )
            except BaseException as error:
                self._statuses[node_id] = NodeRuntimeStatus(
                    node_id,
                    "error",
                    time.perf_counter() - started,
                    status.processed_chunks,
                    str(error),
                )
                raise PipelineExecutionError(f"Node {node_id} failed: {error}") from error
        return final

    def run_offline(self, chunks: list[StreamChunk] | tuple[StreamChunk, ...]) -> list[StreamChunk]:
        self.reset()
        outputs = [result for chunk in chunks if (result := self.process(chunk)) is not None]
        return outputs

    def run_streaming(
        self, chunks: list[StreamChunk] | tuple[StreamChunk, ...]
    ) -> list[StreamChunk]:
        return self.run_offline(chunks)

    def preview(self, node_id: str) -> StreamChunk | None:
        return self._previews.get(node_id)

    @property
    def statuses(self) -> tuple[NodeRuntimeStatus, ...]:
        return tuple(self._statuses.values())


class GraphProcessingAdapter:
    """ProcessingNode adapter for use inside the existing StreamPipeline."""

    def __init__(self, graph: PipelineGraph) -> None:
        self.executor = GraphExecutor(graph)

    def configure(self, settings: dict[str, Any] | None = None) -> None:
        del settings

    def process(self, chunk: StreamChunk) -> StreamChunk | None:
        return self.executor.process(chunk)

    def reset(self) -> None:
        self.executor.reset()
