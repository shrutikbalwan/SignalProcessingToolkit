from __future__ import annotations

import time

import numpy as np
import pytest
from scipy import signal as sp_signal

from signal_processing_toolkit.dsp.analysis import (
    EventDetectionConfig,
    STFTConfig,
    StreamingSpectrogram,
    band_power,
    continuous_wavelet_transform,
    cross_spectral_density,
    detect_events,
    detect_transients,
    envelope_spectrum,
    estimate_dominant_peak,
    harmonic_markers,
    instantaneous_frequency,
    istft,
    magnitude_squared_coherence,
    real_cepstrum,
    signal_envelope,
    stft,
)
from signal_processing_toolkit.models.signal import Signal


@pytest.mark.parametrize(
    ("window", "overlap", "fft_length", "boundary", "scaling"),
    [
        ("hann", 128, 256, "zeros", "spectrum"),
        ("hamming", 192, 512, "even", "psd"),
    ],
)
def test_stft_istft_reconstruction(
    noise_signal: Signal,
    window: str,
    overlap: int,
    fft_length: int,
    boundary: str,
    scaling: str,
) -> None:
    config = STFTConfig(
        window=window,
        window_length=256,
        overlap=overlap,
        fft_length=fft_length,
        boundary=boundary,  # type: ignore[arg-type]
        scaling=scaling,  # type: ignore[arg-type]
        padded=True,
    )
    result = stft(noise_signal, config)
    reconstructed = istft(result)
    relative_error = np.linalg.norm(
        reconstructed.time_data - noise_signal.time_data
    ) / np.linalg.norm(noise_signal.time_data)
    assert relative_error < 1e-12
    assert result.parameters["fft_length"] == fft_length


def test_multichannel_stft_shape_and_reconstruction() -> None:
    rate = 1000.0
    time_axis = np.arange(1000) / rate
    source = Signal(
        np.column_stack((np.sin(2 * np.pi * 50 * time_axis), np.cos(2 * np.pi * 120 * time_axis))),
        rate,
        channel_names=("left", "right"),
    )
    result = stft(source, STFTConfig(window_length=128, overlap=64, fft_length=256))
    assert result.spectrum.ndim == 3
    assert result.spectrum.shape[2] == 2
    reconstructed = istft(result)
    assert reconstructed.shape == source.shape
    np.testing.assert_allclose(reconstructed.time_data, source.time_data, atol=1e-12)


def test_streaming_spectrogram_matches_complete_frames(noise_signal: Signal) -> None:
    config = STFTConfig(window_length=128, overlap=96, fft_length=256, boundary=None, padded=False)
    expected = stft(noise_signal, config)
    streaming = StreamingSpectrogram(noise_signal.sampling_rate, config)
    outputs = []
    for chunk in np.array_split(noise_signal.time_data, 13):
        result = streaming.push(Signal(chunk, noise_signal.sampling_rate))
        if result is not None:
            outputs.append(result.spectrum)
    actual = np.concatenate(outputs, axis=1)
    np.testing.assert_allclose(actual, expected.spectrum)


def test_cross_spectrum_matches_scipy() -> None:
    rate = 2048.0
    rng = np.random.default_rng(10)
    first = Signal(rng.normal(size=4096), rate)
    second = Signal(sp_signal.lfilter([1.0, 0.5], [1.0], first.time_data), rate)
    result = cross_spectral_density(first, second, segment_length=512, overlap=256)
    frequencies, expected = sp_signal.csd(
        first.time_data,
        second.time_data,
        fs=rate,
        window="hann",
        nperseg=512,
        noverlap=256,
        detrend=False,
    )
    np.testing.assert_allclose(result.frequencies, frequencies)
    np.testing.assert_allclose(result.values, expected)


def test_coherence_distinguishes_correlated_and_uncorrelated_inputs() -> None:
    rate = 2048.0
    time_axis = np.arange(16384) / rate
    rng = np.random.default_rng(42)
    shared = np.sin(2 * np.pi * 200 * time_axis)
    first = Signal(shared + 0.3 * rng.normal(size=time_axis.size), rate)
    correlated = Signal(shared + 0.3 * rng.normal(size=time_axis.size), rate)
    unrelated = Signal(rng.normal(size=time_axis.size), rate)
    related_result = magnitude_squared_coherence(first, correlated, segment_length=512)
    unrelated_result = magnitude_squared_coherence(first, unrelated, segment_length=512)
    tone_bin = int(np.argmin(np.abs(related_result.frequencies - 200)))
    assert related_result.values[tone_bin] > 0.9
    assert float(np.mean(unrelated_result.values[1:])) < 0.15


