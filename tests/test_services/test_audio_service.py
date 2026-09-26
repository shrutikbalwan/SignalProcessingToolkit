from __future__ import annotations

import numpy as np
import pytest

from signal_processing_toolkit.models.audio import AudioSignal
from signal_processing_toolkit.models.signal import Signal
from signal_processing_toolkit.services.audio_service import AudioService


@pytest.fixture
def service() -> AudioService:
    return AudioService()


@pytest.fixture
def tone() -> AudioSignal:
    sr = 44100
    t = np.linspace(0, 0.5, int(sr * 0.5), endpoint=False)
    sig = Signal(time_data=np.sin(2 * np.pi * 440 * t), sampling_rate=float(sr))
    return AudioSignal(signal=sig)


class TestAudioService:
    def test_analyze(self, service: AudioService, tone: AudioSignal) -> None:
        result = service.analyze(tone)
        assert result.rms > 0
        assert result.peak > 0

    def test_equalize(self, service: AudioService, tone: AudioSignal) -> None:
        gains = [0] * 10
        eq = service.equalize(tone, gains)
        assert len(eq.samples) == len(tone.samples)
        assert float(np.max(np.abs(eq.samples))) > 0
