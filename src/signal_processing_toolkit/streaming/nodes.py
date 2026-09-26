from __future__ import annotations

from collections.abc import Mapping
from fractions import Fraction
from typing import Any

import numpy as np
from scipy import signal as sp_signal

from signal_processing_toolkit.dsp.fft import compute_fft, compute_welch_psd
from signal_processing_toolkit.models.signal import Signal
from signal_processing_toolkit.streaming.interfaces import StatelessNode, StreamSink
from signal_processing_toolkit.streaming.model import StreamChunk


def _signal(chunk: StreamChunk) -> Signal:
    return Signal(
        chunk.samples,
        chunk.sampling_rate,
        channel_names=tuple(channel.name for channel in chunk.channels),
        units=tuple(channel.unit for channel in chunk.channels),
        start_time=chunk.device_timestamp,
    )


class GainNode(StatelessNode):
    def __init__(self, gain: float = 1.0) -> None:
        self.gain = float(gain)
        self.configure()

    def configure(self, settings: Mapping[str, Any] | None = None) -> None:
        if settings and "gain" in settings:
            self.gain = float(settings["gain"])
        if not np.isfinite(self.gain):
            raise ValueError("gain must be finite")

    def process(self, chunk: StreamChunk) -> StreamChunk:
        return chunk.with_samples(
            chunk.samples * self.gain,
            attributes={"gain": self.gain},
        )


class RecorderNode(StatelessNode):
    """Record a raw stream before returning each unmodified chunk."""

    def __init__(self, recorder: StreamSink) -> None:
        self.recorder = recorder

    def process(self, chunk: StreamChunk) -> StreamChunk:
        self.recorder.consume(chunk)
        return chunk

    def reset(self) -> None:
        self.recorder.reset()

    def close(self) -> None:
        self.recorder.close()


class DCRemovalNode:
    """Stateful first-order DC blocker, continuous across chunk boundaries."""

    def __init__(self, cutoff_frequency: float = 5.0) -> None:
        self.cutoff_frequency = float(cutoff_frequency)
        self._rate: float | None = None
        self._state: np.ndarray | None = None
        self.configure()

    def configure(self, settings: Mapping[str, Any] | None = None) -> None:
        if settings and "cutoff_frequency" in settings:
            self.cutoff_frequency = float(settings["cutoff_frequency"])
        if not np.isfinite(self.cutoff_frequency) or self.cutoff_frequency <= 0:
            raise ValueError("cutoff_frequency must be finite and positive")
        self.reset()

    def process(self, chunk: StreamChunk) -> StreamChunk:
        if self.cutoff_frequency >= chunk.sampling_rate / 2:
            raise ValueError("DC-removal cutoff must be below Nyquist")
        if self._rate is not None and not np.isclose(self._rate, chunk.sampling_rate):
            raise ValueError("sampling rate changed without resetting DCRemovalNode")
        self._rate = chunk.sampling_rate
        alpha = float(np.exp(-2.0 * np.pi * self.cutoff_frequency / chunk.sampling_rate))
        channel_shape = () if chunk.samples.ndim == 1 else (chunk.channel_count,)
        if self._state is None:
            self._state = np.zeros((1, *channel_shape), dtype=np.result_type(chunk.samples, float))
        values, self._state = sp_signal.lfilter(
            np.array([1.0, -1.0]),
            np.array([1.0, -alpha]),
            chunk.samples,
            axis=0,
            zi=self._state,
        )
        return chunk.with_samples(
            values,
            attributes={"dc_removal_cutoff_hz": self.cutoff_frequency},
        )

    def reset(self) -> None:
        self._rate = None
        self._state = None

    def flush(self) -> StreamChunk | None:
        return None


