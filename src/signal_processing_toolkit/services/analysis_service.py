from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass

import numpy as np

from signal_processing_toolkit.dsp.analysis import (
    CepstrumResult,
    CrossSpectrumResult,
    EventDetectionConfig,
    EventDetectionResult,
    HarmonicMarker,
    PeakEstimate,
    STFTConfig,
    STFTResult,
    WaveletResult,
    band_power,
    continuous_wavelet_transform,
    cross_spectral_density,
    detect_events,
    detect_transients,
    envelope_spectrum,
    estimate_dominant_peak,
    harmonic_markers,
    instantaneous_frequency,
    magnitude_squared_coherence,
    real_cepstrum,
    signal_envelope,
    stft,
)
from signal_processing_toolkit.models.fft_result import FFTResult
from signal_processing_toolkit.models.signal import Signal


@dataclass(slots=True)
class AdvancedAnalysisResult:
    source: Signal
    selected_signal: Signal
    stft: STFTResult
    envelope: Signal
    instantaneous_frequency: Signal
    cepstrum: CepstrumResult
    envelope_spectrum: FFTResult
    wavelet: WaveletResult
    peak: PeakEstimate
    harmonics: list[HarmonicMarker]
    events: EventDetectionResult
    transients: EventDetectionResult
    cross_spectrum: CrossSpectrumResult | None
    coherence: CrossSpectrumResult | None
    measurements: dict[str, float]
    parameters: dict[str, object]


class AnalysisService:
    def select_region(self, signal: Signal, start_time: float, end_time: float) -> Signal:
        if not np.isfinite(start_time) or not np.isfinite(end_time) or start_time >= end_time:
            raise ValueError("Region must have finite, increasing time bounds")
        start = max(0, int(np.floor((start_time - signal.start_time) * signal.sampling_rate)))
        end = min(
            signal.n_samples, int(np.ceil((end_time - signal.start_time) * signal.sampling_rate))
        )
        if start >= end:
            raise ValueError("Selected region does not overlap the signal")
        return signal.updated(
            time_data=signal.time_data[start:end],
            start_time=signal.start_time + start / signal.sampling_rate,
            operation="select_analysis_region",
            parameters={"start_time": start_time, "end_time": end_time},
        )

    def analyze(
        self,
        signal: Signal,
        *,
        stft_config: STFTConfig,
        region: tuple[float, float] | None = None,
        wavelet_frequencies: np.ndarray | None = None,
        event_config: EventDetectionConfig | None = None,
        band: tuple[float, float] | None = None,
        max_harmonics: int = 10,
        comparison_signal: Signal | None = None,
        transient_prominence: float | None = None,
        transient_minimum_distance: float = 0.0,
        transient_smoothing: float = 0.001,
        cancellation_check: Callable[[], None] | None = None,
    ) -> AdvancedAnalysisResult:
        check = cancellation_check or (lambda: None)
        check()
        selected = signal if region is None else self.select_region(signal, *region)
        if selected.is_complex:
            raise ValueError("Envelope, cepstrum, and event analysis currently require real input")
        effective_window = min(stft_config.window_length, selected.n_samples)
        effective_overlap = min(stft_config.overlap, max(0, effective_window - 1))
        config = STFTConfig(
            window=stft_config.window,
            window_length=effective_window,
            overlap=effective_overlap,
            fft_length=max(stft_config.effective_fft_length, effective_window),
            scaling=stft_config.scaling,
            boundary=stft_config.boundary,
            padded=stft_config.padded,
            detrend=stft_config.detrend,
        )
        stft_result = stft(selected, config)
        check()
        envelope = signal_envelope(selected)
        instantaneous = instantaneous_frequency(selected)
        check()
        cepstrum = real_cepstrum(selected)
        envelope_result = envelope_spectrum(selected)
        if wavelet_frequencies is None:
            lower = max(selected.sampling_rate / selected.n_samples, 1.0)
            upper = selected.nyquist_frequency * 0.9
            wavelet_frequencies = np.geomspace(lower, upper, 48)
        wavelet = continuous_wavelet_transform(selected, frequencies=wavelet_frequencies)
        check()
        peak = estimate_dominant_peak(selected)
        markers = harmonic_markers(peak.frequency, selected.sampling_rate, max_harmonics)
        if event_config is None:
            threshold = float(np.mean(envelope.time_data) + 2 * np.std(envelope.time_data))
            event_config = EventDetectionConfig(threshold=threshold, direction="above")
        events = detect_events(envelope, event_config)
        if transient_prominence is None:
            envelope_values = np.asarray(envelope.time_data)
            slope = np.gradient(envelope_values, axis=Signal.SAMPLE_AXIS) * selected.sampling_rate
            transient_prominence = max(float(3 * np.std(slope)), np.finfo(float).eps)
        transients = detect_transients(
            selected,
            prominence=transient_prominence,
            minimum_distance=transient_minimum_distance,
            smoothing=transient_smoothing,
        )
        check()
        if band is None:
            half_width = max(
                2 * selected.sampling_rate / effective_window,
                peak.frequency * 0.05,
            )
            band = (
                max(0.0, peak.frequency - half_width),
                min(selected.nyquist_frequency, peak.frequency + half_width),
            )
        measured_power = band_power(selected, *band, segment_length=effective_window)
        measured_power_value = (
            float(np.mean(measured_power))
            if isinstance(measured_power, np.ndarray)
            else float(measured_power)
        )
        measurements = {
            "dominant_frequency_hz": peak.frequency,
            "dominant_magnitude": peak.magnitude,
            "band_low_hz": band[0],
            "band_high_hz": band[1],
            "band_power": measured_power_value,
            "event_count": float(len(events.events)),
            "transient_count": float(len(transients.events)),
            "region_start_s": selected.start_time,
            "region_end_s": selected.start_time + selected.duration,
        }
        cross_spectrum = None
        coherence = None
        if comparison_signal is not None:
            comparison = (
                comparison_signal
                if region is None
                else self.select_region(comparison_signal, *region)
            )
            selected.validate_compatibility(
                comparison,
                require_same_length=True,
                require_same_start=False,
                require_same_units=False,
            )
            cross_spectrum = cross_spectral_density(
                selected,
                comparison,
                segment_length=effective_window,
                overlap=effective_overlap,
                fft_length=config.effective_fft_length,
            )
            coherence = magnitude_squared_coherence(
                selected,
                comparison,
                segment_length=effective_window,
                overlap=effective_overlap,
                fft_length=config.effective_fft_length,
            )
            peak_bin = int(np.argmin(np.abs(coherence.frequencies - peak.frequency)))
            peak_coherence = coherence.values[peak_bin]
            measurements["coherence_at_dominant_frequency"] = float(np.mean(peak_coherence))
        parameters = {
            **config.parameters(),
            "wavelet": wavelet.parameters,
            "event_detection": events.parameters,
            "transient_detection": transients.parameters,
            "band_hz": band,
            "max_harmonics": max_harmonics,
            "comparison_signal_id": (
                None if comparison_signal is None else comparison_signal.metadata.id
            ),
        }
        return AdvancedAnalysisResult(
            signal,
            selected,
            stft_result,
            envelope,
            instantaneous,
            cepstrum,
            envelope_result,
            wavelet,
            peak,
            markers,
            events,
            transients,
            cross_spectrum,
            coherence,
            measurements,
            parameters,
        )
