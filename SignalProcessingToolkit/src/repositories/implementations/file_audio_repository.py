from __future__ import annotations

from pathlib import Path

import numpy as np
import soundfile as sf  # type: ignore[import-untyped]

from src.core.constants import SUPPORTED_AUDIO_FORMATS
from src.core.exceptions import FileFormatError
from src.models.audio import AudioSignal
from src.models.signal import Signal, SignalMetadata


class FileAudioRepository:
    def load(self, path: Path) -> AudioSignal:
        if path.suffix.lower() not in SUPPORTED_AUDIO_FORMATS:
            raise FileFormatError(f"Unsupported audio format: {path.suffix}")
        data, samplerate = sf.read(str(path))
        if data.ndim > 1:
            channels = data.shape[1]
            data = np.mean(data, axis=1)
        else:
            channels = 1
        signal = Signal(
            time_data=data,
            sampling_rate=float(samplerate),
            metadata=SignalMetadata(name=path.stem, source=str(path)),
        )
        return AudioSignal(signal=signal, channels=channels, audio_format=path.suffix[1:])

    def save(self, audio: AudioSignal, path: Path) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        sf.write(str(path), audio.samples, int(audio.sampling_rate))

    def get_metadata(self, path: Path) -> dict:
        info = sf.info(str(path))
        return {
            "samplerate": info.samplerate,
            "channels": info.channels,
            "duration": info.duration,
            "format": info.format,
            "subtype": info.subtype,
        }

    def get_supported_formats(self) -> set[str]:
        return SUPPORTED_AUDIO_FORMATS
