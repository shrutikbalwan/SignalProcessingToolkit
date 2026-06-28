from __future__ import annotations

import numpy as np
from scipy import signal as sp_signal

from src.models.enums import NoiseType
from src.models.signal import Signal


class NoiseService:
    def generate(self, noise_type: NoiseType, length: int, **params) -> Signal:
        import numpy as np

        from src.dsp.noise.generators import generate_noise

        data = generate_noise(noise_type, length, **params)
        return Signal(time_data=np.asarray(data, dtype=np.float64), sampling_rate=44100.0)

    def add_noise(
        self, signal: Signal, noise_type: NoiseType, snr_db: float = 20.0, **params
    ) -> Signal:
        noise = self.generate(noise_type, len(signal.time_data), **params)
        signal_power = np.mean(signal.time_data**2)
        noise_power = np.mean(noise.time_data**2)
        if noise_power == 0:
            return signal.copy()
        scaling = np.sqrt(signal_power / (noise_power * 10 ** (snr_db / 10)))
        noise_scaled = Signal(
            time_data=noise.time_data * scaling,
            sampling_rate=signal.sampling_rate,
        )
        return Signal(
            time_data=signal.time_data + noise_scaled.time_data,
            sampling_rate=signal.sampling_rate,
        )

    def calculate_snr(self, signal: Signal, noise: Signal) -> float:
        signal_power = np.mean(signal.time_data**2)
        noise_power = np.mean(noise.time_data**2)
        if noise_power == 0:
            return float("inf")
        return float(10 * np.log10(signal_power / noise_power))

    def calculate_noise_floor(self, signal: Signal) -> float:
        return float(np.sqrt(np.mean(signal.time_data**2)))

    def calculate_snr_from_clean(self, clean: Signal, noisy: Signal) -> float:
        noise = Signal(
            time_data=noisy.time_data - clean.time_data[: len(noisy.time_data)],
            sampling_rate=noisy.sampling_rate,
        )
        return self.calculate_snr(clean, noise)

    def remove_moving_average(self, signal: Signal, window_size: int = 5) -> Signal:
        window = np.ones(window_size) / window_size
        filtered = np.convolve(signal.time_data, window, mode="same")
        return Signal(time_data=filtered, sampling_rate=signal.sampling_rate)

    def remove_median(self, signal: Signal, kernel_size: int = 5) -> Signal:
        filtered = sp_signal.medfilt(signal.time_data, kernel_size)
        return Signal(time_data=filtered, sampling_rate=signal.sampling_rate)

    def remove_wiener(self, signal: Signal, window_size: int = 5) -> Signal:
        filtered = sp_signal.wiener(signal.time_data, window_size)
        return Signal(time_data=filtered, sampling_rate=signal.sampling_rate)

    def remove_savgol(self, signal: Signal, window_length: int = 11, polyorder: int = 3) -> Signal:
        filtered = sp_signal.savgol_filter(signal.time_data, window_length, polyorder)
        return Signal(time_data=filtered, sampling_rate=signal.sampling_rate)

    def adaptive_filter_lms(
        self, signal: Signal, noise_ref: Signal, mu: float = 0.01, filter_length: int = 32
    ) -> Signal:
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
        return Signal(time_data=output, sampling_rate=signal.sampling_rate)
