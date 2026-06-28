from __future__ import annotations

from PyQt6.QtWidgets import (
    QComboBox,
    QFormLayout,
    QGroupBox,
    QLabel,
    QListWidget,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from src.plots.time_domain import TimeDomainPlot
from src.ui.viewmodels.convolution_vm import ConvolutionViewModel


class ConvolutionView(QWidget):
    def __init__(self, viewmodel: ConvolutionViewModel, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("convolutionView")
        self._vm = viewmodel
        self._setup_ui()
        self._bind()

    def _setup_ui(self) -> None:
        main_layout = QVBoxLayout(self)

        source_group = QGroupBox("Source Signals")
        source_layout = QFormLayout(source_group)
        self.signal_list = QListWidget()
        self.signal_list.setMaximumHeight(80)
        self.kernel_list = QListWidget()
        self.kernel_list.setMaximumHeight(80)
        source_layout.addRow("Input Signal:", self.signal_list)
        source_layout.addRow("Kernel:", self.kernel_list)
        main_layout.addWidget(source_group)

        config_group = QGroupBox("Configuration")
        config_layout = QFormLayout(config_group)
        self.mode_combo = QComboBox()
        self.mode_combo.addItems(["linear", "circular", "same", "valid"])
        config_layout.addRow("Mode:", self.mode_combo)
        main_layout.addWidget(config_group)

        self.execute_btn = QPushButton("Convolve")
        self.execute_btn.setObjectName("primaryButton")
        main_layout.addWidget(self.execute_btn)

        preview_group = QGroupBox("Preview")
        preview_layout = QVBoxLayout(preview_group)
        self.input_plot = TimeDomainPlot()
        self.input_plot.plot_widget.setTitle("Input")
        self.kernel_plot = TimeDomainPlot()
        self.kernel_plot.plot_widget.setTitle("Kernel / Impulse Response")
        self.output_plot = TimeDomainPlot()
        self.output_plot.plot_widget.setTitle("Output")
        preview_layout.addWidget(self.input_plot)
        preview_layout.addWidget(self.kernel_plot)
        preview_layout.addWidget(self.output_plot)
        main_layout.addWidget(preview_group, stretch=1)

        self.status_label = QLabel("")
        main_layout.addWidget(self.status_label)

    def _bind(self) -> None:
        self.mode_combo.currentTextChanged.connect(self._vm.mode.__setattr__)
        self.execute_btn.clicked.connect(self._on_execute)

    def update_signal_list(self, signals: list) -> None:
        self.signal_list.clear()
        self.kernel_list.clear()
        for s in signals:
            label = f"{s.metadata.name} ({s.metadata.id[:6]})"
            self.signal_list.addItem(label)
            self.kernel_list.addItem(label)

    def _on_execute(self) -> None:
        result = self._vm.execute()
        if result is not None:
            self.output_plot.clear()
            self.output_plot.plot(result.time_vector, result.time_data, name="Output")
            self.output_plot.auto_range()
