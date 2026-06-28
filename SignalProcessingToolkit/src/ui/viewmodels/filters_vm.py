from __future__ import annotations

from src.models.enums import DesignMethod, FilterType, ResponseType
from src.models.filter_design import (
    FilterCoefficients,
    FilterDesign,
    FrequencyResponse,
    PoleZeroMap,
)
from src.models.signal import Signal
from src.services.filter_service import FilterService
from src.ui.viewmodels.base_viewmodel import BaseViewModel, Observable


class FilterViewModel(BaseViewModel):
    def __init__(self, filter_service: FilterService) -> None:
        super().__init__()
        self._service = filter_service

        self.filter_type = Observable[FilterType](FilterType.LOWPASS)
        self.response_type = Observable[ResponseType](ResponseType.IIR)
        self.design_method = Observable[DesignMethod](DesignMethod.BUTTERWORTH)
        self.order = Observable[int](4)
        self.cutoff_freq = Observable[float](1000.0)
        self.cutoff_freq2 = Observable[float](2000.0)
        self.sampling_rate = Observable[float](44100.0)
        self.passband_ripple = Observable[float](1.0)
        self.stopband_atten = Observable[float](40.0)
        self.input_signal = Observable[Signal | None](None)

        self.coefficients = Observable[FilterCoefficients | None](None)
        self.freq_response = Observable[FrequencyResponse | None](None)
        self.impulse_response = Observable[Signal | None](None)
        self.pole_zero = Observable[PoleZeroMap | None](None)
        self.filtered_signal = Observable[Signal | None](None)
        self.status_message = Observable[str]("")

    def design(self) -> FilterCoefficients | None:
        cutoff: float | tuple[float, float]
        if self.filter_type.value in (FilterType.BANDPASS, FilterType.BANDSTOP):
            cutoff = (self.cutoff_freq.value, self.cutoff_freq2.value)
        else:
            cutoff = self.cutoff_freq.value

        spec = FilterDesign(
            filter_type=self.filter_type.value,
            response_type=self.response_type.value,
            design_method=self.design_method.value,
            order=self.order.value,
            cutoff_frequency=cutoff,
            sampling_rate=self.sampling_rate.value,
            passband_ripple=self.passband_ripple.value,
            stopband_attenuation=self.stopband_atten.value,
        )

        coeffs = self._service.design(spec)
        fr = self._service.frequency_response(coeffs, spec.sampling_rate)
        ir = self._service.impulse_response(coeffs)
        pz = self._service.pole_zero(coeffs)

        self.coefficients.value = coeffs
        self.freq_response.value = fr
        self.impulse_response.value = ir
        self.pole_zero.value = pz
        self.status_message.value = (
            f"{self.response_type.value.name} {self.filter_type.value.value} "
            f"designed — order {spec.order}"
        )
        return coeffs

    def apply(self) -> Signal | None:
        signal = self.input_signal.value
        coeffs = self.coefficients.value
        if signal is None:
            self.status_message.value = "No input signal"
            return None
        if coeffs is None:
            self.status_message.value = "Design a filter first"
            return None
        result = self._service.apply(signal, coeffs)
        self.filtered_signal.value = result
        self.status_message.value = "Filter applied"
        return result

    def dispose(self) -> None:
        super().dispose()
        self.coefficients.value = None
        self.filtered_signal.value = None
