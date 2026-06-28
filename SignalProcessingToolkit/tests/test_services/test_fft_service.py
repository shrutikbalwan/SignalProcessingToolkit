from __future__ import annotations

import numpy as np
import pytest

from src.models.signal import Signal
from src.services.fft_service import FFTService


@pytest.fixture
def service() -> FFTService:
    return FFTService()


class TestFFTService:
    def test_compute(self, service: FFTService) -> None:
        sr = 1000
        t = np.linspace(0, 1, sr, endpoint=False)
        sig = Signal(time_data=np.sin(2 * np.pi * 10 * t), sampling_rate=float(sr))
        result = service.compute(sig)
        assert result.frequencies is not None
        assert result.magnitude is not None
        peak_idx = int(np.argmax(result.magnitude[:50]))
        assert 9 < result.frequencies[peak_idx] < 11

    def test_ifft(self, service: FFTService) -> None:
        sr = 1000
        t = np.linspace(0, 1, sr, endpoint=False)
        sig = Signal(time_data=np.sin(2 * np.pi * 10 * t), sampling_rate=float(sr))
        result = service.compute(sig)
        recon = service.compute_inverse(result)
        assert len(recon.time_data) == len(sig.time_data)
        assert float(np.max(np.abs(recon.time_data - sig.time_data))) < 0.1
