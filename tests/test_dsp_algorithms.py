from __future__ import annotations

import numpy as np
import pytest
from hypothesis import given
from hypothesis import strategies as st
from scipy import signal as sp_signal

from signal_processing_toolkit.dsp.convolution import (
    overlap_add_convolve,
    overlap_save_convolve,
)
from signal_processing_toolkit.dsp.fft import (
    compute_fft,
    compute_periodogram,
    compute_welch_psd,
    inverse_fft,
)
from signal_processing_toolkit.dsp.filters import design_fir_filter
from signal_processing_toolkit.dsp.filters.design import (
    StatefulFilter,
    apply_causal,
    apply_zero_phase,
)
from signal_processing_toolkit.dsp.noise.metrics import (
    crest_factor,
    enob,
    psnr,
    sinad,
    snr_from_reference,
    thd,
    thdn,
)
from signal_processing_toolkit.dsp.sampling import rational_resample, resample_signal
from signal_processing_toolkit.models.enums import DesignMethod, FilterType, ResponseType
from signal_processing_toolkit.models.filter_design import FilterDesign
from signal_processing_toolkit.models.signal import Signal
from signal_processing_toolkit.services.convolution_service import ConvolutionService
from signal_processing_toolkit.services.correlation_service import CorrelationService
from signal_processing_toolkit.services.filter_service import FilterService
from signal_processing_toolkit.services.sampling_service import SamplingService


@pytest.mark.parametrize("size", [999, 1000])
def test_real_fft_scaling_even_and_odd(size: int) -> None:
    rate = float(size)
    time = np.arange(size) / rate
    result = compute_fft(Signal(2.5 * np.cos(2 * np.pi * 100 * time), rate))
    assert result.one_sided
    assert result.bin_count == size // 2 + 1
    assert result.frequency_resolution == pytest.approx(1.0)
    assert result.magnitude[100] == pytest.approx(2.5, rel=1e-12)
    assert result.total_power == pytest.approx(2.5**2 / 2, rel=1e-12)


def test_dc_nyquist_and_window_coherent_gain() -> None:
    size = 1024
    nyquist = Signal(3.0 * (-1.0) ** np.arange(size), 1024.0)
    result = compute_fft(nyquist)
    assert result.has_nyquist_bin
    assert result.magnitude[-1] == pytest.approx(3.0)
    dc = compute_fft(Signal(np.full(size, 4.0), 1024.0), window="hann")
    assert dc.magnitude[0] == pytest.approx(4.0)
    assert dc.window_coherent_gain == pytest.approx(0.5)
    assert dc.to_db(np.array([2.0]), reference=2.0)[0] == pytest.approx(0.0)
    assert dc.to_db(np.array([0.0]), floor_db=-120.0)[0] == -120.0


def test_periodogram_and_welch_match_scipy(noise_signal: Signal) -> None:
    periodogram = compute_periodogram(noise_signal, window="hann")
    frequency, expected = sp_signal.periodogram(
        noise_signal.time_data,
        fs=noise_signal.sampling_rate,
        window="hann",
        detrend=False,
    )
    np.testing.assert_allclose(periodogram.frequencies, frequency)
    np.testing.assert_allclose(periodogram.psd, expected)
    welch = compute_welch_psd(noise_signal, 512, overlap=256)
    frequency, expected = sp_signal.welch(
        noise_signal.time_data,
        fs=noise_signal.sampling_rate,
        window="hann",
        nperseg=512,
        noverlap=256,
        detrend=False,
    )
    np.testing.assert_allclose(welch.frequencies, frequency)
    np.testing.assert_allclose(welch.psd, expected)
    with pytest.raises(ValueError, match="does not contain an invertible FFT"):
        inverse_fft(welch)


