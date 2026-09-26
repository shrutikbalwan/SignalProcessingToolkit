# Signal API

`signal_processing_toolkit.models.Signal` represents sampled physical data. It uses a
sample-major convention throughout the toolkit:

| Signal kind | `time_data.shape` | Sample axis | Channel axis |
|---|---:|---:|---:|
| Mono | `(n_samples,)` | `0` | none |
| Multichannel | `(n_samples, n_channels)` | `0` | `1` |

Channels are never flattened. `n_samples` means the number of positions on the sample axis, so
`duration == n_samples / sampling_rate` for mono and multichannel signals.
`time_vector` is expressed in seconds and begins at `start_time`.

The legacy `length` property returns `n_samples` for compatibility but emits a
`DeprecationWarning`; new code should use the unambiguous `n_samples` name.

## Values, channels, and units

Real floating-point, complex floating-point, and integer arrays are accepted. Integer arrays are
converted to `float64`; floating and complex precision is retained. Boolean, object, NaN, and
infinite values are rejected at construction. Empty arrays are valid and have zero duration, but
amplitude measurements such as RMS are undefined and raise `ValueError`.

`channel_names` contains one unique name per channel. If omitted, names such as `channel_1` are
generated. `units` may be one string applied to every channel or a tuple with one physical unit per
channel—for example `"V"`, `("Pa", "Pa")`, or `("m/s²", "m/s²", "m/s²")`.

## Metadata and provenance

`SignalMetadata` stores descriptive fields, tags, source information, structured `attributes`, and
an immutable sequence of `ProcessingStep` records. Use `Signal.updated(...)` when producing a
derived signal. It validates the new samples, preserves descriptive metadata, channel information,
units, and start time, creates a new signal identity, and appends a provenance record.

`Signal.copy()` makes a deep copy while preserving identity. Pass `preserve_id=False` when a new
logical signal identity is required.

## Alignment and resampling

Pointwise binary operations require matching sampling rates, start times, channel counts, channel
ordering, and physical units. A sampling-rate mismatch is never resolved implicitly: call
`signal.resample(target_rate)` explicitly. Resampling changes the sample grid and sampling rate but
does not scale physical frequency metadata—a 100 Hz component remains 100 Hz.

`TimeShiftOperation` performs a fixed-length shift with zero padding. Samples shifted beyond an end
are discarded. Use `CircularShiftOperation` only when periodic wraparound is intended.

## SNR measurements

SNR is not an intrinsic `Signal` property. Use one of the explicit functions from
`signal_processing_toolkit.dsp.noise.metrics`:

- `snr_from_noise(signal, noise)` when a noise-only measurement is available;
- `snr_from_reference(measured, reference)` when a clean reference is available.

Both validate signal compatibility and use magnitude-squared power, including for complex data.
