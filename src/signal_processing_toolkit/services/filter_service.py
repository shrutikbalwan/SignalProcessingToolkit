from __future__ import annotations

from scipy import signal as sp_signal

from signal_processing_toolkit.dsp.filters.design import (
    StatefulFilter,
    apply_causal,
    apply_zero_phase,
    design_filter,
    frequency_response,
    impulse_response,
)
from signal_processing_toolkit.models.filter_design import (
    FilterCoefficients,
    FilterDesign,
    FrequencyResponse,
    PoleZeroMap,
)
from signal_processing_toolkit.models.signal import Signal


class FilterService:
    """Application facade over the canonical filtering implementation."""

    def design(self, spec: FilterDesign) -> FilterCoefficients:
        return design_filter(spec)

    def apply(self, signal: Signal, coeffs: FilterCoefficients) -> Signal:
        return apply_zero_phase(signal, coeffs)

    def apply_causal(self, signal: Signal, coeffs: FilterCoefficients) -> Signal:
        return apply_causal(signal, coeffs)

    def streaming(self, coeffs: FilterCoefficients) -> StatefulFilter:
        return StatefulFilter(coeffs)

    def frequency_response(
        self, coeffs: FilterCoefficients, sampling_rate: float, n_points: int = 512
    ) -> FrequencyResponse:
        return frequency_response(coeffs, sampling_rate, n_points)

    def impulse_response(self, coeffs: FilterCoefficients, n_points: int = 64) -> Signal:
        return impulse_response(coeffs, n_points)

    def pole_zero(self, coeffs: FilterCoefficients) -> PoleZeroMap:
        if coeffs.sos is not None:
            zeros, poles, _ = sp_signal.sos2zpk(coeffs.sos)
        else:
            zeros, poles, _ = sp_signal.tf2zpk(coeffs.b, coeffs.a)
        return PoleZeroMap(poles=poles, zeros=zeros)

    def stability(self, coeffs: FilterCoefficients) -> tuple[bool, float]:
        """Return (stable, maximum pole radius); stable means every |pole| < 1."""
        return coeffs.is_stable, coeffs.maximum_pole_radius
