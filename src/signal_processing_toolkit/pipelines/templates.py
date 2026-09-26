"""Reusable, validated starter graphs."""

from __future__ import annotations

from signal_processing_toolkit.pipelines.graph import Edge, Node, PipelineGraph

TEMPLATE_NAMES = (
    "audio_spectrum_analyzer",
    "noise_removal_chain",
    "esp32_vibration_monitor",
    "bearing_envelope_analyzer",
    "edge_ai_anomaly_detector",
)


def _chain(kinds: list[str], parameters: dict[str, dict] | None = None) -> PipelineGraph:
    graph = PipelineGraph()
    settings = parameters or {}
    nodes = [Node("input", "input", "Input", position=(0, 0))]
    for index, kind in enumerate(kinds):
        nodes.append(
            Node(
                f"node_{index}",
                kind,
                parameters=settings.get(kind, {}),
                position=(220 * (index + 1), 0),
            )
        )
    nodes.append(Node("output", "output", "Output", position=(220 * (len(kinds) + 1), 0)))
    for node in nodes:
        graph.add_node(node)
    for first, second in zip(nodes, nodes[1:], strict=False):
        graph.edges.append(Edge(first.node_id, "out", second.node_id, "in"))
    graph.assert_valid()
    return graph


def template(name: str) -> PipelineGraph:
    if name not in TEMPLATE_NAMES:
        raise KeyError(name)
    if name == "audio_spectrum_analyzer":
        return _chain(["gain", "fft"])
    if name == "noise_removal_chain":
        return _chain(["dc_removal", "sos_filter"], {"dc_removal": {"cutoff_frequency": 5.0}})
    if name == "esp32_vibration_monitor":
        return _chain(["dc_removal", "resampler", "psd"], {"resampler": {"output_rate": 2000.0}})
    if name == "bearing_envelope_analyzer":
        return _chain(["dc_removal", "sos_filter", "feature"])
    return _chain(["feature", "edge_ai"])
