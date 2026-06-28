from __future__ import annotations

from src.dsp.filters.iir.base import apply_iir_filter, design_iir_filter
from src.models.enums import DesignMethod, FilterType, ResponseType
from src.models.filter_design import FilterDesign
from src.models.signal import Signal


def design_butterworth(
    filter_type: FilterType,
    cutoff: float | tuple[float, float],
    sampling_rate: float,
    order: int = 4,
    passband_ripple: float = 1.0,
    stopband_attenuation: float = 40.0,
) -> FilterDesign:
    if isinstance(cutoff, tuple):
        if filter_type == FilterType.BANDPASS:
            return FilterDesign(
                filter_type=filter_type,
                response_type=ResponseType.IIR,
                design_method=DesignMethod.BUTTERWORTH,
                order=order,
                cutoff_frequency=cutoff,
                sampling_rate=sampling_rate,
                passband_ripple=passband_ripple,
                stopband_attenuation=stopband_attenuation,
            )
        elif filter_type == FilterType.BANDSTOP:
            return FilterDesign(
                filter_type=filter_type,
                response_type=ResponseType.IIR,
                design_method=DesignMethod.BUTTERWORTH,
                order=order,
                cutoff_frequency=cutoff,
                sampling_rate=sampling_rate,
                passband_ripple=passband_ripple,
                stopband_attenuation=stopband_attenuation,
            )
        else:
            raise ValueError("Butterworth bandpass/bandstop requires tuple cutoff")
    else:
        if filter_type in (FilterType.LOWPASS, FilterType.HIGHPASS):
            return FilterDesign(
                filter_type=filter_type,
                response_type=ResponseType.IIR,
                design_method=DesignMethod.BUTTERWORTH,
                order=order,
                cutoff_frequency=cutoff,
                sampling_rate=sampling_rate,
                passband_ripple=passband_ripple,
                stopband_attenuation=stopband_attenuation,
            )
        else:
            raise ValueError("Butterworth lowpass/highpass requires single cutoff")


def design_chebyshev1(
    filter_type: FilterType,
    cutoff: float | tuple[float, float],
    sampling_rate: float,
    order: int = 4,
    passband_ripple: float = 1.0,
    stopband_attenuation: float = 40.0,
) -> FilterDesign:
    return FilterDesign(
        filter_type=filter_type,
        response_type=ResponseType.IIR,
        design_method=DesignMethod.CHEBYSHEV1,
        order=order,
        cutoff_frequency=cutoff,
        sampling_rate=sampling_rate,
        passband_ripple=passband_ripple,
        stopband_attenuation=stopband_attenuation,
    )


def design_chebyshev2(
    filter_type: FilterType,
    cutoff: float | tuple[float, float],
    sampling_rate: float,
    order: int = 4,
    passband_ripple: float = 1.0,
    stopband_attenuation: float = 40.0,
) -> FilterDesign:
    return FilterDesign(
        filter_type=filter_type,
        response_type=ResponseType.IIR,
        design_method=DesignMethod.CHEBYSHEV2,
        order=order,
        cutoff_frequency=cutoff,
        sampling_rate=sampling_rate,
        passband_ripple=passband_ripple,
        stopband_attenuation=stopband_attenuation,
    )


def design_elliptic(
    filter_type: FilterType,
    cutoff: float | tuple[float, float],
    sampling_rate: float,
    order: int = 4,
    passband_ripple: float = 1.0,
    stopband_attenuation: float = 40.0,
) -> FilterDesign:
    return FilterDesign(
        filter_type=filter_type,
        response_type=ResponseType.IIR,
        design_method=DesignMethod.ELLIPTIC,
        order=order,
        cutoff_frequency=cutoff,
        sampling_rate=sampling_rate,
        passband_ripple=passband_ripple,
        stopband_attenuation=stopband_attenuation,
    )


def apply_iir_lowpass(
    signal: Signal, cutoff: float, sampling_rate: float, order: int = 4, **kwargs
) -> Signal:
    design = design_butterworth(FilterType.LOWPASS, cutoff, sampling_rate, order, **kwargs)
    coeffs = design_iir_filter(design)
    result = apply_iir_filter(signal, coeffs)
    return result if isinstance(result, Signal) else signal


def apply_iir_highpass(
    signal: Signal, cutoff: float, sampling_rate: float, order: int = 4, **kwargs
) -> Signal:
    design = design_butterworth(FilterType.HIGHPASS, cutoff, sampling_rate, order, **kwargs)
    coeffs = design_iir_filter(design)
    result = apply_iir_filter(signal, coeffs)
    return result if isinstance(result, Signal) else signal


def apply_iir_bandpass(
    signal: Signal, low: float, high: float, sampling_rate: float, order: int = 4, **kwargs
) -> Signal:
    design = design_butterworth(FilterType.BANDPASS, (low, high), sampling_rate, order, **kwargs)
    coeffs = design_iir_filter(design)
    result = apply_iir_filter(signal, coeffs)
    return result if isinstance(result, Signal) else signal


def apply_iir_bandstop(
    signal: Signal, low: float, high: float, sampling_rate: float, order: int = 4, **kwargs
) -> Signal:
    design = design_butterworth(FilterType.BANDSTOP, (low, high), sampling_rate, order, **kwargs)
    coeffs = design_iir_filter(design)
    result = apply_iir_filter(signal, coeffs)
    return result if isinstance(result, Signal) else signal
