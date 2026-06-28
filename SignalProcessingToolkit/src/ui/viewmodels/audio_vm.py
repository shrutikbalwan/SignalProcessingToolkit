from __future__ import annotations

from pathlib import Path

from src.models.audio import AudioSignal
from src.models.fft_result import FFTResult
from src.repositories.implementations.file_audio_repository import FileAudioRepository
from src.services.audio_service import EQ_BANDS, AudioAnalysis, AudioService
from src.services.fft_service import FFTService
from src.ui.viewmodels.base_viewmodel import BaseViewModel, Observable


class AudioViewModel(BaseViewModel):
    def __init__(self, audio_service: AudioService) -> None:
        super().__init__()
        self._audio_service = audio_service
        self._fft_service = FFTService()
        self._repo = FileAudioRepository()

        self.audio = Observable[AudioSignal | None](None)
        self.is_playing = Observable[bool](False)
        self.volume = Observable[float](1.0)

        self.eq_gains = Observable[list[float]]([0.0] * len(EQ_BANDS))
        self.eq_enabled = Observable[bool](False)

        self.analysis = Observable[AudioAnalysis | None](None)
        self.spectrum = Observable[FFTResult | None](None)
        self.spectrogram_data = Observable[tuple | None](None)
        self.status_message = Observable[str]("")

    def load_file(self, path: Path) -> AudioSignal | None:
        try:
            audio = self._repo.load(path)
            self.audio.value = audio
            self.analysis.value = self._audio_service.analyze(audio)
            self.spectrum.value = self._audio_service.compute_spectrum(audio)
            self.status_message.value = f"Loaded: {path.name}"
            return audio
        except Exception as e:
            self.status_message.value = f"Failed to load: {e}"
            return None

    def play(self) -> None:
        audio = self._get_playback_audio()
        if audio is None:
            return
        try:
            self._audio_service.play(audio)
            self.is_playing.value = True
            self.status_message.value = "Playing"
        except Exception as e:
            self.status_message.value = f"Playback error: {e}"

    def stop(self) -> None:
        try:
            self._audio_service.stop()
            self.is_playing.value = False
            self.status_message.value = "Stopped"
        except Exception as e:
            self.status_message.value = f"Stop error: {e}"

    def apply_eq(self) -> None:
        audio = self.audio.value
        if audio is None:
            return
        equalized = self._audio_service.equalize(audio, self.eq_gains.value)
        self.audio.value = equalized
        self.analysis.value = self._audio_service.analyze(equalized)
        self.spectrum.value = self._audio_service.compute_spectrum(equalized)
        self.status_message.value = "EQ applied"

    def _get_playback_audio(self) -> AudioSignal | None:
        audio = self.audio.value
        if audio is None:
            self.status_message.value = "No audio loaded"
            return None
        if self.volume.value != 1.0:
            audio = self._audio_service.change_volume(audio, self.volume.value)
        return audio

    def dispose(self) -> None:
        self.stop()
        super().dispose()
        self.audio.value = None
