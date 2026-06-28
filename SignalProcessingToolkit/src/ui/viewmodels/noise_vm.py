from __future__ import annotations

from src.models.enums import NoiseType
from src.models.signal import Signal
from src.services.noise_service import NoiseService
from src.ui.viewmodels.base_viewmodel import BaseViewModel, Observable


class NoiseViewModel(BaseViewModel):
    def __init__(self, noise_service: NoiseService) -> None:
        super().__init__()
        self._service = noise_service

        self.input_signal = Observable[Signal | None](None)
        self.noise_type = Observable[NoiseType](NoiseType.WHITE)
        self.snr_db = Observable[float](20.0)
        self.noise_amplitude = Observable[float](0.1)
        self.removal_method = Observable[str]("moving_average")

        self.moving_avg_window = Observable[int](5)
        self.median_kernel = Observable[int](5)
        self.wiener_window = Observable[int](5)
        self.savgol_window = Observable[int](11)
        self.savgol_order = Observable[int](3)
        self.lms_mu = Observable[float](0.01)
        self.lms_length = Observable[int](32)

        self.generated_noise = Observable[Signal | None](None)
        self.noisy_signal = Observable[Signal | None](None)
        self.denoised_signal = Observable[Signal | None](None)
        self.snr_before = Observable[float](0.0)
        self.snr_after = Observable[float](0.0)
        self.noise_floor = Observable[float](0.0)
        self.status_message = Observable[str]("")

    def generate_noise_only(self) -> Signal | None:
        length = 44100
        signal = self._service.generate(
            self.noise_type.value, length, amplitude=self.noise_amplitude.value
        )
        self.generated_noise.value = signal
        self.status_message.value = f"Generated {self.noise_type.value} noise"
        return signal

    def add_noise_to_signal(self) -> Signal | None:
        signal = self.input_signal.value
        if signal is None:
            self.status_message.value = "No input signal"
            return None
        noisy = self._service.add_noise(
            signal,
            self.noise_type.value,
            snr_db=self.snr_db.value,
            amplitude=self.noise_amplitude.value,
        )
        self.noisy_signal.value = noisy
        self.snr_before.value = self.snr_db.value
        self.noise_floor.value = self._service.calculate_noise_floor(noisy)
        self.status_message.value = (
            f"Added {self.noise_type.value} noise at {self.snr_db.value:.1f} dB SNR"
        )
        return noisy

    def remove_noise(self) -> Signal | None:
        noisy = self.noisy_signal.value or self.input_signal.value
        if noisy is None:
            self.status_message.value = "No signal to denoise"
            return None

        method = self.removal_method.value
        if method == "moving_average":
            result = self._service.remove_moving_average(noisy, self.moving_avg_window.value)
        elif method == "median":
            result = self._service.remove_median(noisy, self.median_kernel.value)
        elif method == "wiener":
            result = self._service.remove_wiener(noisy, self.wiener_window.value)
        elif method == "savgol":
            result = self._service.remove_savgol(
                noisy, self.savgol_window.value, self.savgol_order.value
            )
        elif method == "adaptive_lms":
            noise_ref = self.generated_noise.value
            if noise_ref is None:
                self.status_message.value = "Generate noise reference first for LMS"
                return None
            result = self._service.adaptive_filter_lms(
                noisy, noise_ref, self.lms_mu.value, self.lms_length.value
            )
        else:
            self.status_message.value = f"Unknown method: {method}"
            return None

        self.denoised_signal.value = result
        clean = self.input_signal.value
        if clean is not None:
            self.snr_after.value = self._service.calculate_snr_from_clean(clean, result)
        self.status_message.value = f"Denoised using {method}"
        return result

    def dispose(self) -> None:
        super().dispose()
        self.generated_noise.value = None
        self.noisy_signal.value = None
        self.denoised_signal.value = None
