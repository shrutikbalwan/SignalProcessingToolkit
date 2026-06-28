from __future__ import annotations

import numpy as np
import pytest

from src.models.enums import WaveformType
from src.models.signal import Signal
from src.services.signal_service import SignalService


@pytest.fixture
def service() -> SignalService:
    return SignalService()


@pytest.fixture
def sine(service: SignalService) -> Signal:
    return service.generate(WaveformType.SINE, frequency=10, sampling_rate=1000, duration=1.0)


class TestSignalService:
    def test_generate_returns_signal(self, sine: Signal) -> None:
        assert isinstance(sine, Signal)
        assert len(sine.time_data) == 1000
        assert sine.sampling_rate == 1000

    def test_clip(self, service: SignalService, sine: Signal) -> None:
        clipped = service.clip(sine, -0.5, 0.5)
        assert float(np.max(np.abs(clipped.time_data))) <= 0.5

    def test_rectify(self, service: SignalService, sine: Signal) -> None:
        rect = service.rectify(sine)
        assert float(np.min(rect.time_data)) >= 0

    def test_mix(self, service: SignalService, sine: Signal) -> None:
        noise = service.generate(WaveformType.NOISE, sampling_rate=1000, duration=1.0)
        mixed = service.mix([sine, noise], [0.7, 0.3])
        assert len(mixed.time_data) == 1000
