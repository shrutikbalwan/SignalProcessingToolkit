# DSP algorithms

All operations use `Signal`'s sample-major convention: mono arrays are `(samples,)` and
multichannel arrays are `(samples, channels)`. Frequencies and sample rates are in hertz;
signal units come from the per-channel `Signal.units` metadata.

## Spectral analysis

`compute_fft` uses `rfft`/`rfftfreq` for real input and a two-sided FFT for complex input.
Amplitude is `abs(X) / sum(window)`, which compensates the window coherent gain. For one-sided
results, interior bins are doubled; DC and the Nyquist bin (present only for even FFT sizes) are
not. Per-bin power is `abs(X)^2 / sum(window)^2`, with the same one-sided convention. The raw,
unscaled complex coefficients remain in `FFTResult.spectrum` so `inverse_fft` is lossless when
no analysis window or truncation was requested.

Taking `FFTResult.positive_spectrum` from a two-sided complex transform is an analysis-only
projection and is explicitly marked non-invertible. The older FFT peak and overlap-add ISTFT entry
points remain as deprecated adapters to the canonical analysis implementation; new code should use
`dsp.analysis.interpolate_peak` and `dsp.analysis.istft`.

`compute_periodogram` exposes SciPy-compatible spectrum or density scaling. `compute_welch_psd`
returns power spectral density in signal-units squared per hertz. Amplitude, power per bin, and
power per hertz are available as `magnitude`, `power`, and `psd`. `FFTResult.to_db` uses
20 log10 for amplitude or 10 log10 for power, with an explicit positive reference and floor.

## Sampling

`rational_resample`, `decimate_signal`, and `interpolate_signal` use polyphase FIR filtering via
`scipy.signal.resample_poly`. This applies anti-alias filtering before rate reduction and
reconstruction filtering after zero insertion. Ratios are reduced to lowest terms and output
length is `ceil(input_length * up / down)`. `resample_signal` rejects rate ratios outside its
bounded-rational numerical tolerance.

## Filtering

IIR filters are designed as second-order sections (SOS) by default. `FilterCoefficients` retains
SOS plus transfer-function coefficients for compatibility and reports stability from pole radii.
A causal digital filter is stable only when every pole magnitude is below one.

`apply_zero_phase` is an offline forward/backward operation. It rejects records too short for
edge padding instead of silently changing semantics. `apply_causal` is single-pass.
`StatefulFilter.process` preserves delay state across chunks; `reset` starts a new stream.
Filter design, frequency response, group delay, impulse response, and step response each have one
implementation in `dsp.filters.design`. The historical FIR/IIR module functions delegate to these
canonical functions for source compatibility. FIR design honors `FilterDesign.window`.

## Correlation and convolution

Correlation lags follow `scipy.signal.correlation_lags(len(first), len(second), "full")`, including
unequal lengths. Normalized correlation divides by the geometric mean of total energies;
unnormalized correlation preserves raw sum-of-products. Its physical lag axis is
`first.start_time - second.start_time + lag / sampling_rate`.

Linear convolution uses the sum of the two input start times as the first output time. Binary
operations require equal sampling rates and channel layouts; callers must explicitly resample or
align incompatible signals.

`overlap_add_convolution` and `overlap_save_convolution` are true bounded-block FFT algorithms.
They preserve real or complex dtype, process channels independently, and produce the same full
linear convolution and time origin as the direct operation.

## Measurements

- SNR: `10 log10(P_reference / P_error)` dB, with explicit noise or clean reference.
- PSNR: `10 log10(peak_reference^2 / MSE)` dB.
- THD: `100 * sqrt(sum(P_harmonics) / P_fundamental)` percent.
- THD+N: `100 * RMS(residual after DC and fundamental removal) / RMS(fundamental)` percent.
- SINAD: `10 log10(P_fundamental / P_residual)` dB.
- ENOB: `(SINAD_dB - 1.76) / 6.02` bits, the ideal full-scale sine convention.
- Crest factor: `max(abs(x)) / RMS(x)`, dimensionless; `dynamic_range` expresses it in dB.

Distortion measurements fit sine/cosine bases at the requested physical fundamental and
harmonics using least squares. They require finite, real, mono data and do not depend on an FFT
bin-centered tone.