def test_fft_retains_exact_spectrum_for_real_and_complex(sine_signal: Signal) -> None:
    reconstructed = inverse_fft(compute_fft(sine_signal))
    np.testing.assert_allclose(reconstructed.time_data, sine_signal.time_data, atol=1e-12)
    complex_signal = Signal(np.exp(2j * np.pi * 17 * np.arange(128) / 128), 128.0)
    complex_result = compute_fft(complex_signal)
    assert not complex_result.one_sided
    np.testing.assert_allclose(inverse_fft(complex_result).time_data, complex_signal.time_data)
    positive = complex_result.positive_spectrum
    assert not positive.invertible
    with pytest.raises(ValueError, match="does not contain an invertible FFT"):
        inverse_fft(positive)


def test_decimation_rejects_alias_and_polyphase_matches_scipy() -> None:
    rate = 1000.0
    time = np.arange(1000) / rate
    out_of_band = Signal(np.sin(2 * np.pi * 400 * time), rate)
    down = SamplingService().downsample(out_of_band, 2)
    assert down.n_samples == 500
    assert np.sqrt(np.mean(down.time_data[30:-30] ** 2)) < 0.02
    data = np.random.default_rng(7).normal(size=(101, 2))
    signal = Signal(data, 48000.0, channel_names=("L", "R"))
    converted = rational_resample(signal, 2, 3)
    np.testing.assert_allclose(converted.time_data, sp_signal.resample_poly(data, 2, 3, axis=0))
    assert converted.n_samples == 68


def test_resampling_preserves_tone_frequency() -> None:
    rate = 1000.0
    time = np.arange(1000) / rate
    converted = resample_signal(Signal(np.sin(2 * np.pi * 100 * time), rate), 1600.0)
    result = compute_fft(converted)
    assert result.dominant_frequency == pytest.approx(100.0)
    with pytest.raises(ValueError, match="positive integer"):
        rational_resample(converted, 0, 1)


def _high_order_filter() -> tuple[FilterService, object]:
    service = FilterService()
    coefficients = service.design(
        FilterDesign(
            FilterType.LOWPASS,
            ResponseType.IIR,
            DesignMethod.BUTTERWORTH,
            12,
            100.0,
            1000.0,
        )
    )
    return service, coefficients


def test_high_order_iir_uses_stable_sos() -> None:
    service, coefficients = _high_order_filter()
    assert coefficients.sos is not None
    stable, radius = service.stability(coefficients)
    assert stable
    assert radius < 1.0
    with pytest.raises(ValueError, match="Cutoff frequencies"):
        FilterDesign(
            FilterType.LOWPASS,
            ResponseType.IIR,
            DesignMethod.BUTTERWORTH,
            4,
            500.0,
            1000.0,
        )


def test_chunked_causal_filter_equals_single_pass(noise_signal: Signal) -> None:
    _, coefficients = _high_order_filter()
    expected = apply_causal(noise_signal, coefficients).time_data
    streaming = StatefulFilter(coefficients)
    chunks = [
        streaming.process(noise_signal.updated(time_data=chunk)).time_data
        for chunk in np.array_split(noise_signal.time_data, 7)
    ]
    np.testing.assert_allclose(np.concatenate(chunks), expected, atol=1e-12)
    streaming.reset()
    restarted = streaming.process(noise_signal).time_data
    np.testing.assert_allclose(restarted, expected)


def test_zero_phase_short_signal_has_explicit_error() -> None:
    _, coefficients = _high_order_filter()
    with pytest.raises(ValueError, match="causal filtering"):
        apply_zero_phase(Signal(np.ones(10), 1000.0), coefficients)


def test_unequal_correlation_lags_normalization_and_rate_validation() -> None:
    first = Signal(np.array([1.0, 2.0, 3.0]), 10.0)
    second = Signal(np.array([2.0, -1.0]), 10.0)
    service = CorrelationService()
    raw = service.cross_correlation(first, second, normalize=False)
    np.testing.assert_array_equal(raw.lags, sp_signal.correlation_lags(3, 2))
    np.testing.assert_allclose(raw.values, sp_signal.correlate(first.time_data, second.time_data))
    normalized = service.cross_correlation(first, second)
    expected = raw.values / np.sqrt(np.sum(first.time_data**2) * np.sum(second.time_data**2))
    np.testing.assert_allclose(normalized.values, expected)
    with pytest.raises(ValueError, match="Sampling rate mismatch"):
        service.cross_correlation(first, Signal(second.time_data, 20.0))


