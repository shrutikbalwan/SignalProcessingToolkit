from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from src.models.enums import DesignMethod, FilterType, ResponseType
    from src.models.filter_design import FilterCoefficients, FilterDesign
    from src.models.signal import Signal


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
    from src.models.filter_design import FilterDesign

    return FilterDesign(
        filter_type=filter_type,
        response_type=response_type,
        design_method=design_method,
        order=order,
        cutoff_frequency=cutoff_frequency,
        sampling_rate=sampling_rate,
        passband_ripple=passband_ripple,
        stopband_attenuation=stopband_attenuation,
    )


def design_filter(design: FilterDesign) -> FilterCoefficients:
    if design.response_type.value == "fir":
        from src.dsp.filters.fir.base import design_fir_filter

        return design_fir_filter(design)
    else:
        from src.dsp.filters.iir.base import design_iir_filter

        return design_iir_filter(design)


def apply_filter(signal: Signal, coefficients: FilterCoefficients) -> Signal:

    if isinstance(coefficients.b, list) or len(coefficients.b) == 1:
        from src.dsp.filters.fir.base import apply_fir_filter

        result = apply_fir_filter(signal, coefficients)
    else:
        from src.dsp.filters.iir.base import apply_iir_filter

        result = apply_iir_filter(signal, coefficients)
    return result if isinstance(result, Signal) else signal


def design_lowpass(
    cutoff: float,
    sampling_rate: float,
    order: int = 4,
    response_type: str = "fir",
    design_method: str = "window",
    **kwargs,
) -> FilterCoefficients:
    from src.models.enums import DesignMethod, FilterType, ResponseType
    from src.models.filter_design import FilterDesign

    _rt = ResponseType.FIR if response_type == "fir" else ResponseType.IIR
    _dm = DesignMethod.WINDOW if design_method == "window" else DesignMethod(design_method)
    design = FilterDesign(
        filter_type=FilterType.LOWPASS,
        response_type=_rt,
        design_method=_dm,
        order=order,
        cutoff_frequency=cutoff,
        sampling_rate=sampling_rate,
        **kwargs,
    )
    return design_filter(design)


def design_highpass(
    cutoff: float,
    sampling_rate: float,
    order: int = 4,
    response_type: str = "fir",
    design_method: str = "window",
    **kwargs,
) -> FilterCoefficients:
    from src.models.enums import DesignMethod, FilterType, ResponseType
    from src.models.filter_design import FilterDesign

    _rt = ResponseType.FIR if response_type == "fir" else ResponseType.IIR
    _dm = DesignMethod.WINDOW if design_method == "window" else DesignMethod(design_method)
    design = FilterDesign(
        filter_type=FilterType.HIGHPASS,
        response_type=_rt,
        design_method=_dm,
        order=order,
        cutoff_frequency=cutoff,
        sampling_rate=sampling_rate,
        **kwargs,
    )
    return design_filter(design)


def design_bandpass(
    low: float,
    high: float,
    sampling_rate: float,
    order: int = 4,
    response_type: str = "fir",
    design_method: str = "window",
    **kwargs,
) -> FilterCoefficients:
    from src.models.enums import DesignMethod, FilterType, ResponseType
    from src.models.filter_design import FilterDesign

    _rt = ResponseType.FIR if response_type == "fir" else ResponseType.IIR
    _dm = DesignMethod.WINDOW if design_method == "window" else DesignMethod(design_method)
    design = FilterDesign(
        filter_type=FilterType.BANDPASS,
        response_type=_rt,
        design_method=_dm,
        order=order,
        cutoff_frequency=(low, high),
        sampling_rate=sampling_rate,
        **kwargs,
    )
    return design_filter(design)


def design_bandstop(
    low: float,
    high: float,
    sampling_rate: float,
    order: int = 4,
    response_type: str = "fir",
    design_method: str = "window",
    **kwargs,
) -> FilterCoefficients:
    from src.models.enums import DesignMethod, FilterType, ResponseType
    from src.models.filter_design import FilterDesign

    _rt = ResponseType.FIR if response_type == "fir" else ResponseType.IIR
    _dm = DesignMethod.WINDOW if design_method == "window" else DesignMethod(design_method)
    design = FilterDesign(
        filter_type=FilterType.BANDSTOP,
        response_type=_rt,
        design_method=_dm,
        order=order,
        cutoff_frequency=(low, high),
        sampling_rate=sampling_rate,
        **kwargs,
    )
    return design_filter(design)


def estimate_filter_order(
    filter_type: FilterType,
    response_type: ResponseType,
    cutoff: float | tuple[float, float],
    sampling_rate: float,
    passband_ripple: float = 1.0,
    stopband_attenuation: float = 40.0,
    transition_width: float | None = None,
) -> int:
    if transition_width is None:
        if isinstance(cutoff, tuple):
            transition_width = (cutoff[1] - cutoff[0]) / 10
        else:
            transition_width = cutoff / 10

    nyquist = sampling_rate / 2
    transition_norm = transition_width / nyquist

    if response_type.value == "fir":
        from scipy.signal import kaiserord

        try:
            beta, order = kaiserord(
                ripple=passband_ripple,
                width=transition_norm,
            )
            return int(max(order, 1))
        except Exception:
            return 51
    else:
        if filter_type in (FilterType.LOWPASS, FilterType.HIGHPASS):
            from scipy.signal import buttord

            assert isinstance(cutoff, float)
            wp = cutoff / nyquist
            ws = min((cutoff + transition_width) / nyquist, 0.99)
            result_order, _ = buttord(wp, ws, passband_ripple, stopband_attenuation)
            return int(result_order)
        else:
            return 4


def normalize_coefficients(coefficients: FilterCoefficients) -> FilterCoefficients:
    if len(coefficients.a) > 0 and coefficients.a[0] != 1:
        a0 = coefficients.a[0]
        normalized_b = coefficients.b / a0
        normalized_a = coefficients.a / a0
        from src.models.filter_design import FilterCoefficients

        return FilterCoefficients(b=normalized_b, a=normalized_a, order=coefficients.order)
    return coefficients


def cascade_filters(coeffs_list: list[FilterCoefficients]) -> FilterCoefficients:
    import numpy as np

    from src.models.filter_design import FilterCoefficients

    if not coeffs_list:
        raise ValueError("Empty filter list")

    if len(coeffs_list) == 1:
        return coeffs_list[0]

    b_total = coeffs_list[0].b
    a_total = coeffs_list[0].a

    for coeffs in coeffs_list[1:]:
        b_total = np.convolve(b_total, coeffs.b)
        a_total = np.convolve(a_total, coeffs.a)

    order = len(b_total) + len(a_total) - 2
    return FilterCoefficients(b=b_total, a=a_total, order=order)
