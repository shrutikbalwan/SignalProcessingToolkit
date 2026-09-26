# ADR 0002: sample-major signal arrays

- Status: accepted
- Date: 2026-09-26

Signals use `(samples,)` for mono and `(samples, channels)` for multichannel
data. Sampling rate, channel units, start time, metadata, and provenance travel
with transformations. Binary operations reject incompatible rates/channels
unless alignment is explicit.
