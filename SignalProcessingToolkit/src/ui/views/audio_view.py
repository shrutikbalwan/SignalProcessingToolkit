from __future__ import annotations

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QFileDialog,
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QSlider,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from src.models.audio import AudioSignal
from src.plots.frequency_domain import FrequencyDomainPlot
from src.plots.spectrogram import SpectrogramPlot
from src.plots.time_domain import TimeDomainPlot
from src.ui.viewmodels.audio_vm import EQ_BANDS, AudioViewModel


class AudioView(QWidget):
    def __init__(self, viewmodel: AudioViewModel, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("audioView")
        self._vm = viewmodel
        self._setup_ui()
        self._bind()

    def _setup_ui(self) -> None:
        main_layout = QVBoxLayout(self)

        transport_group = QGroupBox("Transport")
        transport_layout = QHBoxLayout(transport_group)
        self.load_btn = QPushButton("Load Audio")
        self.play_btn = QPushButton("Play")
        self.play_btn.setObjectName("primaryButton")
        self.stop_btn = QPushButton("Stop")
        self.vol_slider = QSlider(Qt.Orientation.Horizontal)
        self.vol_slider.setRange(0, 200)
        self.vol_slider.setValue(100)
        self.vol_label = QLabel("100%")
        transport_layout.addWidget(self.load_btn)
        transport_layout.addWidget(self.play_btn)
        transport_layout.addWidget(self.stop_btn)
        transport_layout.addWidget(QLabel("Vol:"))
        transport_layout.addWidget(self.vol_slider, stretch=1)
        transport_layout.addWidget(self.vol_label)
        main_layout.addWidget(transport_group)

        eq_group = QGroupBox("10-Band Equalizer")
        eq_layout = QHBoxLayout(eq_group)
        self.eq_sliders: list[QSlider] = []
        for _i, band in enumerate(EQ_BANDS):
            col = QVBoxLayout()
            label = QLabel(f"{band}")
            label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            slider = QSlider(Qt.Orientation.Vertical)
            slider.setRange(-24, 24)
            slider.setValue(0)
            slider.setTickPosition(QSlider.TickPosition.TicksRight)
            col.addWidget(slider, alignment=Qt.AlignmentFlag.AlignCenter)
            col.addWidget(label, alignment=Qt.AlignmentFlag.AlignCenter)
            eq_layout.addLayout(col)
            self.eq_sliders.append(slider)
        self.apply_eq_btn = QPushButton("Apply EQ")
        eq_layout.addWidget(self.apply_eq_btn)
        main_layout.addWidget(eq_group)

        tabs = QTabWidget()
        wave_tab = QWidget()
        wave_layout = QVBoxLayout(wave_tab)
        self.wave_plot = TimeDomainPlot()
        wave_layout.addWidget(self.wave_plot)
        tabs.addTab(wave_tab, "Waveform")

        spec_tab = QWidget()
        spec_layout = QVBoxLayout(spec_tab)
        self.freq_plot = FrequencyDomainPlot()
        spec_layout.addWidget(self.freq_plot)
        tabs.addTab(spec_tab, "Spectrum")

        specgram_tab = QWidget()
        specgram_layout = QVBoxLayout(specgram_tab)
        self.spectrogram_plot = SpectrogramPlot()
        specgram_layout.addWidget(self.spectrogram_plot)
        tabs.addTab(specgram_tab, "Spectrogram")
        main_layout.addWidget(tabs, stretch=1)

        info_group = QGroupBox("Audio Info")
        info_layout = QGridLayout(info_group)
        self.dur_label = QLabel("Duration: --")
        self.rms_label = QLabel("RMS: --")
        self.peak_label = QLabel("Peak: --")
        self.crest_label = QLabel("Crest: --")
        self.sr_label = QLabel("Sample Rate: --")
        self.ch_label = QLabel("Channels: --")
        info_layout.addWidget(self.dur_label, 0, 0)
        info_layout.addWidget(self.rms_label, 0, 1)
        info_layout.addWidget(self.peak_label, 1, 0)
        info_layout.addWidget(self.crest_label, 1, 1)
        info_layout.addWidget(self.sr_label, 2, 0)
        info_layout.addWidget(self.ch_label, 2, 1)
        main_layout.addWidget(info_group)

        self.status_label = QLabel("")
        main_layout.addWidget(self.status_label)

    def _bind(self) -> None:
        self.load_btn.clicked.connect(self._on_load)
        self.play_btn.clicked.connect(self._vm.play)
        self.stop_btn.clicked.connect(self._vm.stop)
        self.apply_eq_btn.clicked.connect(self._on_apply_eq)
        self.vol_slider.valueChanged.connect(self._on_volume)

    def _on_load(self) -> None:
        path, _ = QFileDialog.getOpenFileName(
            self, "Open Audio", "", "Audio Files (*.wav *.mp3 *.flac *.ogg *.aiff);;All Files (*)"
        )
        if path:
            from pathlib import Path

            audio = self._vm.load_file(Path(path))
            if audio is not None:
                self._update_display(audio)

    def _on_apply_eq(self) -> None:
        gains = [float(s.value()) for s in self.eq_sliders]
        self._vm.eq_gains.value = gains
        self._vm.apply_eq()
        audio = self._vm.audio.value
        if audio is not None:
            self._update_display(audio)

    def _on_volume(self, value: int) -> None:
        self.vol_label.setText(f"{value}%")
        self._vm.volume.value = value / 100.0

    def _update_display(self, audio: AudioSignal) -> None:
        self.wave_plot.plot_signal(audio.signal, name="Audio")
        analysis = self._vm.analysis.value
        if analysis:
            self.dur_label.setText(f"Duration: {analysis.duration:.2f}s")
            self.rms_label.setText(f"RMS: {analysis.rms:.4f}")
            self.peak_label.setText(f"Peak: {analysis.peak:.4f}")
            self.crest_label.setText(f"Crest: {analysis.crest_factor:.2f}")
        self.sr_label.setText(f"Sample Rate: {audio.sampling_rate:.0f} Hz")
        self.ch_label.setText(f"Channels: {audio.channels}")
        spec = self._vm.spectrum.value
        if spec is not None:
            self.freq_plot.plot_spectrum(spec, name="Spectrum")
        self.spectrogram_plot.plot(audio.signal)
