# Advanced analysis

The advanced analysis API is available from `signal_processing_toolkit.dsp.analysis`. It follows
the toolkit's sample-major convention. Time-frequency arrays use `(frequency, frame)` for mono
signals and `(frequency, frame, channel)` for multichannel signals.

## STFT and streaming

`STFTConfig` records the window, window length, overlap in samples, FFT length, spectrum or PSD
scaling, detrending, boundary extension, and end padding. `stft` stores those settings in every
`STFTResult`; `istft` uses the same settings and crops to the original sample count. Reconstruction
requires a window/hop combination satisfying the overlap-add constraint. The default Hann window
with 50% overlap satisfies it.

`StreamingSpectrogram` uses boundary-free, unpadded frames. It retains exactly the overlap needed
by the next chunk and emits each complete frame once. Call `reset()` before starting an unrelated
stream.

## Cross spectra and coherence

`cross_spectral_density` uses Welch averaging and reports a complex cross spectrum. Density
scaling has units of the first signal's unit times the second signal's unit per hertz.
`magnitude_squared_coherence` calculates `|Pxy|² / (Pxx Pyy)` and returns values bounded from zero
to one. Inputs must have compatible sample rates, lengths, and channel layouts.

## Analytic and envelope analysis

`analytic_signal` applies the Hilbert transform on the sample axis. `signal_envelope` is the
analytic magnitude. Instantaneous phase is the optionally unwrapped analytic angle in radians;
instantaneous frequency is its central numerical derivative multiplied by `sampling_rate / 2π`
and is reported in hertz. Edge samples and locations where the envelope approaches zero are less
reliable.

`real_cepstrum` returns quefrency in seconds. `envelope_spectrum` removes the envelope mean by
default before using the calibrated FFT implementation.

## Wavelets, peaks, harmonics, and events

`continuous_wavelet_transform` uses an energy-normalized complex Morlet wavelet. Scale and
frequency are related by `f = omega0 * sampling_rate / (2π * scale)`. Coefficients use
`(scale, sample)` or `(scale, sample, channel)` shape, and the scalogram is `abs(coefficients)²`.

`band_power` integrates PSD using trapezoidal integration. `interpolate_peak` uses three-bin
parabolic interpolation, optionally in log-magnitude space. Harmonic markers retain markers above
Nyquist with `in_band=False`, allowing callers to explain why they are not plotted.

Threshold events support direction, minimum duration, minimum separation, hysteresis, and Gaussian
smoothing. Transient detection finds prominent positive slopes of the smoothed Hilbert envelope.
Times are physical `Signal` times, including `start_time`.

## Desktop interface

The **Advanced Analysis** page contains time/envelope, STFT, wavelet, envelope-spectrum, cepstrum,
cross-spectrum/coherence, event, measurement, and parameter tabs. A movable time region controls
recalculation. Time cursors are linked between waveform and time-frequency views. Measurement and
parameter tables export to CSV. All calculations run through the Qt worker pool.
The page exposes the event direction, threshold mode/value, hysteresis, durations, transient
prominence, and transient smoothing controls. Threshold events and transients share the exportable
event table with an explicit type column. Every result tab displays the parameters used to compute
that result. Cancelling or closing the page suppresses late results and compound calculations check
for cancellation between analysis stages.
