"""Graph model, port compatibility validation and versioned persistence."""

from __future__ import annotations

from collections import OrderedDict, deque
from dataclasses import dataclass, field
from typing import Any

import numpy as np

SCHEMA_NAME = "signal-processing-toolkit.pipeline"
SCHEMA_VERSION = 1
_CUSTOM_DEFINITIONS: dict[str, tuple[dict[str, PortSpec], dict[str, PortSpec]]] = {}


@dataclass(frozen=True, slots=True)
class PortSpec:
    """A typed stream port.

    ``shape`` follows the sample-major convention. ``None`` is a wildcard;
    channel count and sample rate can also be left unknown for generic nodes.
    """

    name: str
    data_type: str = "signal"
    dtype: str = "float32"
    shape: tuple[int | None, ...] = (None, None)
    channels: int | None = None
    sampling_rate: float | None = None
    variadic: bool = False

    def __post_init__(self) -> None:
        if not self.name.strip():
            raise ValueError("port name cannot be empty")
        if any(d is not None and d < 0 for d in self.shape):
            raise ValueError("port dimensions must be non-negative or None")
        if self.channels is not None and self.channels <= 0:
            raise ValueError("port channel count must be positive")
        if self.sampling_rate is not None and (
            not np.isfinite(self.sampling_rate) or self.sampling_rate <= 0
        ):
            raise ValueError("port sampling rate must be finite and positive")

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "data_type": self.data_type,
            "dtype": self.dtype,
            "shape": list(self.shape),
            "channels": self.channels,
            "sampling_rate": self.sampling_rate,
            "variadic": self.variadic,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> PortSpec:
        return cls(
            name=str(data["name"]),
            data_type=str(data.get("data_type", "signal")),
            dtype=str(data.get("dtype", "float32")),
            shape=tuple(data.get("shape", (None, None))),
            channels=data.get("channels"),
            sampling_rate=data.get("sampling_rate"),
            variadic=bool(data.get("variadic", False)),
        )


@dataclass(slots=True)
class Node:
    node_id: str
    kind: str
    label: str | None = None
    parameters: dict[str, Any] = field(default_factory=dict)
    enabled: bool = True
    bypass: bool = False
    mute: bool = False
    position: tuple[float, float] = (0.0, 0.0)

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.node_id,
            "kind": self.kind,
            "label": self.label,
            "parameters": _json_safe(self.parameters),
            "enabled": self.enabled,
            "bypass": self.bypass,
            "mute": self.mute,
            "position": list(self.position),
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Node:
        return cls(
            node_id=str(data["id"]),
            kind=str(data["kind"]),
            label=data.get("label"),
            parameters=dict(data.get("parameters", {})),
            enabled=bool(data.get("enabled", True)),
            bypass=bool(data.get("bypass", False)),
            mute=bool(data.get("mute", False)),
            position=tuple(data.get("position", (0.0, 0.0))),
        )


@dataclass(frozen=True, slots=True)
class Edge:
    source_node: str
    source_port: str
    target_node: str
    target_port: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "source": {"node": self.source_node, "port": self.source_port},
            "target": {"node": self.target_node, "port": self.target_port},
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Edge:
        # Version 0 accepted flat source_node/source_port keys.
        source = data.get("source", {})
        target = data.get("target", {})
        return cls(
            str(data.get("source_node", source.get("node"))),
            str(data.get("source_port", source.get("port", "out"))),
            str(data.get("target_node", target.get("node"))),
            str(data.get("target_port", target.get("port", "in"))),
        )


class GraphValidationError(ValueError):
    def __init__(self, issues: list[str] | tuple[str, ...]) -> None:
        self.issues = tuple(issues)
        super().__init__("; ".join(self.issues))


