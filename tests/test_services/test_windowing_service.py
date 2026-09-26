from __future__ import annotations

import numpy as np
import pytest

from signal_processing_toolkit.models.enums import WindowType
from signal_processing_toolkit.models.signal import Signal
from signal_processing_toolkit.services.window_service import WindowService


@pytest.fixture
def service() -> WindowService:
    return WindowService()


@pytest.fixture
def ones_signal() -> Signal:
    return Signal(time_data=np.ones(256), sampling_rate=1000.0)


class TestWindowService:
    def test_apply_hanning(self, service: WindowService, ones_signal: Signal) -> None:
        result = service.apply(ones_signal, WindowType.HANNING)
        assert np.allclose(result.time_data, np.hanning(256))

    def test_apply_hamming(self, service: WindowService, ones_signal: Signal) -> None:
        result = service.apply(ones_signal, WindowType.HAMMING)
        assert np.allclose(result.time_data, np.hamming(256))

    def test_apply_blackman(self, service: WindowService, ones_signal: Signal) -> None:
        result = service.apply(ones_signal, WindowType.BLACKMAN)
        assert np.allclose(result.time_data, np.blackman(256))

    def test_compute_metrics(self, service: WindowService, ones_signal: Signal) -> None:
        result = service.apply(ones_signal, WindowType.HANNING)
        metrics = service.compute_metrics(result)
        assert 0 < metrics.energy < 300
