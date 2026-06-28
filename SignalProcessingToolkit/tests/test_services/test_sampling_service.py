from __future__ import annotations

import numpy as np
import pytest

from src.models.signal import Signal
from src.services.sampling_service import SamplingService


@pytest.fixture
def service() -> SamplingService:
    return SamplingService()


class TestSamplingService:
    def test_downsample(self, service: SamplingService) -> None:
        sr = 1000
        t = np.linspace(0, 1, sr, endpoint=False)
        sig = Signal(time_data=np.sin(2 * np.pi * 10 * t), sampling_rate=float(sr))
        down = service.downsample(sig, 2)
        assert len(down.time_data) == len(sig.time_data) // 2
        assert down.sampling_rate == sr // 2

    def test_upsample(self, service: SamplingService) -> None:
        sr = 1000
        t = np.linspace(0, 1, sr, endpoint=False)
        sig = Signal(time_data=np.sin(2 * np.pi * 10 * t), sampling_rate=float(sr))
        up = service.upsample(sig, 2)
        assert len(up.time_data) == len(sig.time_data) * 2
        assert up.sampling_rate == sr * 2
