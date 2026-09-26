from __future__ import annotations

import numpy as np
import pytest
from hypothesis import given
from hypothesis import strategies as st

from signal_processing_toolkit.dsp.noise.metrics import snr, snr_from_noise, snr_from_reference
from signal_processing_toolkit.dsp.operations import (
    AddOperation,
    CircularShiftOperation,
    ScaleOperation,
    TimeShiftOperation,
)
from signal_processing_toolkit.models.signal import Signal, SignalMetadata
from signal_processing_toolkit.repositories.implementations.file_signal_repository import (
    FileSignalRepository,
)


def test_mono_signal_contract() -> None:
    signal = Signal(np.arange(4.0), 2.0, units="V", start_time=1.5)
    assert signal.shape == (4,)
    assert signal.n_samples == 4
    assert signal.n_channels == 1
    assert signal.channel_names == ("channel_1",)
    assert signal.units == ("V",)
    assert signal.duration == 2.0
    np.testing.assert_allclose(signal.time_vector, [1.5, 2.0, 2.5, 3.0])


def test_stereo_signal_preserves_sample_and_channel_axes() -> None:
    samples = np.arange(12.0).reshape(6, 2)
    signal = Signal(
        samples,
        3.0,
        channel_names=("left", "right"),
        units=("Pa", "Pa"),
    )
    assert signal.shape == (6, 2)
    assert signal.length == 6
    assert signal.n_channels == 2
    assert signal.duration == 2.0
    np.testing.assert_array_equal(signal.time_data, samples)
    resampled = signal.resample(6.0)
    assert resampled.shape == (12, 2)
    assert resampled.channel_names == ("left", "right")


def test_complex_signal_uses_magnitude_for_rms() -> None:
    signal = Signal(np.array([1 + 1j, 1 - 1j]), 10.0)
    assert signal.is_complex
    assert signal.rms == pytest.approx(np.sqrt(2.0))


def test_empty_signal_has_defined_timing_and_undefined_amplitude_metrics() -> None:
    signal = Signal(np.array([], dtype=np.float64), 10.0, start_time=2.0)
    assert signal.n_samples == 0
    assert signal.duration == 0.0
    assert signal.time_vector.size == 0
    with pytest.raises(ValueError, match="undefined"):
        _ = signal.rms
    empty_stereo = Signal(np.empty((0, 2)), 10.0)
    assert empty_stereo.shape == (0, 2)
    assert empty_stereo.duration == 0.0


@pytest.mark.parametrize(
    "samples,exception",
    [
        (np.array([np.nan]), ValueError),
        (np.array([np.inf]), ValueError),
        (np.array([True, False]), TypeError),
        (np.zeros((2, 2, 2)), ValueError),
    ],
)
def test_invalid_sample_arrays_are_rejected(
    samples: np.ndarray, exception: type[Exception]
) -> None:
    with pytest.raises(exception):
        Signal(samples, 1.0)


def test_resampling_preserves_physical_tone_identity() -> None:
    old_rate = 1000.0
    new_rate = 1600.0
    time = np.arange(int(old_rate)) / old_rate
    original = Signal(np.sin(2 * np.pi * 100.0 * time), old_rate, frequency=100.0)
    result = original.resample(new_rate)

    spectrum = np.abs(np.fft.rfft(result.time_data))
    frequencies = np.fft.rfftfreq(result.n_samples, 1 / result.sampling_rate)
    measured_frequency = frequencies[int(np.argmax(spectrum))]
    assert result.frequency == 100.0
    assert measured_frequency == pytest.approx(100.0, abs=1.0)
    assert result.duration == pytest.approx(original.duration)


def test_update_preserves_metadata_and_appends_provenance() -> None:
    metadata = SignalMetadata(
        name="ECG lead",
        description="calibrated",
        tags=["patient-1"],
        source="recorder",
        attributes={"subject": {"age": 42}},
    )
    original = Signal(
        np.ones((8, 2)),
        100.0,
        metadata=metadata,
        channel_names=("I", "II"),
        units="mV",
        start_time=12.5,
    )
    result = ScaleOperation().apply(original, factor=2)

    assert result.metadata.name == original.metadata.name
    assert result.metadata.created_at == original.metadata.created_at
    assert result.metadata.description == original.metadata.description
    assert result.metadata.tags == original.metadata.tags
    assert result.metadata.attributes == original.metadata.attributes
    assert result.metadata.attributes is not original.metadata.attributes
    assert result.metadata.parent_id == original.metadata.id
    assert result.metadata.id != original.metadata.id
    assert result.metadata.provenance[-1].operation == "scale"
    assert result.channel_names == original.channel_names
    assert result.units == original.units
    assert result.start_time == original.start_time


