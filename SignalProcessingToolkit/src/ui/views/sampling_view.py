from __future__ import annotations

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QDoubleSpinBox,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QSlider,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)

from src.models.signal import Signal
from src.plots.time_domain import TimeDomainPlot
from src.ui.viewmodels.sampling_vm import SamplingViewModel


class SamplingView(QWidget):
    def __init__(self, viewmodel: SamplingViewModel, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("samplingView")
        self._vm = viewmodel
        self._setup_ui()
        self._bind()

    def _setup_ui(self) -> None:
        main_layout = QVBoxLayout(self)

        controls_group = QGroupBox("Sampling Controls")
        controls_layout = QFormLayout(controls_group)

        rate_layout = QHBoxLayout()
        self.rate_slider = QSlider(Qt.Orientation.Horizontal)
        self.rate_slider.setRange(100, 100000)
        self.rate_slider.setValue(44100)
        self.rate_label = QLabel("44100 Hz")
        self.rate_spin = QDoubleSpinBox()
        self.rate_spin.setRange(100.0, 100000.0)
        self.rate_spin.setValue(44100.0)
        self.rate_spin.setSuffix(" Hz")
        rate_layout.addWidget(self.rate_slider, stretch=1)
        rate_layout.addWidget(self.rate_spin)
        controls_layout.addRow("Target Rate:", rate_layout)

        downsample_layout = QHBoxLayout()
        self.ds_factor_spin = QSpinBox()
        self.ds_factor_spin.setRange(1, 100)
        self.ds_factor_spin.setValue(2)
        self.ds_btn = QPushButton("Downsample")
        downsample_layout.addWidget(self.ds_factor_spin)
        downsample_layout.addWidget(self.ds_btn)
        downsample_layout.addStretch()
        controls_layout.addRow("Downsample:", downsample_layout)

        upsample_layout = QHBoxLayout()
        self.us_factor_spin = QSpinBox()
        self.us_factor_spin.setRange(1, 100)
        self.us_factor_spin.setValue(2)
        self.us_btn = QPushButton("Upsample")
        upsample_layout.addWidget(self.us_factor_spin)
        upsample_layout.addWidget(self.us_btn)
        upsample_layout.addStretch()
        controls_layout.addRow("Upsample:", upsample_layout)

        button_layout = QHBoxLayout()
        self.resample_btn = QPushButton("Resample")
        self.resample_btn.setObjectName("primaryButton")
        self.reconstruct_btn = QPushButton("Reconstruct")
        self.aliasing_btn = QPushButton("Check Aliasing")
        button_layout.addWidget(self.resample_btn)
        button_layout.addWidget(self.reconstruct_btn)
        button_layout.addWidget(self.aliasing_btn)
        controls_layout.addRow("Actions:", button_layout)

        main_layout.addWidget(controls_group)

        plots_group = QGroupBox("Signal Comparison")
        plots_layout = QVBoxLayout(plots_group)
        self.original_plot = TimeDomainPlot()
        self.original_plot.plot_widget.setTitle("Original")
        self.sampled_plot = TimeDomainPlot()
        self.sampled_plot.plot_widget.setTitle("Sampled")
        plots_layout.addWidget(self.original_plot)
        plots_layout.addWidget(self.sampled_plot)
        main_layout.addWidget(plots_group, stretch=1)

        self.status_label = QLabel("")
        main_layout.addWidget(self.status_label)

    def _bind(self) -> None:
        self.rate_slider.valueChanged.connect(self._on_rate_slider)
        self.rate_spin.valueChanged.connect(self._on_rate_spin)
        self.resample_btn.clicked.connect(self._on_resample)
        self.reconstruct_btn.clicked.connect(self._on_reconstruct)
        self.ds_btn.clicked.connect(self._on_downsample)
        self.us_btn.clicked.connect(self._on_upsample)
        self.aliasing_btn.clicked.connect(self._on_aliasing)

    def set_input_signal(self, signal: Signal) -> None:
        self._vm.input_signal.value = signal
        self.original_plot.plot_signal(signal, name="Original")

    def _on_rate_slider(self, value: int) -> None:
        self.rate_spin.setValue(float(value))
        self.rate_label.setText(f"{value} Hz")
        self._vm.target_rate.value = float(value)

    def _on_rate_spin(self, value: float) -> None:
        self.rate_slider.setValue(int(value))
        self.rate_label.setText(f"{int(value)} Hz")
        self._vm.target_rate.value = value

    def _on_resample(self) -> None:
        result = self._vm.resample()
        if result is not None:
            self.sampled_plot.plot_signal(result, name="Sampled")

    def _on_reconstruct(self) -> None:
        result = self._vm.reconstruct()
        if result is not None:
            self.original_plot.clear()
            input_sig = self._vm.input_signal.value
            if input_sig is not None:
                self.original_plot.plot_signal(input_sig, name="Original")
            self.sampled_plot.clear()
            self.sampled_plot.plot(
                result.time_vector, result.time_data, name="Reconstructed", color="#4ec9b0"
            )
            self.sampled_plot.auto_range()

    def _on_downsample(self) -> None:
        self._vm.downsample_factor.value = self.ds_factor_spin.value()
        result = self._vm.downsample()
        if result is not None:
            self.sampled_plot.plot_signal(result, name="Downsampled")

    def _on_upsample(self) -> None:
        self._vm.upsample_factor.value = self.us_factor_spin.value()
        result = self._vm.upsample()
        if result is not None:
            self.sampled_plot.plot_signal(result, name="Upsampled")

    def _on_aliasing(self) -> None:
        result = self._vm.check_aliasing()
        if result is not None:
            aliased = self._vm.aliased_signal.value
            if aliased is not None:
                self.sampled_plot.clear()
                self.sampled_plot.plot_signal(aliased, name="Aliased Signal")
