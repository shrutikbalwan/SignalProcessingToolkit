from __future__ import annotations

import json
from collections.abc import Callable
from pathlib import Path
from typing import Any

from PyQt6.QtCore import Qt, QTimer, pyqtSignal
from PyQt6.QtGui import QBrush, QColor, QPen
from PyQt6.QtWidgets import (
    QComboBox,
    QDoubleSpinBox,
    QFileDialog,
    QFormLayout,
    QGraphicsItem,
    QGraphicsRectItem,
    QGraphicsScene,
    QGraphicsTextItem,
    QGraphicsView,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QSplitter,
    QTableWidget,
    QTableWidgetItem,
    QToolButton,
    QVBoxLayout,
    QWidget,
)

from signal_processing_toolkit.models.signal import Signal
from signal_processing_toolkit.pipelines import (
    TEMPLATE_NAMES,
    Edge,
    GraphExecutor,
    GraphValidationError,
    Node,
    PipelineDocument,
    PipelineGraph,
    template,
)
from signal_processing_toolkit.ui.workers import TaskRunner


class PipelineNodeItem(QGraphicsRectItem):
    def __init__(self, node: Node, selected: Callable[[str], None]) -> None:
        super().__init__(0, 0, 170, 62)
        self.node_id = node.node_id
        self._selected = selected
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsMovable)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable)
        self.setBrush(QBrush(QColor("#263449")))
        self.setPen(QPen(QColor("#64748b"), 1.5))
        self.text = QGraphicsTextItem(node.label or node.kind, self)
        self.text.setDefaultTextColor(QColor("#f8fafc"))
        self.text.setPos(10, 8)
        self.status = QGraphicsTextItem("idle", self)
        self.status.setDefaultTextColor(QColor("#94a3b8"))
        self.status.setPos(10, 34)
        self.setPos(*node.position)

    def mousePressEvent(self, event: Any) -> None:  # noqa: N802
        self._selected(self.node_id)
        super().mousePressEvent(event)

    def update_status(self, state: str, latency: float, error: str | None) -> None:
        self.status.setPlainText(
            f"{state} · {latency * 1000:.2f} ms" if error is None else f"error: {error[:20]}"
        )
        self.setPen(QPen(QColor("#ef4444" if error else "#22c55e"), 1.5))


class PipelineScene(QGraphicsScene):
    node_selected = pyqtSignal(str)

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.items_by_id: dict[str, PipelineNodeItem] = {}

    def load_graph(self, graph: PipelineGraph) -> None:
        self.clear()
        self.items_by_id.clear()
        for node in graph.nodes.values():
            item = PipelineNodeItem(node, self.node_selected.emit)
            self.addItem(item)
            self.items_by_id[node.node_id] = item
        for edge in graph.edges:
            source = self.items_by_id[edge.source_node]
            target = self.items_by_id[edge.target_node]
            line = self.addLine(
                source.x() + 170,
                source.y() + 31,
                target.x(),
                target.y() + 31,
                QPen(QColor("#64748b"), 1.2),
            )
            if line is not None:
                line.setZValue(-1)