def test_npz_round_trip_preserves_complex_channels_and_metadata(tmp_path) -> None:
    original = Signal(
        np.array([[1 + 2j, 3 - 1j], [2 + 0j, 4 + 5j]]),
        8000.0,
        metadata=SignalMetadata(name="IQ", attributes={"receiver": "A"}),
        channel_names=("I", "Q"),
        units=("V", "V"),
        start_time=0.25,
    ).updated(operation="calibrate", parameters={"gain": 2})
    path = tmp_path / "signal.npz"
    repository = FileSignalRepository()
    repository.save(original, path)
    loaded = repository.load(path)

    np.testing.assert_array_equal(loaded.time_data, original.time_data)
    assert loaded.channel_names == original.channel_names
    assert loaded.units == original.units
    assert loaded.start_time == original.start_time
    assert loaded.metadata.name == original.metadata.name
    assert loaded.metadata.attributes == original.metadata.attributes
    assert loaded.metadata.provenance[-1].operation == "calibrate"


def test_binary_operations_reject_incompatible_sampling_rates_and_channels() -> None:
    mono = Signal(np.ones(8), 100.0)
    other_rate = Signal(np.ones(8), 200.0)
    stereo = Signal(np.ones((8, 2)), 100.0)
    with pytest.raises(ValueError, match="Sampling rate mismatch"):
        AddOperation().apply(mono, other_rate)
    with pytest.raises(ValueError, match="Channel count mismatch"):
        AddOperation().apply(mono, stereo)

    volts = Signal(np.ones(8), 100.0, units="V")
    amperes = Signal(np.ones(8), 100.0, units="A")
    with pytest.raises(ValueError, match="unit mismatch"):
        AddOperation().apply(volts, amperes)

    left_right = Signal(np.ones((8, 2)), 100.0, channel_names=("L", "R"))
    right_left = Signal(np.ones((8, 2)), 100.0, channel_names=("R", "L"))
    with pytest.raises(ValueError, match="ordering mismatch"):
        AddOperation().apply(left_right, right_left)


def test_padded_and_circular_shifts_are_distinct() -> None:
    signal = Signal(np.array([1.0, 2.0, 3.0, 4.0]), 1.0)
    padded = TimeShiftOperation().apply(signal, shift_samples=2)
    circular = CircularShiftOperation().apply(signal, shift_samples=2)
    np.testing.assert_array_equal(padded.time_data, [0.0, 0.0, 1.0, 2.0])
    np.testing.assert_array_equal(circular.time_data, [3.0, 4.0, 1.0, 2.0])


def test_snr_requires_an_explicit_definition() -> None:
    clean = Signal(np.ones(8), 10.0)
    noise = Signal(np.full(8, 0.1), 10.0)
    measured = clean.updated(time_data=clean.time_data + noise.time_data)
    with pytest.raises(ValueError, match="requires"):
        snr(measured)
    assert snr_from_noise(clean, noise) == pytest.approx(20.0)
    assert snr_from_reference(measured, clean) == pytest.approx(20.0)
    assert not hasattr(clean, "snr")


@given(
    n_samples=st.integers(min_value=0, max_value=5000),
    sampling_rate=st.floats(min_value=0.1, max_value=192000, allow_nan=False, allow_infinity=False),
    start_time=st.floats(min_value=-1e6, max_value=1e6, allow_nan=False, allow_infinity=False),
)
def test_duration_and_time_vector_properties(
    n_samples: int, sampling_rate: float, start_time: float
) -> None:
    signal = Signal(np.zeros(n_samples), sampling_rate, start_time=start_time)
    assert signal.duration == pytest.approx(n_samples / sampling_rate)
    assert signal.time_vector.shape == (n_samples,)
    if n_samples:
        assert signal.time_vector[0] == pytest.approx(start_time)
        assert signal.time_vector[-1] == pytest.approx(start_time + (n_samples - 1) / sampling_rate)


@given(
    n_samples=st.integers(min_value=1, max_value=500),
    old_rate=st.integers(min_value=10, max_value=5000),
    new_rate=st.integers(min_value=10, max_value=5000),
)
def test_resampling_preserves_duration_within_one_output_sample(
    n_samples: int, old_rate: int, new_rate: int
) -> None:
    signal = Signal(np.zeros(n_samples), float(old_rate))
    result = signal.resample(float(new_rate))
    # scipy.signal.resample_poly defines the output length as ceil(n * up / down).
    assert result.n_samples == max(1, int(np.ceil(n_samples * new_rate / old_rate)))
    assert abs(result.duration - signal.duration) <= 1.0 / new_rate + 1e-12
