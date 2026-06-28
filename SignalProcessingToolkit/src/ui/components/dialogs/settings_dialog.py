from __future__ import annotations

from PyQt6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QDoubleSpinBox,
    QFormLayout,
    QGroupBox,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)

from src.config import settings


class SettingsDialog(QDialog):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Settings")
        self.setMinimumWidth(500)
        self._setup_ui()
        self._load_settings()

    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)

        ui_group = QGroupBox("User Interface")
        ui_layout = QFormLayout(ui_group)
        self.theme_combo = QComboBox()
        self.theme_combo.addItems(["dark", "light"])
        ui_layout.addRow("Theme:", self.theme_combo)
        layout.addWidget(ui_group)

        dsp_group = QGroupBox("DSP Defaults")
        dsp_layout = QFormLayout(dsp_group)
        self.sr_spin = QDoubleSpinBox()
        self.sr_spin.setRange(100.0, 1000000.0)
        self.sr_spin.setValue(44100.0)
        self.sr_spin.setSuffix(" Hz")
        dsp_layout.addRow("Sampling Rate:", self.sr_spin)

        self.dur_spin = QDoubleSpinBox()
        self.dur_spin.setRange(0.01, 60.0)
        self.dur_spin.setValue(1.0)
        self.dur_spin.setSuffix(" s")
        dsp_layout.addRow("Duration:", self.dur_spin)

        self.fft_spin = QSpinBox()
        self.fft_spin.setRange(64, 65536)
        self.fft_spin.setValue(4096)
        dsp_layout.addRow("FFT Size:", self.fft_spin)
        layout.addWidget(dsp_group)

        file_group = QGroupBox("File Management")
        file_layout = QFormLayout(file_group)
        self.autosave_check = QCheckBox("Enable autosave")
        self.autosave_check.setChecked(True)
        file_layout.addRow(self.autosave_check)

        self.auto_interval_spin = QSpinBox()
        self.auto_interval_spin.setRange(30, 3600)
        self.auto_interval_spin.setValue(300)
        self.auto_interval_spin.setSuffix(" s")
        file_layout.addRow("Autosave Interval:", self.auto_interval_spin)

        self.recent_spin = QSpinBox()
        self.recent_spin.setRange(1, 50)
        self.recent_spin.setValue(10)
        file_layout.addRow("Recent Files:", self.recent_spin)
        layout.addWidget(file_group)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def _load_settings(self) -> None:
        self.theme_combo.setCurrentText(settings.theme)
        self.sr_spin.setValue(settings.default_sampling_rate)
        self.dur_spin.setValue(settings.default_duration)
        self.fft_spin.setValue(settings.fft_size)
        self.autosave_check.setChecked(settings.autosave_enabled)
        self.auto_interval_spin.setValue(settings.auto_save_interval)
        self.recent_spin.setValue(settings.recent_files_max)

    def get_settings(self) -> dict:
        return {
            "theme": self.theme_combo.currentText(),
            "default_sampling_rate": self.sr_spin.value(),
            "default_duration": self.dur_spin.value(),
            "fft_size": self.fft_spin.value(),
            "autosave_enabled": self.autosave_check.isChecked(),
            "auto_save_interval": self.auto_interval_spin.value(),
            "recent_files_max": self.recent_spin.value(),
        }