class SOSFilterNode:
    """Causal SOS filter with independent delay state for every channel."""

    def __init__(self, sos: np.ndarray) -> None:
        self.sos = np.asarray(sos, dtype=float)
        self._state: np.ndarray | None = None
        self.configure()

    def configure(self, settings: Mapping[str, Any] | None = None) -> None:
        if settings and "sos" in settings:
            self.sos = np.asarray(settings["sos"], dtype=float)
        if self.sos.ndim != 2 or self.sos.shape[1] != 6 or not np.all(np.isfinite(self.sos)):
            raise ValueError("sos must be a finite array with shape (sections, 6)")
        _, poles, _ = sp_signal.sos2zpk(self.sos)
        if np.any(np.abs(poles) >= 1.0):
            raise ValueError("SOS filter must be stable for real-time processing")
        self.reset()

    def process(self, chunk: StreamChunk) -> StreamChunk:
        channel_shape = () if chunk.samples.ndim == 1 else (chunk.channel_count,)
        if self._state is None:
            self._state = np.zeros(
                (len(self.sos), 2, *channel_shape),
                dtype=np.result_type(chunk.samples, float),
            )
        values, self._state = sp_signal.sosfilt(self.sos, chunk.samples, axis=0, zi=self._state)
        return chunk.with_samples(values, attributes={"filter": "causal_sos"})

    def reset(self) -> None:
        self._state = None

    def flush(self) -> StreamChunk | None:
        return None


class ResamplerNode:
    """Bounded-state causal rational FIR sample-rate converter.

    The anti-alias/reconstruction filter runs at the upsampled rate. Unlike
    zero-phase offline ``resample_poly``, this streaming converter retains its
    causal group delay and never needs future samples.
    """

    def __init__(self, output_rate: float, *, taps_per_phase: int = 10) -> None:
        self.output_rate = float(output_rate)
        self.taps_per_phase = int(taps_per_phase)
        self._input_rate: float | None = None
        self._up = 1
        self._down = 1
        self._taps = np.ones(1)
        self._state: np.ndarray | None = None
        self._upsampled_count = 0
        self._last_chunk: StreamChunk | None = None
        self._flushed = False
        self.configure()

    def configure(self, settings: Mapping[str, Any] | None = None) -> None:
        if settings and "output_rate" in settings:
            self.output_rate = float(settings["output_rate"])
        if not np.isfinite(self.output_rate) or self.output_rate <= 0:
            raise ValueError("output_rate must be finite and positive")
        if self.taps_per_phase < 1:
            raise ValueError("taps_per_phase must be positive")
        self.reset()

    def _design(self, input_rate: float) -> None:
        ratio = Fraction(self.output_rate / input_rate).limit_denominator(100_000)
        achieved = input_rate * ratio.numerator / ratio.denominator
        if not np.isclose(achieved, self.output_rate, rtol=1e-10, atol=1e-12):
            raise ValueError("output/input rate ratio cannot be represented accurately")
        self._up, self._down = ratio.numerator, ratio.denominator
        factor = max(self._up, self._down)
        half_length = self.taps_per_phase * factor
        self._taps = sp_signal.firwin(2 * half_length + 1, 1.0 / factor) * self._up
        self._input_rate = input_rate

    def process(self, chunk: StreamChunk) -> StreamChunk:
        if self._flushed:
            raise RuntimeError("Reset ResamplerNode before processing after flush")
        self._last_chunk = chunk
        if self._input_rate is None:
            self._design(chunk.sampling_rate)
        elif not np.isclose(self._input_rate, chunk.sampling_rate):
            raise ValueError("input sampling rate changed without resetting ResamplerNode")
        if self._up == self._down == 1:
            return chunk.with_samples(chunk.samples.copy(), sampling_rate=self.output_rate)
        count = chunk.sample_count * self._up
        shape = (count,) if chunk.samples.ndim == 1 else (count, chunk.channel_count)
        expanded = np.zeros(shape, dtype=np.result_type(chunk.samples, float))
        expanded[:: self._up] = chunk.samples
        channel_shape = () if expanded.ndim == 1 else (chunk.channel_count,)
        if self._state is None:
            self._state = np.zeros((len(self._taps) - 1, *channel_shape), dtype=expanded.dtype)
        filtered, self._state = sp_signal.lfilter(
            self._taps, np.array([1.0]), expanded, axis=0, zi=self._state
        )
        first = (-self._upsampled_count) % self._down
        output = filtered[first :: self._down]
        self._upsampled_count += count
        return chunk.with_samples(
            output,
            sampling_rate=self.output_rate,
            attributes={
                "resample_up": self._up,
                "resample_down": self._down,
                "causal_group_delay_input_samples": (len(self._taps) - 1) / (2 * self._up),
            },
        )

    def reset(self) -> None:
        self._input_rate = None
        self._state = None
        self._upsampled_count = 0
        self._last_chunk = None
        self._flushed = False

    def flush(self) -> StreamChunk | None:
        """Emit the finite causal FIR tail once at end of stream."""
        if self._flushed or self._last_chunk is None or self._state is None:
            return None
        self._flushed = True
        if self._up == self._down == 1:
            return None
        last = self._last_chunk
        count = len(self._taps) - 1
        shape = (count,) if last.samples.ndim == 1 else (count, last.channel_count)
        zeros = np.zeros(shape, dtype=self._state.dtype)
        filtered, self._state = sp_signal.lfilter(
            self._taps, np.array([1.0]), zeros, axis=0, zi=self._state
        )
        first = (-self._upsampled_count) % self._down
        output = filtered[first :: self._down]
        self._upsampled_count += count
        return StreamChunk(
            output,
            self.output_rate,
            last.channels,
            last.sequence,
            last.device_timestamp + last.duration,
            last.host_timestamp,
            {**last.attributes, "resampler_flush": True},
        )


