from __future__ import annotations

import numpy as np
from scipy import signal as sp_signal

from src.core.exceptions import FilterDesignError
from src.models.enums import DesignMethod, FilterType, ResponseType
from src.models.filter_design import (
    FilterCoefficients,
    FilterDesign,
    FrequencyResponse,
    PoleZeroMap,
)
from src.models.signal import Signal


class FilterService:
    def design(self, spec: FilterDesign) -> FilterCoefficients:
        if spec.response_type == ResponseType.FIR:
            return self._design_fir(spec)
        return self._design_iir(spec)

    def apply(self, signal: Signal, coeffs: FilterCoefficients) -> Signal:
        filtered = sp_signal.filtfilt(coeffs.b, coeffs.a, signal.time_data)
        return Signal(
            time_data=filtered,
            sampling_rate=signal.sampling_rate,
            metadata=signal.metadata,
        )

    def frequency_response(
        self, coeffs: FilterCoefficients, sampling_rate: float, n_points: int = 512
    ) -> FrequencyResponse:
        w, h = sp_signal.freqz(coeffs.b, coeffs.a, worN=n_points)
        freqs = w / (2 * np.pi) * sampling_rate
        return FrequencyResponse(
            frequencies=freqs,
            magnitude=np.abs(h),
            phase=np.angle(h),
        )

    def impulse_response(self, coeffs: FilterCoefficients, n_points: int = 64) -> Signal:
        impulse = np.zeros(n_points)
        impulse[0] = 1.0
        response = sp_signal.lfilter(coeffs.b, coeffs.a, impulse)
        return Signal(time_data=response, sampling_rate=1.0)

    def pole_zero(self, coeffs: FilterCoefficients) -> PoleZeroMap:
        zeros = np.roots(coeffs.b)
        poles = np.roots(coeffs.a)
        return PoleZeroMap(poles=poles, zeros=zeros)

    def _design_fir(self, spec: FilterDesign) -> FilterCoefficients:
        normalized_cutoff = spec.normalized_cutoff
        cutoff: list[float] | float = (
            list(normalized_cutoff) if isinstance(normalized_cutoff, tuple) else normalized_cutoff
        )
        try:
            b = sp_signal.firwin(
                numtaps=spec.order + 1,
                cutoff=cutoff,
                window="hamming",
                pass_zero=(
                    "lowpass"
                    if spec.filter_type == FilterType.LOWPASS
                    else "highpass"
                    if spec.filter_type == FilterType.HIGHPASS
                    else "bandpass"
                ),
            )
            return FilterCoefficients(b=b, a=np.array([1.0]), order=spec.order)
        except Exception as e:
            raise FilterDesignError(f"FIR design failed: {e}") from e

    def _design_iir(self, spec: FilterDesign) -> FilterCoefficients:
        method_map = {
            DesignMethod.BUTTERWORTH: ("butter", {}),
            DesignMethod.CHEBYSHEV1: ("cheby1", {"rp": spec.passband_ripple}),
            DesignMethod.CHEBYSHEV2: ("cheby2", {"rs": spec.stopband_attenuation}),
            DesignMethod.ELLIPTIC: (
                "ellip",
                {"rp": spec.passband_ripple, "rs": spec.stopband_attenuation},
            ),
        }
        method_name, extra = method_map.get(spec.design_method, ("butter", {}))
        normalized_cutoff2 = spec.normalized_cutoff
        iir_cutoff: list[float] | float = (
            list(normalized_cutoff2)
            if isinstance(normalized_cutoff2, tuple)
            else normalized_cutoff2
        )
        try:
            b, a = getattr(sp_signal, method_name)(
                spec.order,
                iir_cutoff,
                btype=spec.filter_type.value,
                output="ba",
                **extra,
            )
            return FilterCoefficients(b=b, a=a, order=spec.order)
        except Exception as e:
            raise FilterDesignError(f"IIR design failed: {e}") from e
