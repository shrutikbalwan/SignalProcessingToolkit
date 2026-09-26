from __future__ import annotations

import numpy as np
import pytest

from signal_processing_toolkit.models.enums import DesignMethod, FilterType, ResponseType
from signal_processing_toolkit.models.filter_design import FilterCoefficients, FilterDesign
from signal_processing_toolkit.models.signal import Signal
from signal_processing_toolkit.services.filter_service import FilterService


@pytest.fixture
def service() -> FilterService:
    return FilterService()


@pytest.fixture
def noise() -> Signal:
    sr = 1000
    rng = np.random.default_rng(42)
    return Signal(time_data=rng.normal(0, 1, sr), sampling_rate=float(sr))


class TestFilterService:
    def test_design_lowpass(self, service: FilterService) -> None:
        spec = FilterDesign(
            filter_type=FilterType.LOWPASS,
            response_type=ResponseType.FIR,
            design_method=DesignMethod.WINDOW,
            order=20,
            cutoff_frequency=100,
            sampling_rate=1000,
        )
        coeffs = service.design(spec)
        assert isinstance(coeffs, FilterCoefficients)
        assert coeffs.b is not None

    def test_apply_filter(self, service: FilterService, noise: Signal) -> None:
        spec = FilterDesign(
            filter_type=FilterType.LOWPASS,
            response_type=ResponseType.FIR,
            design_method=DesignMethod.WINDOW,
            order=20,
            cutoff_frequency=100,
            sampling_rate=1000,
        )
        coeffs = service.design(spec)
        filtered = service.apply(noise, coeffs)
        assert len(filtered.time_data) == len(noise.time_data)
