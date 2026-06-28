from __future__ import annotations

from typing import Any

from PyQt6.QtWidgets import (
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QPushButton,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)

from src.plots.base import BasePlotWidget
from src.ui.viewmodels.correlation_vm import CorrelationViewModel


class CorrelationView(QWidget):
    def __init__(self, viewmodel: CorrelationViewModel, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("correlationView")
        self._vm = viewmodel
        self._setup_ui()
        self._bind()

    def _setup_ui(self) -> None:
        main_layout = QVBoxLayout(self)

        source_group = QGroupBox("Source Signals")
        source_layout = QFormLayout(source_group)
        self.signal_a_list = QListWidget()
        self.signal_a_list.setMaximumHeight(80)
        self.signal_b_list = QListWidget()
        self.signal_b_list.setMaximumHeight(80)
        source_layout.addRow("Signal A:", self.signal_a_list)
        source_layout.addRow("Signal B:", self.signal_b_list)
        main_layout.addWidget(source_group)

        config_group = QGroupBox("Configuration")
        config_layout = QFormLayout(config_group)
        self.max_lag_spin = QSpinBox()
        self.max_lag_spin.setRange(10, 10000)
        self.max_lag_spin.setValue(200)
        config_layout.addRow("Max Lag (samples):", self.max_lag_spin)
        main_layout.addWidget(config_group)

        button_layout = QHBoxLayout()
        self.auto_btn = QPushButton("Auto-Correlate")
        self.auto_btn.setObjectName("primaryButton")
        self.cross_btn = QPushButton("Cross-Correlate")
        button_layout.addWidget(self.auto_btn)
        button_layout.addWidget(self.cross_btn)
        button_layout.addStretch()
        main_layout.addLayout(button_layout)

        plot_group = QGroupBox("Correlation")
        plot_layout = QVBoxLayout(plot_group)
        self.corr_plot = BasePlotWidget(title="Correlation (lag domain)")
        self.corr_plot.set_labels(x_label="Lag (samples)", y_label="Correlation")
        plot_layout.addWidget(self.corr_plot)
        main_layout.addWidget(plot_group, stretch=1)

        self.result_label = QLabel("Peak lag: --")
        self.result_label.setObjectName("resultLabel")
        main_layout.addWidget(self.result_label)

        self.status_label = QLabel("")
        main_layout.addWidget(self.status_label)

    def _bind(self) -> None:
        self.auto_btn.clicked.connect(self._on_auto)
        self.cross_btn.clicked.connect(self._on_cross)

    def update_signal_list(self, signals: list) -> None:
        self.signal_a_list.clear()
        self.signal_b_list.clear()
        for s in signals:
            label = f"{s.metadata.name} ({s.metadata.id[:6]})"
            self.signal_a_list.addItem(label)
            self.signal_b_list.addItem(label)

    def _on_auto(self) -> None:
        self._vm.max_lag.value = self.max_lag_spin.value()
        result = self._vm.auto_correlate()
        self._display_result(result)

    def _on_cross(self) -> None:
        self._vm.max_lag.value = self.max_lag_spin.value()
        result = self._vm.cross_correlate()
        self._display_result(result)

    def _display_result(self, result: Any) -> None:
        if result is None:
            return
        self.corr_plot.clear()
        self.corr_plot.plot(result.lags, result.values, name="Correlation")  # type: ignore[attr-defined]
        self.corr_plot.auto_range()
        self.result_label.setText(
            f"Peak lag: {result.peak_lag} samples  |  Peak value: {result.peak_value:.4f}"
        )
