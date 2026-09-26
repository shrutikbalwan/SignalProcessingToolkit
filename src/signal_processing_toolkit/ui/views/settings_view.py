"""Persistent application settings page."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from PyQt6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDoubleSpinBox,
    QFormLayout,
    QGroupBox,
    QLabel,
    QPushButton,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)

from signal_processing_toolkit.core.settings import SettingsManager


class SettingsView(QWidget):
    def __init__(
        self,
        manager: SettingsManager,
        on_save: Callable[[dict[str, Any]], None],
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self.setObjectName("settingsView")
        self._manager = manager
        self._on_save = on_save
        layout = QVBoxLayout(self)

        title = QLabel("Settings")
        title.setObjectName("sectionTitle")
        layout.addWidget(title)

        ui_group = QGroupBox("User interface")
        ui_layout = QFormLayout(ui_group)
        self.theme_combo = QComboBox()
        self.theme_combo.addItems(["dark", "light"])
        self.theme_combo.setAccessibleName("Application theme")
        ui_layout.addRow("&Theme:", self.theme_combo)
        layout.addWidget(ui_group)

        dsp_group = QGroupBox("DSP defaults")
        dsp_layout = QFormLayout(dsp_group)
        self.sampling_rate_spin = QDoubleSpinBox()
        self.sampling_rate_spin.setRange(100.0, 1_000_000.0)
        self.sampling_rate_spin.setSuffix(" Hz")
        self.sampling_rate_spin.setAccessibleName("Default sampling rate")
        dsp_layout.addRow("&Sampling rate:", self.sampling_rate_spin)
        self.duration_spin = QDoubleSpinBox()
        self.duration_spin.setRange(0.001, 60.0)
        self.duration_spin.setSuffix(" s")
        self.duration_spin.setAccessibleName("Default signal duration")
        dsp_layout.addRow("&Duration:", self.duration_spin)
        self.fft_size_spin = QSpinBox()
        self.fft_size_spin.setRange(64, 65_536)
        self.fft_size_spin.setAccessibleName("Default FFT size")
        dsp_layout.addRow("&FFT size:", self.fft_size_spin)
        layout.addWidget(dsp_group)

        files_group = QGroupBox("File management")
        files_layout = QFormLayout(files_group)
        self.autosave_check = QCheckBox("Enable &autosave")
        self.autosave_check.setAccessibleName("Enable autosave")
        files_layout.addRow(self.autosave_check)
        self.autosave_interval_spin = QSpinBox()
        self.autosave_interval_spin.setRange(30, 3600)
        self.autosave_interval_spin.setSuffix(" s")
        self.autosave_interval_spin.setAccessibleName("Autosave interval")
        files_layout.addRow("Autosave &interval:", self.autosave_interval_spin)
        layout.addWidget(files_group)

        self.save_button = QPushButton("&Save settings")
        self.save_button.setObjectName("primaryButton")
        self.save_button.setAccessibleName("Save settings")
        self.save_button.clicked.connect(self._save)
        layout.addWidget(self.save_button)
        self.status_label = QLabel("")
        self.status_label.setAccessibleName("Settings status")
        layout.addWidget(self.status_label)
        layout.addStretch()
        self.reload()

    def reload(self) -> None:
        self.theme_combo.setCurrentText(self._manager.theme)
        self.sampling_rate_spin.setValue(float(self._manager.get("default_sampling_rate", 44100)))
        self.duration_spin.setValue(float(self._manager.get("default_duration", 1.0)))
        self.fft_size_spin.setValue(int(self._manager.get("fft_size", 4096)))
        self.autosave_check.setChecked(bool(self._manager.get("autosave_enabled", True)))
        self.autosave_interval_spin.setValue(int(self._manager.get("auto_save_interval", 300)))

    def values(self) -> dict[str, Any]:
        return {
            "theme": self.theme_combo.currentText(),
            "default_sampling_rate": self.sampling_rate_spin.value(),
            "default_duration": self.duration_spin.value(),
            "fft_size": self.fft_size_spin.value(),
            "autosave_enabled": self.autosave_check.isChecked(),
            "auto_save_interval": self.autosave_interval_spin.value(),
        }

    def _save(self, _checked: bool = False) -> None:
        values = self.values()
        try:
            self._on_save(values)
        except Exception as exc:
            self.status_label.setText(f"Error: {exc}")
            return
        self.status_label.setText("Settings saved")
