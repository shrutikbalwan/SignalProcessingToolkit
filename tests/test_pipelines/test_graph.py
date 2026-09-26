from __future__ import annotations

import numpy as np
import pytest

from signal_processing_toolkit.pipelines import (
    TEMPLATE_NAMES,
    Edge,
    GraphExecutor,
    GraphValidationError,
    Node,
    PipelineDocument,
    PipelineGraph,
    PortSpec,
    register_node_definition,
    template,
)
from signal_processing_toolkit.streaming.model import ChannelMetadata, StreamChunk


def make_graph() -> PipelineGraph:
    graph = PipelineGraph()
    graph.add_node(Node("source", "input"))
    graph.add_node(Node("gain", "gain", parameters={"gain": 2.0}))
    graph.add_node(Node("sink", "output"))
    graph.connect(Edge("source", "out", "gain", "in"))
    graph.connect(Edge("gain", "out", "sink", "in"))
    return graph


def make_chunk(sequence: int, values: np.ndarray) -> StreamChunk:
    return StreamChunk(
        values,
        1000.0,
        (ChannelMetadata("x", "V"),),
        sequence,
        sequence * values.shape[0] / 1000.0,
    )


def test_topological_order_and_cycle_prevention() -> None:
    graph = make_graph()
    assert graph.topological_order() == ("source", "gain", "sink")
    cycle = PipelineGraph()
    for node_id in ("a", "b", "c"):
        cycle.add_node(Node(node_id, "gain"))
    cycle.connect(Edge("a", "out", "b", "in"))
    cycle.connect(Edge("b", "out", "c", "in"))
    with pytest.raises(GraphValidationError, match="cycle"):
        cycle.connect(Edge("c", "out", "a", "in"))


def test_typed_connections_reject_domain_dtype_and_sample_rate_mismatches() -> None:
    register_node_definition(
        "rate_100",
        {"in": PortSpec("in", sampling_rate=100.0)},
        {"out": PortSpec("out", sampling_rate=100.0)},
    )
    register_node_definition(
        "rate_200",
        {"in": PortSpec("in", sampling_rate=200.0)},
        {"out": PortSpec("out", sampling_rate=200.0)},
    )
    graph = PipelineGraph()
    graph.add_node(Node("a", "rate_100"))
    graph.add_node(Node("b", "rate_200"))
    with pytest.raises(GraphValidationError, match="sample rates"):
        graph.connect(Edge("a", "out", "b", "in"))

    graph = PipelineGraph()
    graph.add_node(Node("a", "fft"))
    graph.add_node(Node("b", "gain"))
    with pytest.raises(GraphValidationError, match="data types|dtypes"):
        graph.connect(Edge("a", "out", "b", "in"))


def test_serialization_round_trip_and_schema_migration() -> None:
    original = make_graph()
    restored = PipelineGraph.from_dict(original.to_dict())
    assert restored.to_dict() == original.to_dict()
    old = {
        "version": 0,
        "nodes": [node.to_dict() for node in original.nodes.values()],
        "connections": [edge.to_dict() for edge in original.edges],
    }
    assert PipelineGraph.from_dict(old).to_dict() == original.to_dict()


def test_document_undo_redo_and_saved_graph_execution() -> None:
    document = PipelineDocument()
    document.add_node(Node("source", "input"))
    document.add_node(Node("gain", "gain", parameters={"gain": 2.0}))
    document.add_node(Node("sink", "output"))
    document.connect(Edge("source", "out", "gain", "in"))
    document.connect(Edge("gain", "out", "sink", "in"))
    saved = document.graph.to_dict()
    document.undo()
    assert len(document.graph.edges) == 1
    document.redo()
    assert document.graph.to_dict() == saved
    reopened = PipelineGraph.from_dict(saved)
    chunks = [make_chunk(0, np.ones((8, 1))), make_chunk(1, np.full((8, 1), 2.0))]
    first = GraphExecutor(reopened).run_offline(chunks)
    second = GraphExecutor(reopened).run_streaming(chunks)
    assert [item.samples.tolist() for item in first] == [item.samples.tolist() for item in second]
    assert np.allclose(first[0].samples, 2.0)


def test_all_templates_are_valid_and_named() -> None:
    for name in TEMPLATE_NAMES:
        graph = template(name)
        graph.assert_valid()
        assert graph.topological_order()[0] == "input"
        assert graph.topological_order()[-1] == "output"
