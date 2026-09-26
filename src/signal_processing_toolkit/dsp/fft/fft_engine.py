from __future__ import annotations

import numpy as np
from scipy import signal as sp_signal
from scipy.fft import fft, fftfreq, rfft, rfftfreq

from signal_processing_toolkit.models.fft_result import FFTResult
from signal_processing_toolkit.models.signal import Signal


def _prepare(
    signal: Signal, n_fft: int | None, window: str | tuple | np.ndarray | None
) -> tuple[np.ndarray, int, np.ndarray, float]:
    if signal.n_samples == 0:
        raise ValueError("Spectral analysis is undefined for an empty signal")
    n = signal.n_samples if n_fft is None else int(n_fft)
    if n <= 0:
        raise ValueError("n_fft must be positive")
    used = min(signal.n_samples, n)
    data = signal.time_data[:used]
    if window is None:
        weights = np.ones(used)
    elif isinstance(window, np.ndarray):
        weights = np.asarray(window, dtype=float)
        if weights.shape != (used,):
            raise ValueError(f"Window must have shape ({used},), got {weights.shape}")
    else:
        weights = sp_signal.get_window(window, used, fftbins=True)
    gain = float(np.sum(weights) / used)
    if np.isclose(gain, 0.0):
        raise ValueError("Window coherent gain is zero; amplitude correction is undefined")
    shaped = weights if data.ndim == 1 else weights[:, np.newaxis]
    return data * shaped, n, weights, gain


def _onesided_factors(n: int, bins: int) -> np.ndarray:
    factors = np.ones(bins)
    if bins > 1:
        factors[1:-1] = 2.0
        if n % 2:
            factors[-1] = 2.0
    return factors


def compute_fft(
    signal: Signal,
    n_fft: int | None = None,
    window: str | tuple | np.ndarray | None = None,
    *,
    one_sided: bool | None = None,
    db_reference: float = 1.0,
    db_floor: float = -300.0,
) -> FFTResult:
    """Compute amplitude and power spectra with coherent-gain correction.

    Real input defaults to ``rfft``. Interior one-sided bins are doubled;
    DC and the even-length Nyquist bin are not.
    """
    data, n, weights, gain = _prepare(signal, n_fft, window)
    use_one_sided = not signal.is_complex if one_sided is None else one_sided
    if use_one_sided and signal.is_complex:
        raise TypeError("A one-sided FFT requires real-valued input")
    if use_one_sided:
        raw = rfft(data, n=n, axis=Signal.SAMPLE_AXIS)
        frequencies = rfftfreq(n, 1.0 / signal.sampling_rate)
        factors = _onesided_factors(n, raw.shape[0])
    else:
        raw = fft(data, n=n, axis=Signal.SAMPLE_AXIS)
        frequencies = fftfreq(n, 1.0 / signal.sampling_rate)
        factors = np.ones(raw.shape[0])
    scale = factors if raw.ndim == 1 else factors[:, np.newaxis]
    amplitude = np.abs(raw) / np.sum(weights) * scale
    power = np.abs(raw) ** 2 / np.sum(weights) ** 2 * scale
    result = FFTResult(
        frequencies=frequencies,
        magnitude=amplitude,
        phase=np.angle(raw),
        n_points=n,
        sampling_rate=signal.sampling_rate,
        spectrum=raw,
        invertible=True,
        power=power,
        one_sided=use_one_sided,
        input_was_real=not signal.is_complex,
        window_coherent_gain=gain,
        db_reference=db_reference,
        db_floor=db_floor,
    )
    result.find_peaks(min_height=0.1 * float(np.max(amplitude)))
    return result


def compute_rfft(
    signal: Signal, n_fft: int | None = None, window: str | tuple | np.ndarray | None = None
) -> FFTResult:
    return compute_fft(signal, n_fft, window, one_sided=True)


def compute_power_spectrum(
    signal: Signal, n_fft: int | None = None, window: str | tuple | np.ndarray | None = None
) -> FFTResult:
    """Return a result whose calibrated per-bin power is ``result.power``."""
    return compute_fft(signal, n_fft, window)


def compute_periodogram(
    signal: Signal,
    n_fft: int | None = None,
    window: str | tuple | np.ndarray = "boxcar",
    *,
    scaling: str = "density",
) -> FFTResult:
    if signal.n_samples == 0:
        raise ValueError("Periodogram is undefined for an empty signal")
    n = signal.n_samples if n_fft is None else int(n_fft)
    freqs, values = sp_signal.periodogram(
        signal.time_data,
        fs=signal.sampling_rate,
        window=window,
        nfft=n,
        detrend=False,
        return_onesided=not signal.is_complex,
        scaling=scaling,
        axis=Signal.SAMPLE_AXIS,
    )
    result = compute_fft(signal, n, window, one_sided=not signal.is_complex)
    result.frequencies = freqs
    if scaling == "density":
        result.psd = values
    elif scaling == "spectrum":
        result.power = values
    else:
        raise ValueError("scaling must be 'density' or 'spectrum'")
    return result


def compute_welch_psd(
    signal: Signal,
    nperseg: int | None = None,
    *,
    n_fft: int | None = None,
    window: str | tuple | np.ndarray = "hann",
    overlap: int | None = None,
) -> FFTResult:
    if signal.n_samples == 0:
        raise ValueError("Welch PSD is undefined for an empty signal")
    segment = min(signal.n_samples, 256) if nperseg is None else int(nperseg)
    if segment <= 0 or segment > signal.n_samples:
        raise ValueError("nperseg must be in [1, signal.n_samples]")
    n = segment if n_fft is None else int(n_fft)
    if n < segment:
        raise ValueError("n_fft cannot be smaller than nperseg")
    freqs, density = sp_signal.welch(
        signal.time_data,
        fs=signal.sampling_rate,
        window=window,
        nperseg=segment,
        noverlap=overlap,
        nfft=n,
        detrend=False,
        return_onesided=not signal.is_complex,
        scaling="density",
        axis=Signal.SAMPLE_AXIS,
    )
    return FFTResult(
        frequencies=freqs,
        magnitude=np.sqrt(np.maximum(density, 0.0)),
        phase=np.zeros_like(density),
        n_points=n,
        sampling_rate=signal.sampling_rate,
        spectrum=np.zeros_like(density, dtype=complex),
        invertible=False,
        power=density * (signal.sampling_rate / n),
        psd=density,
        one_sided=not signal.is_complex,
        input_was_real=not signal.is_complex,
    )


def compute_psd(
    signal: Signal, n_fft: int | None = None, window: str | tuple | np.ndarray = "hann"
) -> FFTResult:
    segment = min(signal.n_samples, n_fft or 256)
    return compute_welch_psd(signal, segment, n_fft=n_fft, window=window)


def next_power_of_two(n: int) -> int:
    if n < 1:
        raise ValueError("n must be positive")
    return 1 << (n - 1).bit_length()


def compute_spectrogram(
    signal: Signal,
    n_fft: int = 256,
    hop_length: int | None = None,
    window: np.ndarray | str | tuple = "hann",
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    from signal_processing_toolkit.dsp.analysis.time_frequency import STFTConfig, stft

    hop = n_fft // 4 if hop_length is None else int(hop_length)
    if hop <= 0 or hop > n_fft:
        raise ValueError("hop_length must be in [1, n_fft]")
    result = stft(
        signal,
        STFTConfig(
            window=window,
            window_length=n_fft,
            overlap=n_fft - hop,
            fft_length=n_fft,
            scaling="spectrum",
            boundary=None,
            padded=False,
        ),
    )
    return result.frequencies, result.times, result.magnitude
