from __future__ import annotations

from PyQt6.QtWidgets import (
    QComboBox,
    QDoubleSpinBox,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QPushButton,
    QSpinBox,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

from src.models.signal import Signal
from src.plots.time_domain import TimeDomainPlot
from src.ui.viewmodels.signal_operations_vm import SignalOperationsViewModel


class SignalOperationsView(QWidget):
    def __init__(self, viewmodel: SignalOperationsViewModel, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("signalOperationsView")
        self._vm = viewmodel
        self._setup_ui()
        self._bind()

    def _setup_ui(self) -> None:
        main_layout = QVBoxLayout(self)

        source_group = QGroupBox("Source Signals")
        source_layout = QHBoxLayout(source_group)

        self.signal_a_list = QListWidget()
        self.signal_a_list.setMaximumHeight(120)
        self.signal_b_list = QListWidget()
        self.signal_b_list.setMaximumHeight(120)

        source_layout.addWidget(QLabel("Signal A:"))
        source_layout.addWidget(self.signal_a_list)
        source_layout.addWidget(QLabel("Signal B:"))
        source_layout.addWidget(self.signal_b_list)
        main_layout.addWidget(source_group)

        op_group = QGroupBox("Operation")
        op_layout = QFormLayout(op_group)

        self.op_combo = QComboBox()
        for o in self._vm.available_operations:
            self.op_combo.addItem(o.capitalize(), o)
        op_layout.addRow("Type:", self.op_combo)

        self.param_stack = QStackedWidget()
        self.param_stack.addWidget(self._make_none_widget())
        self.param_stack.addWidget(self._make_none_widget())
        self.param_stack.addWidget(self._make_none_widget())
        self.param_stack.addWidget(self._make_scale_widget())
        self.param_stack.addWidget(self._make_none_widget())
        self.param_stack.addWidget(self._make_shift_widget())
        self.param_stack.addWidget(self._make_none_widget())
        self.param_stack.addWidget(self._make_clip_widget())
        self.param_stack.addWidget(self._make_rectify_widget())
        self.param_stack.addWidget(self._make_mix_widget())
        op_layout.addRow("Params:", self.param_stack)
        main_layout.addWidget(op_group)

        preview_group = QGroupBox("Output Preview")
        preview_layout = QVBoxLayout(preview_group)
        self.plot = TimeDomainPlot()
        preview_layout.addWidget(self.plot)
        main_layout.addWidget(preview_group, stretch=1)

        button_layout = QHBoxLayout()
        self.execute_btn = QPushButton("Execute")
        self.execute_btn.setObjectName("primaryButton")
        self.undo_btn = QPushButton("Undo")
        self.redo_btn = QPushButton("Redo")
        button_layout.addStretch()
        button_layout.addWidget(self.undo_btn)
        button_layout.addWidget(self.redo_btn)
        button_layout.addWidget(self.execute_btn)
        main_layout.addLayout(button_layout)

        self.status_label = QLabel("")
        main_layout.addWidget(self.status_label)

    def _make_none_widget(self) -> QLabel:
        return QLabel("No additional parameters")

    def _make_scale_widget(self) -> QWidget:
        w = QWidget()
        layout = QHBoxLayout(w)
        layout.setContentsMargins(0, 0, 0, 0)
        self.scale_spin = QDoubleSpinBox()
        self.scale_spin.setRange(-100.0, 100.0)
        self.scale_spin.setValue(1.0)
        self.scale_spin.setSingleStep(0.1)
        layout.addWidget(QLabel("Factor:"))
        layout.addWidget(self.scale_spin)
        layout.addStretch()
        return w

    def _make_shift_widget(self) -> QWidget:
        w = QWidget()
        layout = QHBoxLayout(w)
        layout.setContentsMargins(0, 0, 0, 0)
        self.shift_spin = QSpinBox()
        self.shift_spin.setRange(-100000, 100000)
        self.shift_spin.setValue(0)
        layout.addWidget(QLabel("Samples:"))
        layout.addWidget(self.shift_spin)
        layout.addStretch()
        return w

    def _make_clip_widget(self) -> QWidget:
        w = QWidget()
        layout = QHBoxLayout(w)
        layout.setContentsMargins(0, 0, 0, 0)
        self.clip_min_spin = QDoubleSpinBox()
        self.clip_min_spin.setRange(-100.0, 100.0)
        self.clip_min_spin.setValue(-1.0)
        self.clip_max_spin = QDoubleSpinBox()
        self.clip_max_spin.setRange(-100.0, 100.0)
        self.clip_max_spin.setValue(1.0)
        layout.addWidget(QLabel("Min:"))
        layout.addWidget(self.clip_min_spin)
        layout.addWidget(QLabel("Max:"))
        layout.addWidget(self.clip_max_spin)
        layout.addStretch()
        return w

    def _make_rectify_widget(self) -> QWidget:
        w = QWidget()
        layout = QHBoxLayout(w)
        layout.setContentsMargins(0, 0, 0, 0)
        self.rect_combo = QComboBox()
        self.rect_combo.addItems(["full", "positive", "negative"])
        layout.addWidget(QLabel("Mode:"))
        layout.addWidget(self.rect_combo)
        layout.addStretch()
        return w

    def _make_mix_widget(self) -> QWidget:
        w = QWidget()
        layout = QHBoxLayout(w)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(QLabel("Mixes all active signals with equal weights"))
        layout.addStretch()
        return w

    def _bind(self) -> None:
        self.op_combo.currentIndexChanged.connect(self._on_op_changed)
        self.execute_btn.clicked.connect(self._on_execute)
        self.undo_btn.clicked.connect(self._on_undo)
        self.redo_btn.clicked.connect(self._on_redo)

    def update_signal_list(self, signals: list[Signal]) -> None:
        self.signal_a_list.clear()
        self.signal_b_list.clear()
        for s in signals:
            label = f"{s.metadata.name} ({s.metadata.id[:6]})"
            self.signal_a_list.addItem(label)
            self.signal_b_list.addItem(label)

    def _on_op_changed(self, index: int) -> None:
        self.param_stack.setCurrentIndex(index)
        self._vm.operation.value = self.op_combo.currentData()

    def _on_execute(self) -> None:
        signals = self._vm.active_signals.value
        sel_a = self.signal_a_list.currentRow()
        sel_b = self.signal_b_list.currentRow()

        if signals and 0 <= sel_a < len(signals):
            self._vm.input_a.value = signals[sel_a]
        if signals and 0 <= sel_b < len(signals):
            self._vm.input_b.value = signals[sel_b]

        self._sync_params()
        result = self._vm.execute()
        if result is not None:
            self.plot.clear()
            self.plot.plot(result.time_vector, result.time_data, name="Output")
            self.plot.auto_range()

    def _sync_params(self) -> None:
        self._vm.scale_factor.value = self.scale_spin.value()
        self._vm.shift_samples.value = self.shift_spin.value()
        self._vm.clip_min.value = self.clip_min_spin.value()
        self._vm.clip_max.value = self.clip_max_spin.value()
        self._vm.rectify_half.value = self.rect_combo.currentText()

    def _on_undo(self) -> None:
        result = self._vm.undo()
        if result is not None:
            self.plot.plot(result.time_vector, result.time_data, name="Output")
            self.plot.auto_range()

    def _on_redo(self) -> None:
        result = self._vm.redo()
        if result is not None:
            self.plot.plot(result.time_vector, result.time_data, name="Output")
            self.plot.auto_range()