def test_envelope_and_envelope_spectrum_recover_amplitude_modulation() -> None:
    rate = 4000.0
    time_axis = np.arange(8000) / rate
    expected_envelope = 1.0 + 0.4 * np.sin(2 * np.pi * 7 * time_axis)
    modulated = Signal(expected_envelope * np.cos(2 * np.pi * 400 * time_axis), rate)
    recovered = signal_envelope(modulated)
    assert np.corrcoef(recovered.time_data[100:-100], expected_envelope[100:-100])[0, 1] > 0.999
    spectrum = envelope_spectrum(modulated)
    assert spectrum.dominant_frequency == pytest.approx(7.0, abs=0.5)


def test_instantaneous_frequency_recovers_linear_chirp(chirp_signal: Signal) -> None:
    recovered = instantaneous_frequency(chirp_signal).time_data
    expected = np.linspace(20, 700, chirp_signal.n_samples)
    assert np.median(np.abs(recovered[100:-100] - expected[100:-100])) < 2.0


def test_cepstrum_detects_echo_delay() -> None:
    rate = 4000.0
    rng = np.random.default_rng(123)
    source = rng.normal(size=8000)
    delay = 80
    echoed = source.copy()
    echoed[delay:] += 0.7 * source[:-delay]
    result = real_cepstrum(Signal(echoed, rate))
    search = np.abs(result.values[10:200])
    detected = int(np.argmax(search) + 10)
    assert detected == pytest.approx(delay, abs=1)


def test_wavelet_localizes_transient() -> None:
    rate = 1000.0
    time_axis = np.arange(2000) / rate
    carrier = np.sin(2 * np.pi * 100 * time_axis)
    burst = carrier * np.exp(-0.5 * ((time_axis - 0.8) / 0.025) ** 2)
    result = continuous_wavelet_transform(Signal(burst, rate), frequencies=np.array([100.0]))
    detected_time = result.times[int(np.argmax(result.scalogram[0]))]
    assert detected_time == pytest.approx(0.8, abs=0.02)


def test_band_power_peak_harmonics_and_events() -> None:
    rate = 1000.0
    time_axis = np.arange(4000) / rate
    signal = Signal(2 * np.sin(2 * np.pi * 51.37 * time_axis), rate)
    measured = band_power(signal, 45, 58, segment_length=1000)
    assert measured == pytest.approx(2.0, rel=0.03)
    peak = estimate_dominant_peak(signal, fft_length=8192)
    assert peak.frequency == pytest.approx(51.37, abs=0.03)
    markers = harmonic_markers(peak.frequency, rate, 12)
    assert markers[0].frequency == pytest.approx(peak.frequency)
    assert markers[-1].in_band is False
    pulse = np.zeros(1000)
    pulse[200:240] = 3.0
    pulse[700:780] = 4.0
    events = detect_events(
        Signal(pulse, rate),
        EventDetectionConfig(2.0, minimum_duration=0.02, minimum_distance=0.1),
    )
    assert [event.peak_index for event in events.events] == [200, 700]


def test_transient_detection_is_configurable() -> None:
    rate = 2000.0
    time_axis = np.arange(2000) / rate
    pulse = np.exp(-0.5 * ((time_axis - 0.5) / 0.004) ** 2)
    result = detect_transients(
        Signal(pulse, rate), prominence=20.0, minimum_distance=0.1, smoothing=0.001
    )
    assert len(result.events) == 1
    assert result.events[0].peak_time == pytest.approx(0.49, abs=0.02)
    assert result.parameters["prominence"] == 20.0


@pytest.mark.slow
def test_large_stft_performance() -> None:
    source = Signal(np.random.default_rng(4).normal(size=1_000_000), 48000.0)
    started = time.perf_counter()
    result = stft(
        source,
        STFTConfig(window_length=2048, overlap=1536, fft_length=2048, boundary=None, padded=False),
    )
    elapsed = time.perf_counter() - started
    assert result.spectrum.shape[1] > 1900
    assert elapsed < 10.0