class PipelineEditorView(QWidget):
    """Visual graph editor backed by the typed PipelineDocument model."""

    pipeline_changed = pyqtSignal(object)

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("pipelineEditorView")
        self.document = PipelineDocument(template("audio_spectrum_analyzer"))
        self._selected: list[str] = []
        self._input_signal: Signal | None = None
        self._tasks = TaskRunner(self)
        self._build_ui()
        self._refresh()

    def _build_ui(self) -> None:
        outer = QVBoxLayout(self)
        toolbar = QHBoxLayout()
        self.template_combo = QComboBox()
        self.template_combo.setAccessibleName("Pipeline template")
        self.template_combo.addItems(TEMPLATE_NAMES)
        load_template = QPushButton("Load template")
        load_template.setAccessibleName("Load pipeline template")
        load_template.clicked.connect(self._load_template)
        toolbar.addWidget(self.template_combo)
        toolbar.addWidget(load_template)
        for kind in ("input", "gain", "output"):
            button = QToolButton()
            button.setText(f"+ {kind.title()}")
            button.setAccessibleName(f"Add {kind} node")
            button.clicked.connect(lambda checked=False, value=kind: self._add_node(value))
            toolbar.addWidget(button)
        self.connect_button = QPushButton("Connect selected")
        self.connect_button.setAccessibleName("Connect selected pipeline nodes")
        self.connect_button.clicked.connect(self._connect_selected)
        toolbar.addWidget(self.connect_button)
        disconnect = QPushButton("Disconnect")
        disconnect.setAccessibleName("Disconnect selected pipeline nodes")
        disconnect.clicked.connect(self._disconnect_selected)
        toolbar.addWidget(disconnect)
        delete = QPushButton("Delete selected")
        delete.setAccessibleName("Delete selected pipeline node")
        delete.clicked.connect(self._delete_selected)
        toolbar.addWidget(delete)
        move_up = QPushButton("Move up")
        move_up.setAccessibleName("Move selected node up")
        move_up.clicked.connect(lambda: self._reorder_selected(-1))
        toolbar.addWidget(move_up)
        move_down = QPushButton("Move down")
        move_down.setAccessibleName("Move selected node down")
        move_down.clicked.connect(lambda: self._reorder_selected(1))
        toolbar.addWidget(move_down)
        undo = QPushButton("Undo")
        undo.setAccessibleName("Undo pipeline edit")
        undo.clicked.connect(self._undo)
        toolbar.addWidget(undo)
        redo = QPushButton("Redo")
        redo.setAccessibleName("Redo pipeline edit")
        redo.clicked.connect(self._redo)
        toolbar.addWidget(redo)
        save = QPushButton("Save JSON")
        save.setAccessibleName("Save pipeline JSON")
        save.clicked.connect(self._save_json)
        toolbar.addWidget(save)
        load = QPushButton("Open JSON")
        load.setAccessibleName("Open pipeline JSON")
        load.clicked.connect(self._load_json)
        toolbar.addWidget(load)
        outer.addLayout(toolbar)

        splitter = QSplitter(Qt.Orientation.Horizontal)
        self.scene = PipelineScene(self)
        self.scene.node_selected.connect(self._select_node)
        self.canvas = QGraphicsView(self.scene)
        self.canvas.setObjectName("pipelineCanvas")
        self.canvas.setAccessibleName("Visual pipeline graph")
        self.canvas.setSceneRect(0, 0, 1400, 700)
        splitter.addWidget(self.canvas)

        inspector = QWidget()
        inspector_layout = QVBoxLayout(inspector)
        inspector_layout.addWidget(QLabel("Node inspector"))
        self.selected_label = QLabel("Select a node")
        inspector_layout.addWidget(self.selected_label)
        form = QFormLayout()
        self.enabled = QComboBox()
        self.enabled.addItems(["enabled", "disabled"])
        self.enabled.currentTextChanged.connect(self._update_flags)
        form.addRow("State", self.enabled)
        self.bypass = QComboBox()
        self.bypass.addItems(["active", "bypass"])
        self.bypass.currentTextChanged.connect(self._update_flags)
        form.addRow("Processing", self.bypass)
        self.mute = QComboBox()
        self.mute.addItems(["audible", "mute"])
        self.mute.currentTextChanged.connect(self._update_flags)
        form.addRow("Output", self.mute)
        self.gain = QDoubleSpinBox()
        self.gain.setRange(-1000, 1000)
        self.gain.setValue(1.0)
        self.gain.valueChanged.connect(self._update_gain)
        form.addRow("Gain", self.gain)
        inspector_layout.addLayout(form)
        inspector_layout.addWidget(QLabel("Live node status"))
        self.status_table = QTableWidget(0, 4)
        self.status_table.setHorizontalHeaderLabels(["Node", "State", "Latency", "Error"])
        self.status_table.setAccessibleName("Pipeline node status")
        inspector_layout.addWidget(self.status_table)
        self.preview_label = QLabel("No intermediate preview")
        self.preview_label.setWordWrap(True)
        inspector_layout.addWidget(self.preview_label)
        inspector_layout.addStretch()
        splitter.addWidget(inspector)
        splitter.setSizes([760, 320])
        outer.addWidget(splitter)
        self._tasks.error.connect(self._show_error)

    def _refresh(self) -> None:
        self.scene.load_graph(self.document.graph)
        self._refresh_inspector()
        self.pipeline_changed.emit(self.document.graph)

    def _load_template(self) -> None:
        self.document = PipelineDocument(template(self.template_combo.currentText()))
        self._selected.clear()
        self._refresh()

    def _add_node(self, kind: str) -> None:
        node_id = f"{kind}_{len(self.document.graph.nodes)}"
        self.document.add_node(
            Node(
                node_id,
                kind,
                kind.title(),
                position=(80, 100 + 90 * len(self.document.graph.nodes)),
            )
        )
        self._refresh()

    def _select_node(self, node_id: str) -> None:
        if node_id in self._selected:
            self._selected.remove(node_id)
        else:
            self._selected = [*self._selected[-1:], node_id]
        self._refresh_inspector()

    def _connect_selected(self) -> None:
        if len(self._selected) != 2:
            self._show_error("Select a source and target node first")
            return
        try:
            self.document.connect(Edge(self._selected[0], "out", self._selected[1], "in"))
        except (ValueError, GraphValidationError) as error:
            self._show_error(str(error))
            return
        self._refresh()

    def _disconnect_selected(self) -> None:
        if len(self._selected) != 2:
            return
        edges = [
            edge
            for edge in self.document.graph.edges
            if edge.source_node == self._selected[0] and edge.target_node == self._selected[1]
        ]
        if edges:
            self.document.disconnect(edges[0])
            self._refresh()

    def _delete_selected(self) -> None:
        if len(self._selected) != 1:
            return
        try:
            self.document.remove_node(self._selected[0])
        except (KeyError, GraphValidationError) as error:
            self._show_error(str(error))
            return
        self._selected.clear()
        self._refresh()

    def _reorder_selected(self, delta: int) -> None:
        if len(self._selected) != 1:
            return
        keys = list(self.document.graph.nodes)
        index = keys.index(self._selected[0])
        self.document.reorder(self._selected[0], index + delta)
        self._refresh()

    def _update_flags(self) -> None:
        if len(self._selected) != 1 or self._selected[0] not in self.document.graph.nodes:
            return
        try:
            self.document.update_node(
                self._selected[0],
                enabled=self.enabled.currentText() == "enabled",
                bypass=self.bypass.currentText() == "bypass",
                mute=self.mute.currentText() == "mute",
            )
        except (ValueError, GraphValidationError):
            return
        self._refresh()

    def _update_gain(self, value: float) -> None:
        if len(self._selected) == 1 and self.document.graph.nodes[self._selected[0]].kind == "gain":
            self.document.update_node(self._selected[0], parameters={"gain": value})
            self._refresh()

    def _refresh_inspector(self) -> None:
        if len(self._selected) == 1 and self._selected[0] in self.document.graph.nodes:
            node = self.document.graph.nodes[self._selected[0]]
            self.selected_label.setText(f"{node.label or node.kind} ({node.node_id})")
            self.enabled.blockSignals(True)
            self.enabled.setCurrentText("enabled" if node.enabled else "disabled")
            self.enabled.blockSignals(False)
            self.bypass.blockSignals(True)
            self.bypass.setCurrentText("bypass" if node.bypass else "active")
            self.bypass.blockSignals(False)
            self.mute.blockSignals(True)
            self.mute.setCurrentText("mute" if node.mute else "audible")
            self.mute.blockSignals(False)
            self.gain.blockSignals(True)
            self.gain.setValue(float(node.parameters.get("gain", 1.0)))
            self.gain.blockSignals(False)
        else:
            self.selected_label.setText("Select a node")

    def _undo(self) -> None:
        if self.document.undo():
            self._refresh()

    def _redo(self) -> None:
        if self.document.redo():
            self._refresh()

    def _save_json(self) -> None:
        for node_id, item in self.scene.items_by_id.items():
            self.document.graph.nodes[node_id].position = (item.x(), item.y())
        path, _ = QFileDialog.getSaveFileName(
            self, "Save Pipeline JSON", "pipeline.json", "Pipeline JSON (*.json)"
        )
        if not path:
            return
        Path(path).write_text(json.dumps(self.document.graph.to_dict(), indent=2), encoding="utf-8")
        self.preview_label.setText(f"Pipeline saved: {Path(path).name}")

    def _load_json(self) -> None:
        path, _ = QFileDialog.getOpenFileName(
            self, "Open Pipeline JSON", "", "Pipeline JSON (*.json)"
        )
        if not path:
            return
        try:
            graph = PipelineGraph.from_dict(json.loads(Path(path).read_text(encoding="utf-8")))
        except (
            OSError,
            ValueError,
            TypeError,
            GraphValidationError,
            json.JSONDecodeError,
        ) as error:
            self._show_error(f"Unable to open pipeline: {error}")
            return
        self.document = PipelineDocument(graph)
        self._selected.clear()
        self._refresh()
        self.preview_label.setText(f"Pipeline opened: {Path(path).name}")

    def set_input_signal(self, signal: Signal | None) -> None:
        self._input_signal = signal
        if signal is None:
            self.preview_label.setText("No signal available for preview")
            return
        QTimer.singleShot(0, self._preview_signal)

    def _preview_signal(self) -> None:
        signal = self._input_signal
        if signal is None:
            return
        self._tasks.submit(
            lambda: self._execute_signal(signal),
            self._show_preview,
            self._show_error,
        )

    def _execute_signal(self, signal: Signal) -> GraphExecutor:
        chunk = signal_to_chunk(signal)
        executor = GraphExecutor(self.document.graph)
        executor.process(chunk)
        return executor

    def _show_preview(self, executor: GraphExecutor) -> None:
        statuses = executor.statuses
        self.status_table.setRowCount(len(statuses))
        for row, status in enumerate(statuses):
            self.status_table.setItem(row, 0, QTableWidgetItem(status.node_id))
            self.status_table.setItem(row, 1, QTableWidgetItem(status.state))
            self.status_table.setItem(
                row, 2, QTableWidgetItem(f"{status.latency_seconds * 1000:.2f} ms")
            )
            self.status_table.setItem(row, 3, QTableWidgetItem(status.error or ""))
        if len(self._selected) == 1:
            preview = executor.preview(self._selected[0])
            if preview is not None:
                self.preview_label.setText(
                    f"Preview {self._selected[0]}: {preview.samples.shape}, "
                    f"{preview.sampling_rate:g} Hz"
                )

    def _show_error(self, message: str) -> None:
        self.preview_label.setText(f"Error: {message}")


def signal_to_chunk(signal: Signal) -> Any:
    from signal_processing_toolkit.streaming.model import ChannelMetadata, StreamChunk

    return StreamChunk(
        signal.time_data,
        signal.sampling_rate,
        tuple(
            ChannelMetadata(name, unit)
            for name, unit in zip(signal.channel_names or (), signal.units, strict=True)
        ),
        0,
        signal.start_time,
        attributes={"source": "pipeline_editor"},
    )