def _ports(kind: str) -> tuple[dict[str, PortSpec], dict[str, PortSpec]]:
    signal = PortSpec("in", shape=(None, None), channels=None)
    output = PortSpec("out", shape=(None, None), channels=None)
    definitions: dict[str, tuple[dict[str, PortSpec], dict[str, PortSpec]]] = {
        "input": ({}, {"out": output}),
        "output": ({"in": PortSpec("in", "any", "any", (None, None))}, {}),
        "gain": ({"in": signal}, {"out": output}),
        "dc_removal": ({"in": signal}, {"out": output}),
        "sos_filter": ({"in": signal}, {"out": output}),
        "resampler": ({"in": signal}, {"out": output}),
        "fft": (
            {"in": signal},
            {"out": PortSpec("out", "spectrum", "complex64", (None, None))},
        ),
        "psd": (
            {"in": signal},
            {"out": PortSpec("out", "psd", "float32", (None, None))},
        ),
        "feature": (
            {"in": signal},
            {"out": PortSpec("out", "signal", "float32", (None, None))},
        ),
        "preview": ({"in": signal}, {"out": output}),
        "edge_ai": ({"in": signal}, {"out": PortSpec("out", "features")}),
    }
    definitions.update(_CUSTOM_DEFINITIONS)
    if kind not in definitions:
        raise GraphValidationError((f"Unknown node kind: {kind}",))
    return definitions[kind]


def register_node_definition(
    kind: str,
    inputs: dict[str, PortSpec],
    outputs: dict[str, PortSpec],
) -> None:
    """Register a typed extension kind used by validation and persistence."""
    if not kind.strip() or kind in {"input", "output"}:
        raise ValueError("custom node kind must be a non-reserved non-empty name")
    _CUSTOM_DEFINITIONS[kind] = (dict(inputs), dict(outputs))