class FFTNode(StatelessNode):
    def __init__(self, fft_length: int | None = None, window: str = "hann") -> None:
        self.fft_length = fft_length
        self.window = window

    def process(self, chunk: StreamChunk) -> StreamChunk:
        result = compute_fft(_signal(chunk), self.fft_length, self.window)
        spectrum = result.spectrum
        assert spectrum is not None
        return chunk.with_samples(
            spectrum,
            attributes={
                "domain": "frequency",
                "frequencies_hz": result.frequencies,
                "amplitude": result.magnitude,
                "fft_length": result.n_points,
                "window": self.window,
            },
        )


class PSDNode(StatelessNode):
    def __init__(self, segment_length: int | None = None, window: str = "hann") -> None:
        self.segment_length = segment_length
        self.window = window

    def process(self, chunk: StreamChunk) -> StreamChunk:
        segment = min(chunk.sample_count, self.segment_length or 256)
        result = compute_welch_psd(_signal(chunk), segment, window=self.window)
        density = result.psd
        assert density is not None
        return chunk.with_samples(
            density,
            attributes={
                "domain": "psd",
                "frequencies_hz": result.frequencies,
                "segment_length": segment,
                "window": self.window,
                "units": "unit^2/Hz",
            },
        )


class FeatureExtractionNode(StatelessNode):
    """Attach per-channel time-domain features without discarding samples."""

    def process(self, chunk: StreamChunk) -> StreamChunk:
        magnitude = np.abs(chunk.samples)
        rms = np.sqrt(np.mean(magnitude**2, axis=0)) if chunk.sample_count else 0.0
        peak = np.max(magnitude, axis=0) if chunk.sample_count else 0.0
        crest = np.divide(peak, rms, out=np.zeros_like(np.asarray(peak)), where=np.asarray(rms) > 0)
        crossing_data = np.real(chunk.samples)
        crossings = (
            np.mean(np.diff(np.signbit(crossing_data), axis=0), axis=0)
            if chunk.sample_count > 1
            else 0.0
        )
        return chunk.with_samples(
            chunk.samples,
            attributes={
                "features": {
                    "rms": np.asarray(rms),
                    "peak": np.asarray(peak),
                    "crest_factor": np.asarray(crest),
                    "zero_crossing_rate": np.asarray(crossings),
                }
            },
        )
