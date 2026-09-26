from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from scipy import signal as sp_signal

from signal_processing_toolkit.core.exceptions import AudioError
from signal_processing_toolkit.models.audio import AudioSignal
from signal_processing_toolkit.models.fft_result import FFTResult
from signal_processing_toolkit.models.signal import Signal

EQ_BANDS = [31, 62, 125, 250, 500, 1000, 2000, 4000, 8000, 16000]


@dataclass
class AudioAnalysis:
    rms: float
    peak: float
    crest_factor: float
    duration: float


class AudioService:
    def play(self, audio: AudioSignal) -> None:
        try:
            import sounddevice as sd

            sd.play(audio.samples, int(audio.sampling_rate))
        except Exception as e:
            raise AudioError(f"Playback failed: {e}") from e

    def stop(self) -> None:
        try:
            import sounddevice as sd

            sd.stop()
        except Exception as e:
            raise AudioError(f"Stop failed: {e}") from e

    def record(self, duration: float, sampling_rate: int = 44100) -> AudioSignal:
        try:
            import sounddevice as sd

            recording = sd.rec(
                int(duration * sampling_rate),
                samplerate=sampling_rate,
                channels=1,
            )
            sd.wait()
            signal = Signal(
                time_data=recording[:, 0],
                sampling_rate=float(sampling_rate),
                channel_names=("mono",),
                units="FS",
            )
            return AudioSignal(signal=signal, channels=1)
        except Exception as e:
            raise AudioError(f"Recording failed: {e}") from e

    def change_volume(self, audio: AudioSignal, factor: float) -> AudioSignal:
        return AudioSignal(
            signal=audio.signal.updated(
                time_data=audio.samples * factor,
                operation="change_volume",
                parameters={"factor": factor},
            ),
            channels=audio.channels,
            bit_depth=audio.bit_depth,
        )

    def analyze(self, audio: AudioSignal) -> AudioAnalysis:
        data = audio.samples
        rms = float(np.sqrt(np.mean(np.abs(data) ** 2)))
        peak = float(np.max(np.abs(data)))
        crest = peak / rms if rms > 0 else 0.0
        return AudioAnalysis(rms=rms, peak=peak, crest_factor=crest, duration=audio.duration)

    def equalize(self, audio: AudioSignal, gains: list[float], q: float = 1.0) -> AudioSignal:
        if len(gains) != len(EQ_BANDS):
            raise ValueError(f"Expected {len(EQ_BANDS)} gain values, got {len(gains)}")
        data = audio.samples.copy()
        fs = audio.sampling_rate
        nyquist = fs / 2.0
        for band_gain, center_hz in zip(gains, EQ_BANDS, strict=False):
            if center_hz >= nyquist:
                continue
            normalized = center_hz / nyquist
            b, a = sp_signal.iirpeak(normalized, q)
            filtered = sp_signal.filtfilt(b, a, data, axis=Signal.SAMPLE_AXIS)
            db_gain = band_gain
            linear_gain = 10 ** (db_gain / 20.0)
            data = data + (filtered - data) * (1 - 1.0 / (linear_gain + 1e-10))
        return AudioSignal(
            signal=audio.signal.updated(
                time_data=data,
                operation="equalize",
                parameters={"gains_db": gains, "q": q},
            ),
            channels=audio.channels,
            bit_depth=audio.bit_depth,
        )

    def compute_spectrum(self, audio: AudioSignal, n_fft: int = 4096) -> FFTResult:
        from signal_processing_toolkit.dsp.fft import compute_fft

        return compute_fft(audio.signal, min(n_fft, audio.signal.n_samples))
