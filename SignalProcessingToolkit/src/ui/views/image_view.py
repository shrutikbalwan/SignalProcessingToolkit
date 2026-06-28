from __future__ import annotations

import numpy as np
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QImage, QPixmap
from PyQt6.QtWidgets import (
    QComboBox,
    QDoubleSpinBox,
    QFileDialog,
    QFormLayout,
    QGroupBox,
    QLabel,
    QPushButton,
    QSpinBox,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from src.models.image import ImageSignal
from src.plots.base import BasePlotWidget
from src.ui.viewmodels.image_vm import ImageViewModel


class ImageView(QWidget):
    def __init__(self, viewmodel: ImageViewModel, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("imageView")
        self._vm = viewmodel
        self._setup_ui()
        self._bind()

    def _setup_ui(self) -> None:
        main_layout = QVBoxLayout(self)

        self.load_btn = QPushButton("Load Image")
        self.load_btn.setObjectName("primaryButton")
        main_layout.addWidget(self.load_btn)

        tabs = QTabWidget()
        display_tab = QWidget()
        display_layout = QVBoxLayout(display_tab)
        self.image_label = QLabel("No image loaded")
        self.image_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.image_label.setMinimumSize(400, 300)
        self.image_label.setStyleSheet("background-color: #1e1e1e; border: 1px solid #3c3c3c;")
        display_layout.addWidget(self.image_label, stretch=1)
        tabs.addTab(display_tab, "Display")

        processed_tab = QWidget()
        processed_layout = QVBoxLayout(processed_tab)
        self.processed_label = QLabel("No processed image")
        self.processed_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.processed_label.setMinimumSize(400, 300)
        self.processed_label.setStyleSheet("background-color: #1e1e1e; border: 1px solid #3c3c3c;")
        processed_layout.addWidget(self.processed_label, stretch=1)
        tabs.addTab(processed_tab, "Processed")

        hist_tab = QWidget()
        hist_layout = QVBoxLayout(hist_tab)
        self.hist_plot = BasePlotWidget(title="Histogram")
        self.hist_plot.set_labels(x_label="Pixel Value", y_label="Count")
        hist_layout.addWidget(self.hist_plot)
        tabs.addTab(hist_tab, "Histogram")

        fft_tab = QWidget()
        fft_layout = QVBoxLayout(fft_tab)
        self.fft_plot = BasePlotWidget(title="2D FFT (Magnitude)")
        fft_layout.addWidget(self.fft_plot)
        tabs.addTab(fft_tab, "FFT Spectrum")

        fft_filt_tab = QWidget()
        fft_filt_layout = QVBoxLayout(fft_filt_tab)
        fft_form = QFormLayout()
        self.fft_cutoff_spin = QDoubleSpinBox()
        self.fft_cutoff_spin.setRange(0.01, 0.5)
        self.fft_cutoff_spin.setValue(0.3)
        self.fft_cutoff_spin.setSingleStep(0.05)
        self.fft_type_combo = QComboBox()
        self.fft_type_combo.addItems(["lowpass", "highpass"])
        self.fft_filter_btn = QPushButton("Apply FFT Filter")
        fft_form.addRow("Cutoff:", self.fft_cutoff_spin)
        fft_form.addRow("Type:", self.fft_type_combo)
        fft_form.addRow(self.fft_filter_btn)
        fft_filt_layout.addLayout(fft_form)
        self.fft_result_label = QLabel("")
        fft_filt_layout.addWidget(self.fft_result_label)
        tabs.addTab(fft_filt_tab, "FFT Filter")

        main_layout.addWidget(tabs, stretch=1)

        process_group = QGroupBox("Processing")
        process_layout = QFormLayout(process_group)

        self.edge_combo = QComboBox()
        self.edge_combo.addItems(["canny", "sobel", "laplacian"])
        self.edge_btn = QPushButton("Edge Detect")
        process_layout.addRow("Edge:", self.edge_combo)
        process_layout.addRow(self.edge_btn)

        self.blur_combo = QComboBox()
        self.blur_combo.addItems(["gaussian", "median", "bilateral", "average"])
        self.blur_kernel_spin = QSpinBox()
        self.blur_kernel_spin.setRange(3, 31)
        self.blur_kernel_spin.setValue(5)
        self.blur_kernel_spin.setSingleStep(2)
        self.blur_btn = QPushButton("Blur")
        process_layout.addRow("Blur:", self.blur_combo)
        process_layout.addRow("Kernel:", self.blur_kernel_spin)
        process_layout.addRow(self.blur_btn)

        self.sharpen_strength_spin = QDoubleSpinBox()
        self.sharpen_strength_spin.setRange(0.1, 5.0)
        self.sharpen_strength_spin.setValue(1.0)
        self.sharpen_btn = QPushButton("Sharpen")
        process_layout.addRow("Strength:", self.sharpen_strength_spin)
        process_layout.addRow(self.sharpen_btn)

        self.denoise_strength_spin = QSpinBox()
        self.denoise_strength_spin.setRange(1, 50)
        self.denoise_strength_spin.setValue(10)
        self.denoise_btn = QPushButton("Denoise")
        process_layout.addRow("Strength:", self.denoise_strength_spin)
        process_layout.addRow(self.denoise_btn)

        self.equalize_btn = QPushButton("Equalize Histogram")
        process_layout.addRow(self.equalize_btn)

        self.morph_combo = QComboBox()
        self.morph_combo.addItems(
            ["dilate", "erode", "open", "close", "gradient", "tophat", "blackhat"]
        )
        self.morph_kernel_spin = QSpinBox()
        self.morph_kernel_spin.setRange(1, 21)
        self.morph_kernel_spin.setValue(3)
        self.morph_btn = QPushButton("Apply")
        process_layout.addRow("Morph:", self.morph_combo)
        process_layout.addRow("Kernel:", self.morph_kernel_spin)
        process_layout.addRow(self.morph_btn)

        main_layout.addWidget(process_group)

        self.status_label = QLabel("")
        main_layout.addWidget(self.status_label)

    def _bind(self) -> None:
        self.load_btn.clicked.connect(self._on_load)
        self.edge_btn.clicked.connect(lambda: self._run("edge"))
        self.blur_btn.clicked.connect(lambda: self._run("blur"))
        self.sharpen_btn.clicked.connect(lambda: self._run("sharpen"))
        self.denoise_btn.clicked.connect(lambda: self._run("denoise"))
        self.equalize_btn.clicked.connect(lambda: self._run("equalize"))
        self.morph_btn.clicked.connect(lambda: self._run("morph"))
        self.fft_filter_btn.clicked.connect(lambda: self._run("fft_filter"))

    def _on_load(self) -> None:
        path, _ = QFileDialog.getOpenFileName(
            self, "Open Image", "", "Images (*.png *.jpg *.jpeg *.bmp *.tiff);;All Files (*)"
        )
        if path:
            from pathlib import Path

            img = self._vm.load_file(Path(path))
            if img is not None:
                self._display_image(img, self.image_label)
                self._update_histogram()
                self._update_fft()

    def _display_image(self, img: ImageSignal, label: QLabel) -> None:
        h, w = img.pixel_data.shape[:2]
        data_bytes = img.pixel_data.tobytes()
        if img.is_color:
            qimg = QImage(data_bytes, w, h, w * 3, QImage.Format.Format_RGB888)
        else:
            qimg = QImage(data_bytes, w, h, w, QImage.Format.Format_Grayscale8)
        pixmap = QPixmap.fromImage(qimg)
        label.setPixmap(
            pixmap.scaled(
                400,
                300,
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation,
            )
        )

    def _update_histogram(self) -> None:
        hist = self._vm.histogram.value
        if hist is not None:
            self.hist_plot.clear()
            x = np.arange(256)
            if hist.ndim == 1:
                self.hist_plot.plot(x, hist, name="Grayscale")
            else:
                colors = ["#569cd6", "#4ec9b0", "#ce9178"]
                for ch in range(min(hist.shape[0], 3)):
                    self.hist_plot.plot(x, hist[ch], name=f"Ch{ch}", color=colors[ch])
            self.hist_plot.auto_range()

    def _update_fft(self) -> None:
        fft = self._vm.fft_result.value
        if fft is not None:
            self.fft_plot.clear()
            h, w = fft.magnitude_db.shape
            self.fft_plot.plot(np.arange(w), fft.magnitude_db[h // 2, :], name="Center row")
            self.fft_plot.auto_range()

    def _run(self, action: str) -> None:
        result = None
        if action == "edge":
            result = self._vm.edge_detect(self.edge_combo.currentText())
        elif action == "blur":
            result = self._vm.blur(self.blur_kernel_spin.value(), self.blur_combo.currentText())
        elif action == "sharpen":
            result = self._vm.sharpen(self.sharpen_strength_spin.value())
        elif action == "denoise":
            result = self._vm.denoise(self.denoise_strength_spin.value())
        elif action == "equalize":
            result = self._vm.equalize()
        elif action == "morph":
            result = self._vm.morph(self.morph_combo.currentText(), self.morph_kernel_spin.value())
        elif action == "fft_filter":
            result = self._vm.fft_filter(
                self.fft_cutoff_spin.value(), self.fft_type_combo.currentText()
            )
        if result is not None:
            self._display_image(result, self.processed_label)
