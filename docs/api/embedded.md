# Embedded-target analysis and export

`signal_processing_toolkit.embedded` simulates Q7, Q15 and Q31 arithmetic and
generates portable C headers, source, JSON test vectors and configuration
metadata. Rounding (`nearest`, `floor`, `ceil`, `truncate`) and overflow
(`saturate`, `wrap`, `raise`) are explicit. `simulate_fir` and `simulate_sos`
return fixed-point output, floating reference output, error and memory/MAC
estimates.

Generated files include a version, SHA-256 coefficient checksum and all filter
parameters. CMSIS-DSP and ESP-DSP exports currently use compatible integer
coefficient declarations; implementation integration and performance must be
measured on the target. MAC and memory numbers are estimates, never cycle
claims. `compare_results` compares host and device vectors with an explicit
tolerance.
