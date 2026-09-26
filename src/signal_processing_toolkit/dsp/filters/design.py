from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import numpy as np
from scipy import signal as sp_signal

from signal_processing_toolkit.core.exceptions import FilterDesignError
from signal_processing_toolkit.models.enums import DesignMethod, FilterType, ResponseType
from signal_processing_toolkit.models.filter_design import (
    FilterCoefficients,
    FilterDesign,
    FrequencyResponse,
)
from signal_processing_toolkit.models.signal import Signal


def create_filter_design(
    filter_type: FilterType,
    response_type: ResponseType,
    design_method: DesignMethod,
    order: int,
    cutoff_frequency: float | tuple[float, float],
    sampling_rate: float,
    passband_ripple: float = 1.0,
    stopband_attenuation: float = 40.0,
) -> FilterDesign:
    return FilterDesign(
        filter_type,
        response_type,
        design_method,
        order,
        cutoff_frequency,
        sampling_rate,
        passband_ripple,
        stopband_attenuation,
    )


def design_filter(design: FilterDesign) -> FilterCoefficients:
    """Design one canonical FIR transfer function or IIR SOS cascade."""
    cutoff = design.cutoff_frequency
    try:
        if design.response_type == ResponseType.FIR:
            pass_zero: bool | str = {
                FilterType.LOWPASS: True,
                FilterType.HIGHPASS: False,
                FilterType.BANDPASS: False,
                FilterType.BANDSTOP: True,
            }[design.filter_type]
            b = sp_signal.firwin(
                design.order + 1,
                cutoff,
                window=design.window,
                pass_zero=pass_zero,
                fs=design.sampling_rate,
            )
            return FilterCoefficients(b=b, a=np.array([1.0]), order=design.order)

        family = {
            DesignMethod.BUTTERWORTH: "butter",
            DesignMethod.CHEBYSHEV1: "cheby1",
            DesignMethod.CHEBYSHEV2: "cheby2",
            DesignMethod.ELLIPTIC: "ellip",
        }.get(design.design_method)
        if family is None:
            raise ValueError(f"{design.design_method.value} is not an IIR design method")
        kwargs: dict[str, float] = {}
        if family in ("cheby1", "ellip"):
            kwargs["rp"] = design.passband_ripple
        if family in ("cheby2", "ellip"):
            kwargs["rs"] = design.stopband_attenuation
        sos = sp_signal.iirfilter(
            design.order,
            cutoff,
            btype=design.filter_type.value,
            ftype=family,
            output="sos",
            fs=design.sampling_rate,
            **kwargs,
        )
        b, a = sp_signal.sos2tf(sos)
        return FilterCoefficients(b=b, a=a, order=design.order, sos=sos)
    except (TypeError, ValueError) as error:
        raise FilterDesignError(f"Filter design failed: {error}") from error


def _zero_phase_padlen(coefficients: FilterCoefficients) -> int:
    if coefficients.sos is None:
        return 3 * (max(len(coefficients.a), len(coefficients.b)) - 1)
    sos = coefficients.sos
    correction = min(np.sum(sos[:, 2] == 0), np.sum(sos[:, 5] == 0))
    return int(3 * (2 * len(sos) + 1 - correction))


def apply_zero_phase(signal: Signal, coefficients: FilterCoefficients) -> Signal:
    """Apply an offline forward/backward filter with zero phase distortion."""
    padlen = _zero_phase_padlen(coefficients)
    if signal.n_samples <= padlen:
        raise ValueError(
            f"Zero-phase filtering requires more than {padlen} samples; "
            "use causal filtering for shorter signals"
        )
    if coefficients.sos is not None:
        values = sp_signal.sosfiltfilt(
            coefficients.sos, signal.time_data, axis=Signal.SAMPLE_AXIS, padlen=padlen
        )
    else:
        values = sp_signal.filtfilt(
            coefficients.b,
            coefficients.a,
            signal.time_data,
            axis=Signal.SAMPLE_AXIS,
            padlen=padlen,
        )
    return signal.updated(
        time_data=values,
        operation="filter_zero_phase",
        parameters={"order": coefficients.order, "sos": coefficients.is_sos},
    )


