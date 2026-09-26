# ADR 0001: src layout and optional integrations

- Status: accepted
- Date: 2026-09-26

Use `src/signal_processing_toolkit` and setuptools discovery. Keep GUI, audio,
image, AI, hardware, export, and documentation dependencies optional so the
scientific DSP core imports in a minimal environment. This prevents accidental
runtime coupling and makes wheel smoke tests meaningful.
