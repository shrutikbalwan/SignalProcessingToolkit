from __future__ import annotations

from PyQt6.QtWidgets import (
    QComboBox,
    QDoubleSpinBox,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QScrollArea,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)

from src.ui.components.plots.time_domain import TimeDomainPlot


class GraphArea(QWidget):
    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setObjectName("graphArea")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        title = QLabel("Real-time Signal Visualization")
        title.setObjectName("sectionTitle")
        title.setStyleSheet("font-size: 18px; font-weight: bold; padding: 10px;")
        layout.addWidget(title)

        self.plot = TimeDomainPlot()
        layout.addWidget(self.plot, stretch=1)

        info_bar = self._create_info_bar()
        layout.addWidget(info_bar)

    def _create_info_bar(self) -> QWidget:
        bar = QWidget()
        bar.setObjectName("infoBar")
        layout = QHBoxLayout(bar)
        layout.setContentsMargins(15, 10, 15, 10)

        self.frequency_label = QLabel("Frequency: 440 Hz")
        self.amplitude_label = QLabel("Amplitude: 0.8")
        self.duration_label = QLabel("Duration: 2.0 s")
        self.points_label = QLabel("Samples: 88200")

        layout.addWidget(self.frequency_label)
        layout.addWidget(self.amplitude_label)
        layout.addWidget(self.duration_label)
        layout.addWidget(self.points_label)
        layout.addStretch()

        self.update_button = QPushButton("Update Plot")
        self.update_button.clicked.connect(self._on_update_plot)
        self.update_button.setObjectName("primaryButton")
        layout.addWidget(self.update_button)

        return bar

    def _on_update_plot(self) -> None:
        pass

    def update_info_labels(self, signal=None) -> None:
        if signal:
            self.frequency_label.setText(f"Frequency: {signal.frequency} Hz")
            self.amplitude_label.setText(f"Amplitude: {signal.amplitude:.2f}")
            self.duration_label.setText(f"Duration: {signal.duration:.2f} s")
            self.points_label.setText(f"Samples: {len(signal.time_data)}")

    def update_plot(self, signal=None) -> None:
        if signal:
            self.plot.clear()
            self.plot.plot(signal.time_data, signal.time_data, name="Signal")
            self.plot.auto_range()
            self.plot.set_title(
                f"Signal: {signal.metadata.name if signal.metadata else 'Untitled'}"
            )


class ParameterPanel(QWidget):
    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setObjectName("parameterPanel")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        title = QLabel("Signal Parameters")
        title.setObjectName("sectionTitle")
        title.setStyleSheet("font-size: 18px; font-weight: bold; padding: 15px 15px 5px 15px;")
        layout.addWidget(title)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll_content = QWidget()
        scroll_layout = QVBoxLayout(scroll_content)
        scroll_layout.setContentsMargins(15, 5, 15, 15)

        self._add_basic_group(scroll_layout)
        self._add_advanced_group(scroll_layout)
        self._add_preset_group(scroll_layout)

        scroll.setWidget(scroll_content)
        layout.addWidget(scroll)

    def _add_basic_group(self, parent_layout: QVBoxLayout) -> None:
        group = QGroupBox("Basic Parameters")
        form_layout = QFormLayout(group)

        self.type_combo = QComboBox()
        self.type_combo.addItems(["Sine", "Cosine", "Square", "Triangle", "Impulse"])
        form_layout.addRow("Type:", self.type_combo)

        self.frequency_spin = QDoubleSpinBox()
        self.frequency_spin.setRange(1.0, 10000.0)
        self.frequency_spin.setValue(440.0)
        self.frequency_spin.setSingleStep(1.0)
        form_layout.addRow("Frequency (Hz):", self.frequency_spin)

        self.amplitude_spin = QDoubleSpinBox()
        self.amplitude_spin.setRange(0.1, 10.0)
        self.amplitude_spin.setValue(1.0)
        self.amplitude_spin.setSingleStep(0.1)
        form_layout.addRow("Amplitude:", self.amplitude_spin)

        self.phase_spin = QDoubleSpinBox()
        self.phase_spin.setRange(0.0, 360.0)
        self.phase_spin.setValue(0.0)
        self.phase_spin.setSingleStep(1.0)
        form_layout.addRow("Phase (°):", self.phase_spin)

        self.duration_spin = QDoubleSpinBox()
        self.duration_spin.setRange(0.1, 10.0)
        self.duration_spin.setValue(1.0)
        self.duration_spin.setSingleStep(0.1)
        form_layout.addRow("Duration (s):", self.duration_spin)

        parent_layout.addWidget(group)

    def _add_advanced_group(self, parent_layout: QVBoxLayout) -> None:
        group = QGroupBox("Advanced Parameters")
        form_layout = QFormLayout(group)

        self.sampling_rate_spin = QSpinBox()
        self.sampling_rate_spin.setRange(1000, 192000)
        self.sampling_rate_spin.setValue(44100)
        form_layout.addRow("Sampling Rate (Hz):", self.sampling_rate_spin)

        self.phase_offset_spin = QSpinBox()
        self.phase_offset_spin.setRange(-180, 180)
        self.phase_offset_spin.setValue(0)
        form_layout.addRow("Phase Offset (°):", self.phase_offset_spin)

        self.noise_level_spin = QDoubleSpinBox()
        self.noise_level_spin.setRange(0.0, 1.0)
        self.noise_level_spin.setValue(0.0)
        self.noise_level_spin.setSingleStep(0.01)
        form_layout.addRow("Noise Level:", self.noise_level_spin)

        self.bias_spin = QDoubleSpinBox()
        self.bias_spin.setRange(-5.0, 5.0)
        self.bias_spin.setValue(0.0)
        self.bias_spin.setSingleStep(0.1)
        form_layout.addRow("DC Offset:", self.bias_spin)

        parent_layout.addWidget(group)

    def _add_preset_group(self, parent_layout: QVBoxLayout) -> None:
        group = QGroupBox("Presets")
        layout = QHBoxLayout(group)

        presets = [
            ("Sine 440Hz", {"type": "sine", "frequency": 440, "amplitude": 1.0, "phase": 0}),
            ("Cosine 1000Hz", {"type": "cosine", "frequency": 1000, "amplitude": 0.8, "phase": 0}),
            ("Square 220Hz", {"type": "square", "frequency": 220, "amplitude": 1.0, "phase": 0}),
            (
                "Triangle 440Hz",
                {"type": "triangle", "frequency": 440, "amplitude": 0.7, "phase": 0},
            ),
        ]

        for name, _ in presets:
            btn = QPushButton(name)
            btn.setObjectName("secondaryButton")
            btn.clicked.connect(lambda checked, p=name: self._load_preset(p))
            layout.addWidget(btn)

        layout.addStretch()
        parent_layout.addWidget(group)

    def _load_preset(self, name: str) -> None:
        pass

    def get_parameters(self) -> dict:
        return {
            "type": self.type_combo.currentText().lower(),
            "frequency": self.frequency_spin.value(),
            "amplitude": self.amplitude_spin.value(),
            "phase": self.phase_spin.value(),
            "duration": self.duration_spin.value(),
            "sampling_rate": self.sampling_rate_spin.value(),
            "phase_offset": self.phase_offset_spin.value(),
            "noise_level": self.noise_level_spin.value(),
            "bias": self.bias_spin.value(),
        }

    def set_parameters(self, params: dict) -> None:
        if "type" in params:
            index = self.type_combo.findText(params["type"].title())
            if index >= 0:
                self.type_combo.setCurrentIndex(index)
        if "frequency" in params:
            self.frequency_spin.setValue(params["frequency"])
        if "amplitude" in params:
            self.amplitude_spin.setValue(params["amplitude"])
        if "phase" in params:
            self.phase_spin.setValue(params["phase"])
        if "duration" in params:
            self.duration_spin.setValue(params["duration"])
        if "sampling_rate" in params:
            self.sampling_rate_spin.setValue(params["sampling_rate"])
        if "phase_offset" in params:
            self.phase_offset_spin.setValue(params["phase_offset"])
        if "noise_level" in params:
            self.noise_level_spin.setValue(params["noise_level"])
        if "bias" in params:
            self.bias_spin.setValue(params["bias"])