@dataclass
class StatefulFilter:
    """Causal filter that retains delay state between streaming chunks."""

    coefficients: FilterCoefficients
    state: np.ndarray | None = None

    def reset(self) -> None:
        self.state = None

    def process(self, signal: Signal) -> Signal:
        if signal.n_samples == 0:
            return signal.copy()
        channels = () if signal.time_data.ndim == 1 else (signal.n_channels,)
        if self.coefficients.sos is not None:
            if self.state is None:
                self.state = np.zeros((len(self.coefficients.sos), 2, *channels))
            values, self.state = sp_signal.sosfilt(
                self.coefficients.sos,
                signal.time_data,
                axis=Signal.SAMPLE_AXIS,
                zi=self.state,
            )
        else:
            state_length = max(len(self.coefficients.a), len(self.coefficients.b)) - 1
            if self.state is None:
                self.state = np.zeros((state_length, *channels))
            values, self.state = sp_signal.lfilter(
                self.coefficients.b,
                self.coefficients.a,
                signal.time_data,
                axis=Signal.SAMPLE_AXIS,
                zi=self.state,
            )
        return signal.updated(
            time_data=values,
            operation="filter_causal",
            parameters={"order": self.coefficients.order, "sos": self.coefficients.is_sos},
        )


def apply_causal(signal: Signal, coefficients: FilterCoefficients) -> Signal:
    return StatefulFilter(coefficients).process(signal)


def frequency_response(
    coefficients: FilterCoefficients,
    sampling_rate: float,
    n_points: int = 4096,
) -> FrequencyResponse:
    """Return the canonical digital-filter response in Hz.

    ``magnitude`` is a linear amplitude ratio and ``phase`` is in radians.
    SOS evaluation is retained when available to avoid expanding a high-order
    IIR cascade into an ill-conditioned transfer-function polynomial.
    """
    if sampling_rate <= 0 or not np.isfinite(sampling_rate):
        raise ValueError("sampling_rate must be finite and positive")
    if n_points < 1:
        raise ValueError("n_points must be positive")
    if coefficients.sos is not None:
        frequencies, response = sp_signal.sosfreqz(
            coefficients.sos, worN=n_points, fs=sampling_rate
        )
    else:
        frequencies, response = sp_signal.freqz(
            coefficients.b, coefficients.a, worN=n_points, fs=sampling_rate
        )
    return FrequencyResponse(frequencies, np.abs(response), np.angle(response))


def filter_group_delay(
    coefficients: FilterCoefficients,
    sampling_rate: float,
    n_points: int = 4096,
) -> tuple[np.ndarray, np.ndarray]:
    """Return frequency in Hz and group delay in samples."""
    if sampling_rate <= 0 or not np.isfinite(sampling_rate):
        raise ValueError("sampling_rate must be finite and positive")
    if n_points < 1:
        raise ValueError("n_points must be positive")
    frequencies, delay = sp_signal.group_delay(
        (coefficients.b, coefficients.a), w=n_points, fs=sampling_rate
    )
    return np.asarray(frequencies), np.asarray(delay)


def impulse_response(
    coefficients: FilterCoefficients,
    n_samples: int = 1024,
    sampling_rate: float = 1.0,
) -> Signal:
    """Return the causal response to a unit impulse."""
    if n_samples < 1:
        raise ValueError("n_samples must be positive")
    impulse = np.zeros(n_samples)
    impulse[0] = 1.0
    return apply_causal(Signal(impulse, sampling_rate), coefficients)


