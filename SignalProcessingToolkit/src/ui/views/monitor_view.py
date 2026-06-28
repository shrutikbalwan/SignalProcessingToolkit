from __future__ import annotations

import numpy as np
from PyQt6.QtCore import QTimer
from PyQt6.QtWidgets import (
    QComboBox,
    QDoubleSpinBox,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from src.dsp.generators import create_generator
from src.plots.base import BasePlotWidget


class LiveMonitorView(QWidget):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._timer = QTimer(self)
        self._timer.setInterval(200)

        layout = QVBoxLayout(self)

        controls = QHBoxLayout()
        controls.addWidget(QLabel("Type:"))
        self.wave_combo = QComboBox()
        self.wave_combo.addItems(["sine", "square", "sawtooth", "noise"])
        controls.addWidget(self.wave_combo)

        controls.addWidget(QLabel("Freq (Hz):"))
        self.freq_spin = QDoubleSpinBox()
        self.freq_spin.setRange(1, 20000)
        self.freq_spin.setValue(440)
        controls.addWidget(self.freq_spin)

        self.toggle_btn = QPushButton("Start")
        self.toggle_btn.clicked.connect(self._toggle)
        controls.addWidget(self.toggle_btn)

        layout.addLayout(controls)

        self.plot = BasePlotWidget(self)
        self.plot.set_labels(x_label="Sample", y_label="Amplitude")
        layout.addWidget(self.plot)

        self._running = False
        self._sample = 0

    def _toggle(self) -> None:
        if self._running:
            self._timer.stop()
            self.toggle_btn.setText("Start")
            self._running = False
        else:
            self._timer.timeout.connect(self._update)
            self._timer.start()
            self.toggle_btn.setText("Stop")
            self._running = True

    def _update(self) -> None:
        wave_type = self.wave_combo.currentText()
        freq = self.freq_spin.value()
        try:
            from src.models.enums import WaveformType

            gen = create_generator(WaveformType(wave_type))
            sig = gen.generate(sampling_rate=44100, duration=0.2, frequency=freq)
            self._sample += len(sig.time_data)
            n = len(sig.time_data[:500])
            self.plot.plot(np.arange(n), sig.time_data[:500], name="Monitor")
        except Exception:
            import logging
            logging.getLogger(__name__).exception("Live monitor error")

    def stop(self) -> None:
        self._timer.stop()
        self._running = False
        self.toggle_btn.setText("Start")