class MetricCard(QWidget):
    def __init__(
        self,
        title: str,
        value: str,
        unit: str = "",
        icon: str = "",
        color: str = "#0078d4",
        parent=None,
    ) -> None:
        super().__init__(parent)
        self.setObjectName("metricCard")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(15, 15, 15, 15)

        header = QHBoxLayout()

        icon_label = QLabel(icon)
        icon_label.setObjectName("cardIcon")
        header.addWidget(icon_label)

        title_label = QLabel(title)
        title_label.setObjectName("cardTitle")
        header.addWidget(title_label)
        header.addStretch()

        layout.addLayout(header)

        value_container = QHBoxLayout()
        self.value_label = QLabel(value)
        self.value_label.setObjectName("cardValue")
        self.value_label.setStyleSheet(f"color: {color};")
        value_container.addWidget(self.value_label)

        if unit:
            unit_label = QLabel(unit)
            unit_label.setObjectName("cardUnit")
            value_container.addWidget(unit_label)

        layout.addLayout(value_container)

    def set_value(self, value: str) -> None:
        self.value_label.setText(value)

    def update_value(self, value: float, unit: str = "") -> None:
        self.value_label.setText(f"{value:.2f}{unit}")


class SignalCard(QWidget):
    def __init__(
        self,
        title: str,
        signal_name: str,
        metadata: str = "",
        parent=None,
    ) -> None:
        super().__init__(parent)
        self.setObjectName("signalCard")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(15, 15, 15, 15)

        title_label = QLabel(title)
        title_label.setObjectName("cardTitle")
        layout.addWidget(title_label)

        self.name_label = QLabel(signal_name)
        self.name_label.setObjectName("cardSubtitle")
        self.name_label.setStyleSheet("font-size: 14px; color: #0078d4;")
        layout.addWidget(self.name_label)

        if metadata:
            meta_label = QLabel(metadata)
            meta_label.setObjectName("cardMetadata")
            meta_label.setStyleSheet("font-size: 12px; opacity: 0.7;")
            layout.addWidget(meta_label)

        self.plot_preview = TimeDomainPlot()
        self.plot_preview.setMaximumHeight(80)
        layout.addWidget(self.plot_preview)

        footer = QHBoxLayout()
        footer.addStretch()

        self.view_btn = QPushButton("View Details")
        self.view_btn.setObjectName("secondaryButton")
        footer.addWidget(self.view_btn)

        layout.addLayout(footer)

    def set_signal(self, signal) -> None:
        pass


class PlotCard(QWidget):
    def __init__(
        self,
        title: str,
        plot_widget=None,
        parent=None,
    ) -> None:
        super().__init__(parent)
        self.setObjectName("plotCard")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(15, 15, 15, 15)

        title_label = QLabel(title)
        title_label.setObjectName("cardTitle")
        layout.addWidget(title_label)

        if plot_widget:
            layout.addWidget(plot_widget)

    def update_plot(self, signal) -> None:
        pass