def step_response(
    coefficients: FilterCoefficients,
    n_samples: int = 1024,
    sampling_rate: float = 1.0,
) -> Signal:
    """Return the causal response to a unit step."""
    if n_samples < 1:
        raise ValueError("n_samples must be positive")
    return apply_causal(Signal(np.ones(n_samples), sampling_rate), coefficients)


def apply_filter(signal: Signal, coefficients: FilterCoefficients) -> Signal:
    """Compatibility alias for offline zero-phase filtering."""
    return apply_zero_phase(signal, coefficients)


def _convenience(
    filter_type: FilterType,
    cutoff: float | tuple[float, float],
    sampling_rate: float,
    order: int,
    response_type: str,
    design_method: str,
    **kwargs: Any,
) -> FilterCoefficients:
    response = ResponseType(response_type)
    method = DesignMethod(design_method)
    return design_filter(
        FilterDesign(filter_type, response, method, order, cutoff, sampling_rate, **kwargs)
    )


def design_lowpass(
    cutoff: float,
    sampling_rate: float,
    order: int = 4,
    response_type: str = "fir",
    design_method: str = "window",
    **kwargs: Any,
) -> FilterCoefficients:
    return _convenience(
        FilterType.LOWPASS, cutoff, sampling_rate, order, response_type, design_method, **kwargs
    )


def design_highpass(
    cutoff: float,
    sampling_rate: float,
    order: int = 4,
    response_type: str = "fir",
    design_method: str = "window",
    **kwargs: Any,
) -> FilterCoefficients:
    return _convenience(
        FilterType.HIGHPASS, cutoff, sampling_rate, order, response_type, design_method, **kwargs
    )


def design_bandpass(
    low: float,
    high: float,
    sampling_rate: float,
    order: int = 4,
    response_type: str = "fir",
    design_method: str = "window",
    **kwargs: Any,
) -> FilterCoefficients:
    return _convenience(
        FilterType.BANDPASS,
        (low, high),
        sampling_rate,
        order,
        response_type,
        design_method,
        **kwargs,
    )


def design_bandstop(
    low: float,
    high: float,
    sampling_rate: float,
    order: int = 4,
    response_type: str = "fir",
    design_method: str = "window",
    **kwargs: Any,
) -> FilterCoefficients:
    return _convenience(
        FilterType.BANDSTOP,
        (low, high),
        sampling_rate,
        order,
        response_type,
        design_method,
        **kwargs,
    )


def normalize_coefficients(coefficients: FilterCoefficients) -> FilterCoefficients:
    if coefficients.a[0] == 1:
        return coefficients
    return FilterCoefficients(
        coefficients.b / coefficients.a[0],
        coefficients.a / coefficients.a[0],
        coefficients.order,
        coefficients.sos,
    )


def cascade_filters(coeffs_list: list[FilterCoefficients]) -> FilterCoefficients:
    if not coeffs_list:
        raise ValueError("Empty filter list")
    sos_parts = []
    for coefficients in coeffs_list:
        sos_parts.append(
            coefficients.sos
            if coefficients.sos is not None
            else sp_signal.tf2sos(coefficients.b, coefficients.a)
        )
    sos = np.vstack(sos_parts)
    b, a = sp_signal.sos2tf(sos)
    return FilterCoefficients(b, a, sum(item.order for item in coeffs_list), sos)


def estimate_filter_order(
    filter_type: FilterType,
    response_type: ResponseType,
    cutoff: float | tuple[float, float],
    sampling_rate: float,
    passband_ripple: float = 1.0,
    stopband_attenuation: float = 40.0,
    transition_width: float | None = None,
) -> int:
    del filter_type, cutoff, sampling_rate, passband_ripple
    if transition_width is None or transition_width <= 0:
        raise ValueError("transition_width must be explicitly positive")
    if response_type == ResponseType.FIR:
        order, _ = sp_signal.kaiserord(stopband_attenuation, transition_width)
        return int(order)
    raise ValueError("IIR order estimation requires explicit passband and stopband edges")
