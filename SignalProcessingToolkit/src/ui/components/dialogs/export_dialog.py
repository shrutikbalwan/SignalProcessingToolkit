from __future__ import annotations

from pathlib import Path

from PyQt6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFileDialog,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QSpinBox,
    QVBoxLayout,
)


class ExportDialog(QDialog):
    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Export Signal")
        self.setMinimumWidth(400)
        self._selected_path: Path | None = None
        self._setup_ui()

    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)

        format_group = QGroupBox("Export Format")
        format_layout = QFormLayout(format_group)
        self.format_combo = QComboBox()
        self.format_combo.addItems(
            ["CSV (.csv)", "Excel (.xlsx)", "Text (.txt)", "WAV (.wav)", "NumPy (.npz)"]
        )
        format_layout.addRow("Format:", self.format_combo)
        layout.addWidget(format_group)

        options_group = QGroupBox("Options")
        options_layout = QFormLayout(options_group)
        self.metadata_check = QCheckBox("Include metadata")
        self.metadata_check.setChecked(True)
        self.precision_spin = QSpinBox()
        self.precision_spin.setRange(1, 15)
        self.precision_spin.setValue(6)
        options_layout.addRow("Precision:", self.precision_spin)
        options_layout.addRow(self.metadata_check)
        layout.addWidget(options_group)

        self.path_label = QLabel("No file selected")
        self.browse_btn = QPushButton("Browse...")
        path_layout = QHBoxLayout()
        path_layout.addWidget(self.path_label, stretch=1)
        path_layout.addWidget(self.browse_btn)
        layout.addLayout(path_layout)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

        self.browse_btn.clicked.connect(self._on_browse)

    def _on_browse(self) -> None:
        fmt = self.format_combo.currentText().split(" ")[0].lower()
        ext_map = {"csv": ".csv", "excel": ".xlsx", "text": ".txt", "wav": ".wav", "numpy": ".npz"}
        ext = ext_map.get(fmt, ".csv")
        path, _ = QFileDialog.getSaveFileName(self, "Export Signal", "", f"*{ext}")
        if path:
            self._selected_path = Path(path)
            self.path_label.setText(path)

    @property
    def selected_path(self) -> Path | None:
        return self._selected_path

    @property
    def selected_format(self) -> str:
        return self.format_combo.currentText().split(" ")[0].lower()

    @property
    def include_metadata(self) -> bool:
        return self.metadata_check.isChecked()

    @property
    def precision(self) -> int:
        return self.precision_spin.value()
