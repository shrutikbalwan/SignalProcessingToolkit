from __future__ import annotations

import numpy as np
from scipy import signal as sp_signal

from signal_processing_toolkit.models.enums import NoiseType
from signal_processing_toolkit.models.signal import Signal


class NoiseService:
    def generate(self, noise_type: NoiseType, length: int, **params) -> Signal:
        import numpy as np

        from signal_processing_toolkit.dsp.noise.generators import generate_noise

        data = generate_noise(noise_type, length, **params)
        return Signal(time_data=np.asarray(data, dtype=np.float64), sampling_rate=44100.0)

    def add_noise(
        self, signal: Signal, noise_type: NoiseType, snr_db: float = 20.0, **params
    ) -> Signal:
        noise = self.generate(noise_type, len(signal.time_data), **params)
        noise_data = noise.time_data
        if signal.time_data.ndim == 2:
            noise_data = np.repeat(noise_data[:, np.newaxis], signal.n_channels, axis=1)
        signal_power = np.mean(np.abs(signal.time_data) ** 2)
        noise_power = np.mean(np.abs(noise_data) ** 2)
        if noise_power == 0:
            return signal.copy()
        scaling = np.sqrt(signal_power / (noise_power * 10 ** (snr_db / 10)))
        return signal.updated(
            time_data=signal.time_data + noise_data * scaling,
            operation="add_noise",
            parameters={"type": noise_type.value, "snr_db": snr_db},
        )

    def calculate_snr(self, signal: Signal, noise: Signal) -> float:
        from signal_processing_toolkit.dsp.noise.metrics import snr_from_noise

        return snr_from_noise(signal, noise)

    def calculate_noise_floor(self, signal: Signal) -> float:
        return float(np.sqrt(np.mean(np.abs(signal.time_data) ** 2)))

    def calculate_snr_from_clean(self, clean: Signal, noisy: Signal) -> float:
        from signal_processing_toolkit.dsp.noise.metrics import snr_from_reference

        return snr_from_reference(noisy, clean)

    def remove_moving_average(self, signal: Signal, window_size: int = 5) -> Signal:
        window = np.ones(window_size) / window_size
        kernel = window if signal.is_mono else window[:, np.newaxis]
        filtered = sp_signal.convolve(signal.time_data, kernel, mode="same")
        return signal.updated(
            time_data=filtered,
            operation="remove_noise_moving_average",
            parameters={"window_size": window_size},
        )

    def remove_median(self, signal: Signal, kernel_size: int = 5) -> Signal:
        size = kernel_size if signal.is_mono else (kernel_size, 1)
        filtered = sp_signal.medfilt(signal.time_data, size)
        return signal.updated(
            time_data=filtered,
            operation="remove_noise_median",
            parameters={"kernel_size": kernel_size},
        )

    def remove_wiener(self, signal: Signal, window_size: int = 5) -> Signal:
        size = window_size if signal.is_mono else (window_size, 1)
        filtered = sp_signal.wiener(signal.time_data, size)
        return signal.updated(
            time_data=filtered,
            operation="remove_noise_wiener",
            parameters={"window_size": window_size},
        )

    def remove_savgol(self, signal: Signal, window_length: int = 11, polyorder: int = 3) -> Signal:
        filtered = sp_signal.savgol_filter(
            signal.time_data, window_length, polyorder, axis=Signal.SAMPLE_AXIS
        )
        return signal.updated(
            time_data=filtered,
            operation="remove_noise_savgol",
            parameters={"window_length": window_length, "polyorder": polyorder},
        )

    def adaptive_filter_lms(
        self, signal: Signal, noise_ref: Signal, mu: float = 0.01, filter_length: int = 32
    ) -> Signal:
        signal.validate_compatibility(noise_ref)
        if not signal.is_mono:
            raise ValueError("Adaptive LMS currently requires mono signals")
        n = len(signal.time_data)
        w = np.zeros(filter_length)
        output = np.zeros(n)
        min_len = min(n, len(noise_ref.time_data))
        for i in range(filter_length, min_len):
            x = noise_ref.time_data[i - filter_length : i][::-1]
            y = np.dot(w, x)
            e = signal.time_data[i] - y
            w += 2 * mu * e * x
            output[i] = e
        return signal.updated(
            time_data=output,
            operation="remove_noise_lms",
            parameters={"mu": mu, "filter_length": filter_length},
        )