class PipelineGraph:
    def __init__(self) -> None:
        self.nodes: OrderedDict[str, Node] = OrderedDict()
        self.edges: list[Edge] = []

    def copy(self) -> PipelineGraph:
        return self.from_dict(self.to_dict())

    def add_node(self, node: Node) -> None:
        if node.node_id in self.nodes:
            raise ValueError(f"Duplicate node id: {node.node_id}")
        _ports(node.kind)
        self.nodes[node.node_id] = node

    def remove_node(self, node_id: str) -> None:
        if node_id not in self.nodes:
            raise KeyError(node_id)
        del self.nodes[node_id]
        self.edges = [
            edge
            for edge in self.edges
            if edge.source_node != node_id and edge.target_node != node_id
        ]

    def connect(self, edge: Edge) -> None:
        if edge in self.edges:
            return
        self.edges.append(edge)
        try:
            self.assert_valid()
        except GraphValidationError:
            self.edges.pop()
            raise

    def disconnect(self, edge: Edge) -> None:
        self.edges.remove(edge)

    def reorder(self, node_id: str, index: int) -> None:
        if node_id not in self.nodes:
            raise KeyError(node_id)
        items = list(self.nodes.items())
        item = items.pop(next(i for i, (key, _) in enumerate(items) if key == node_id))
        items.insert(max(0, min(index, len(items))), item)
        self.nodes = OrderedDict(items)

    def topological_order(self) -> tuple[str, ...]:
        self.assert_valid()
        incoming = dict.fromkeys(self.nodes, 0)
        outgoing: dict[str, list[str]] = {node_id: [] for node_id in self.nodes}
        for edge in self.edges:
            incoming[edge.target_node] += 1
            outgoing[edge.source_node].append(edge.target_node)
        ready = deque(node_id for node_id, count in incoming.items() if count == 0)
        result: list[str] = []
        while ready:
            node_id = ready.popleft()
            result.append(node_id)
            for downstream in outgoing[node_id]:
                incoming[downstream] -= 1
                if incoming[downstream] == 0:
                    ready.append(downstream)
        if len(result) != len(self.nodes):
            raise GraphValidationError(("Pipeline graph contains a cycle",))
        return tuple(result)

    def validate(self) -> tuple[str, ...]:
        issues: list[str] = []
        for node_id, node in self.nodes.items():
            try:
                inputs, outputs = _ports(node.kind)
            except GraphValidationError as error:
                issues.extend(error.issues)
                continue
            del outputs
            for edge in self.edges:
                if edge.target_node == node_id and edge.target_port not in inputs:
                    issues.append(f"Unknown target port {node_id}.{edge.target_port}")
        for edge in self.edges:
            source = self.nodes.get(edge.source_node)
            target = self.nodes.get(edge.target_node)
            if source is None or target is None:
                issues.append(f"Edge references missing node: {edge}")
                continue
            source_ports, source_outputs = _ports(source.kind)
            target_inputs, target_ports = _ports(target.kind)
            del source_ports, target_ports
            source_spec = source_outputs.get(edge.source_port)
            target_spec = target_inputs.get(edge.target_port)
            if source_spec is None or target_spec is None:
                issues.append(f"Unknown port in edge: {edge}")
                continue
            issues.extend(_compatibility_issues(source_spec, target_spec, edge))
        for target_id in self.nodes:
            target_edges = [edge for edge in self.edges if edge.target_node == target_id]
            target_inputs, _ = _ports(self.nodes[target_id].kind)
            for port_name, port in target_inputs.items():
                count = sum(edge.target_port == port_name for edge in target_edges)
                if count > 1 and not port.variadic:
                    issues.append(f"Input port {target_id}.{port_name} has multiple connections")
        if not issues and self._has_cycle():
            issues.append("Pipeline graph contains a cycle")
        return tuple(dict.fromkeys(issues))

    def assert_valid(self) -> None:
        issues = self.validate()
        if issues:
            raise GraphValidationError(issues)

    def to_dict(self) -> dict[str, Any]:
        self.assert_valid()
        return {
            "schema": SCHEMA_NAME,
            "version": SCHEMA_VERSION,
            "nodes": [node.to_dict() for node in self.nodes.values()],
            "edges": [edge.to_dict() for edge in self.edges],
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> PipelineGraph:
        migrated = migrate_schema(data)
        graph = cls()
        for node in migrated["nodes"]:
            graph.add_node(Node.from_dict(node))
        graph.edges = [Edge.from_dict(edge) for edge in migrated["edges"]]
        graph.assert_valid()
        return graph

    def _has_cycle(self) -> bool:
        visiting: set[str] = set()
        visited: set[str] = set()

        def visit(node_id: str) -> bool:
            if node_id in visiting:
                return True
            if node_id in visited:
                return False
            visiting.add(node_id)
            if any(edge.source_node == node_id and visit(edge.target_node) for edge in self.edges):
                return True
            visiting.remove(node_id)
            visited.add(node_id)
            return False

        return any(visit(node_id) for node_id in self.nodes)


def _compatibility_issues(source: PortSpec, target: PortSpec, edge: Edge) -> list[str]:
    prefix = (
        f"Incompatible connection {edge.source_node}.{edge.source_port} -> "
        f"{edge.target_node}.{edge.target_port}"
    )
    issues: list[str] = []
    if source.data_type != target.data_type and "any" not in {source.data_type, target.data_type}:
        issues.append(f"{prefix}: data types {source.data_type!r} and {target.data_type!r}")
    if source.dtype != target.dtype and "any" not in {source.dtype, target.dtype}:
        issues.append(f"{prefix}: dtypes {source.dtype!r} and {target.dtype!r}")
    if (
        source.channels is not None
        and target.channels is not None
        and source.channels != target.channels
    ):
        issues.append(f"{prefix}: channel counts {source.channels} and {target.channels}")
    if (
        source.sampling_rate is not None
        and target.sampling_rate is not None
        and not np.isclose(source.sampling_rate, target.sampling_rate, rtol=0, atol=1e-12)
    ):
        issues.append(f"{prefix}: sample rates {source.sampling_rate} and {target.sampling_rate}")
    if len(source.shape) != len(target.shape):
        issues.append(f"{prefix}: ranks {len(source.shape)} and {len(target.shape)}")
    else:
        for axis, (source_dim, target_dim) in enumerate(
            zip(source.shape, target.shape, strict=True)
        ):
            if source_dim is not None and target_dim is not None and source_dim != target_dim:
                issues.append(f"{prefix}: shape axis {axis} is {source_dim} and {target_dim}")
    return issues


def migrate_schema(data: dict[str, Any]) -> dict[str, Any]:
    version = int(data.get("version", 0))
    if data.get("schema", SCHEMA_NAME) not in {SCHEMA_NAME, "spt.pipeline"}:
        raise GraphValidationError(("Unknown pipeline schema",))
    if version > SCHEMA_VERSION:
        raise GraphValidationError((f"Unsupported pipeline schema version: {version}",))
    if version == 0:
        return {
            "schema": SCHEMA_NAME,
            "version": 1,
            "nodes": data.get("nodes", []),
            "edges": data.get("edges", data.get("connections", [])),
        }
    return data


def _json_safe(value: Any) -> Any:
    if isinstance(value, np.ndarray):
        return value.tolist()
    if isinstance(value, np.generic):
        return value.item()
    if isinstance(value, dict):
        return {str(key): _json_safe(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_json_safe(item) for item in value]
    return value
