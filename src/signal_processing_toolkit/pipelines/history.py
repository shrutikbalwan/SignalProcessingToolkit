"""Undo/redo snapshots for pipeline graph editing."""

from __future__ import annotations

from collections import deque
from collections.abc import Callable
from typing import Any

from signal_processing_toolkit.pipelines.graph import Edge, Node, PipelineGraph


class PipelineDocument:
    def __init__(self, graph: PipelineGraph | None = None, max_history: int = 50) -> None:
        self.graph = graph or PipelineGraph()
        self._undo: deque[tuple[dict[str, Any], dict[str, Any], str]] = deque(maxlen=max_history)
        self._redo: deque[tuple[dict[str, Any], dict[str, Any], str]] = deque(maxlen=max_history)

    def _commit(self, description: str, operation: Callable[[], None]) -> None:
        before = (
            self.graph.to_dict()
            if self.graph.nodes
            else {
                "schema": "signal-processing-toolkit.pipeline",
                "version": 1,
                "nodes": [],
                "edges": [],
            }
        )
        operation()
        try:
            after = self.graph.to_dict()
        except BaseException:
            self.graph = PipelineGraph.from_dict(before)
            raise
        self._undo.append((before, after, description))
        self._redo.clear()

    def add_node(self, node: Node) -> None:
        self._commit(f"add {node.kind}", lambda: self.graph.add_node(node))

    def remove_node(self, node_id: str) -> None:
        self._commit(f"delete {node_id}", lambda: self.graph.remove_node(node_id))

    def connect(self, edge: Edge) -> None:
        self._commit("connect nodes", lambda: self.graph.connect(edge))

    def disconnect(self, edge: Edge) -> None:
        self._commit("disconnect nodes", lambda: self.graph.disconnect(edge))

    def update_node(self, node_id: str, **changes: Any) -> None:
        def update() -> None:
            if node_id not in self.graph.nodes:
                raise KeyError(node_id)
            node = self.graph.nodes[node_id]
            for key, value in changes.items():
                if not hasattr(node, key):
                    raise AttributeError(key)
                setattr(node, key, value)

        self._commit(f"update {node_id}", update)

    def reorder(self, node_id: str, index: int) -> None:
        self._commit(f"reorder {node_id}", lambda: self.graph.reorder(node_id, index))

    def undo(self) -> bool:
        if not self._undo:
            return False
        before, after, description = self._undo.pop()
        self.graph = PipelineGraph.from_dict(before)
        self._redo.append((before, after, description))
        return True

    def redo(self) -> bool:
        if not self._redo:
            return False
        before, after, description = self._redo.pop()
        self.graph = PipelineGraph.from_dict(after)
        self._undo.append((before, after, description))
        return True

    @property
    def can_undo(self) -> bool:
        return bool(self._undo)

    @property
    def can_redo(self) -> bool:
        return bool(self._redo)
