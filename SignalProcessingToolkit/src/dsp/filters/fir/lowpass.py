from __future__ import annotations

from src.dsp.filters.fir.base import apply_fir_filter, design_fir_filter
from src.models.enums import DesignMethod, FilterType, ResponseType
from src.models.filter_design import FilterDesign
from src.models.signal import Signal


def design_lowpass_fir(
    cutoff: float,
    sampling_rate: float,
    order: int = 50,
    design_method: DesignMethod = DesignMethod.WINDOW,
    window_type: str = "hamming",
    passband_ripple: float = 1.0,
    stopband_attenuation: float = 40.0,
) -> FilterDesign:
    return FilterDesign(
        filter_type=FilterType.LOWPASS,
        response_type=ResponseType.FIR,
        design_method=design_method,
        order=order,
        cutoff_frequency=cutoff,
        sampling_rate=sampling_rate,
        passband_ripple=passband_ripple,
        stopband_attenuation=stopband_attenuation,
    )


def design_highpass_fir(
    cutoff: float,
    sampling_rate: float,
    order: int = 50,
    design_method: DesignMethod = DesignMethod.WINDOW,
    window_type: str = "hamming",
    passband_ripple: float = 1.0,
    stopband_attenuation: float = 40.0,
) -> FilterDesign:
    return FilterDesign(
        filter_type=FilterType.HIGHPASS,
        response_type=ResponseType.FIR,
        design_method=design_method,
        order=order,
        cutoff_frequency=cutoff,
        sampling_rate=sampling_rate,
        passband_ripple=passband_ripple,
        stopband_attenuation=stopband_attenuation,
    )


def design_bandpass_fir(
    low_cutoff: float,
    high_cutoff: float,
    sampling_rate: float,
    order: int = 50,
    design_method: DesignMethod = DesignMethod.WINDOW,
    window_type: str = "hamming",
    passband_ripple: float = 1.0,
    stopband_attenuation: float = 40.0,
) -> FilterDesign:
    if low_cutoff >= high_cutoff:
        raise ValueError("Low cutoff must be less than high cutoff")
    return FilterDesign(
        filter_type=FilterType.BANDPASS,
        response_type=ResponseType.FIR,
        design_method=design_method,
        order=order,
        cutoff_frequency=(low_cutoff, high_cutoff),
        sampling_rate=sampling_rate,
        passband_ripple=passband_ripple,
        stopband_attenuation=stopband_attenuation,
    )


def design_bandstop_fir(
    low_cutoff: float,
    high_cutoff: float,
    sampling_rate: float,
    order: int = 50,
    design_method: DesignMethod = DesignMethod.WINDOW,
    window_type: str = "hamming",
    passband_ripple: float = 1.0,
    stopband_attenuation: float = 40.0,
) -> FilterDesign:
    if low_cutoff >= high_cutoff:
        raise ValueError("Low cutoff must be less than high cutoff")
    return FilterDesign(
        filter_type=FilterType.BANDSTOP,
        response_type=ResponseType.FIR,
        design_method=design_method,
        order=order,
        cutoff_frequency=(low_cutoff, high_cutoff),
        sampling_rate=sampling_rate,
        passband_ripple=passband_ripple,
        stopband_attenuation=stopband_attenuation,
    )


def apply_fir_lowpass(
    signal: Signal, cutoff: float, sampling_rate: float, order: int = 50, **kwargs
) -> Signal:
    design = design_lowpass_fir(cutoff, sampling_rate, order, **kwargs)
    coeffs = design_fir_filter(design)
    result = apply_fir_filter(signal, coeffs)
    return result if isinstance(result, Signal) else signal


def apply_fir_highpass(
    signal: Signal, cutoff: float, sampling_rate: float, order: int = 50, **kwargs
) -> Signal:
    design = design_highpass_fir(cutoff, sampling_rate, order, **kwargs)
    coeffs = design_fir_filter(design)
    result = apply_fir_filter(signal, coeffs)
    return result if isinstance(result, Signal) else signal


def apply_fir_bandpass(
    signal: Signal, low: float, high: float, sampling_rate: float, order: int = 50, **kwargs
) -> Signal:
    design = design_bandpass_fir(low, high, sampling_rate, order, **kwargs)
    coeffs = design_fir_filter(design)
    result = apply_fir_filter(signal, coeffs)
    return result if isinstance(result, Signal) else signal


def apply_fir_bandstop(
    signal: Signal, low: float, high: float, sampling_rate: float, order: int = 50, **kwargs
) -> Signal:
    design = design_bandstop_fir(low, high, sampling_rate, order, **kwargs)
    coeffs = design_fir_filter(design)
    result = apply_fir_filter(signal, coeffs)
    return result if isinstance(result, Signal) else signal