def test_convolution_origin_and_values() -> None:
    first = Signal(np.array([1.0, 2.0]), 10.0, start_time=0.2)
    second = Signal(np.array([3.0, 4.0, 5.0]), 10.0, start_time=-0.1)
    result = ConvolutionService().linear(first, second)
    np.testing.assert_allclose(
        result.time_data, sp_signal.convolve(first.time_data, second.time_data)
    )
    assert result.start_time == pytest.approx(0.1)


@pytest.mark.parametrize("block_size", [1, 7, 64])
def test_overlap_block_convolution_matches_scipy(block_size: int) -> None:
    rng = np.random.default_rng(block_size)
    first_data = rng.normal(size=(137, 2))
    second_data = rng.normal(size=(19, 2))
    first = Signal(first_data, 1000.0, channel_names=("L", "R"))
    second = Signal(second_data, 1000.0, channel_names=("L", "R"))
    expected = np.column_stack(
        [
            sp_signal.convolve(first_data[:, channel], second_data[:, channel])
            for channel in range(2)
        ]
    )
    added = overlap_add_convolve(first, second, block_size)
    saved = overlap_save_convolve(first, second, block_size)
    np.testing.assert_allclose(added.time_data, expected, atol=1e-11)
    np.testing.assert_allclose(saved.time_data, expected, atol=1e-11)


def test_fir_window_selection_is_honored() -> None:
    boxcar = design_fir_filter(
        FilterDesign(
            FilterType.LOWPASS,
            ResponseType.FIR,
            DesignMethod.WINDOW,
            20,
            100.0,
            1000.0,
            window="boxcar",
        )
    )
    hamming = design_fir_filter(
        FilterDesign(
            FilterType.LOWPASS,
            ResponseType.FIR,
            DesignMethod.WINDOW,
            20,
            100.0,
            1000.0,
            window="hamming",
        )
    )
    assert not np.allclose(boxcar.b, hamming.b)


def test_measurement_formulas() -> None:
    rate = 4096.0
    time = np.arange(4096) / rate
    clean = Signal(np.sin(2 * np.pi * 64 * time), rate)
    harmonic = 0.1 * np.sin(2 * np.pi * 128 * time)
    measured = Signal(clean.time_data + harmonic, rate)
    assert snr_from_reference(measured, clean) == pytest.approx(20.0)
    assert psnr(measured, clean) == pytest.approx(23.0102999566)
    assert thd(measured, 64.0) == pytest.approx(10.0)
    assert thdn(measured, 64.0) == pytest.approx(10.0)
    assert sinad(measured, 64.0) == pytest.approx(20.0)
    assert enob(measured, 64.0) == pytest.approx((20.0 - 1.76) / 6.02)
    assert crest_factor(clean) == pytest.approx(np.sqrt(2.0))


@given(
    size=st.integers(min_value=2, max_value=300),
    up=st.integers(min_value=1, max_value=8),
    down=st.integers(min_value=1, max_value=8),
)
def test_polyphase_output_length_invariant(size: int, up: int, down: int) -> None:
    signal = Signal(np.arange(size, dtype=float), 1000.0)
    result = rational_resample(signal, up, down)
    gcd = int(np.gcd(up, down))
    expected = (size * (up // gcd) + (down // gcd) - 1) // (down // gcd)
    assert result.n_samples == expected


@given(size=st.integers(min_value=2, max_value=256))
def test_fft_power_obeys_parseval(size: int) -> None:
    data = np.random.default_rng(size).normal(size=size)
    result = compute_fft(Signal(data, 1000.0))
    assert result.total_power == pytest.approx(float(np.mean(data**2)), rel=1e-12)
