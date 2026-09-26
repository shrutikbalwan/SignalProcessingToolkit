# Signal Processing Toolkit

Signal Processing Toolkit is a Python 3.12+ desktop application and DSP library for signal
generation, analysis, filtering, sampling, convolution, correlation, audio, and image workflows.

## Installation

Clone the repository and install the project from its root:

```bash
git clone https://github.com/shrutikbalwan/SignalProcessingToolkit.git
cd SignalProcessingToolkit
python -m pip install -e .
```

The default installation contains the numerical DSP core only. Install the extras needed by a
workflow:

```bash
# Desktop interface
python -m pip install -e ".[gui]"

# Optional feature integrations
python -m pip install -e ".[audio,image,ai,export]"

# All desktop integrations
python -m pip install -e ".[gui,audio,image,ai,hardware,export]"
```

Other isolated extras are `ai`, `hardware`, `dev`, and `docs`. OpenCV, sounddevice, and ONNX
Runtime are not installed with the DSP core.

## Running

After installation, either command launches the desktop application:

```bash
spt
python -m signal_processing_toolkit
```

Both entry points support standard command help and version checks without importing GUI or
hardware packages:

```bash
spt --help
python -m signal_processing_toolkit --version
```

If the `gui` extra is absent, launching the desktop application prints the exact installation
command needed. Importing `signal_processing_toolkit` or its DSP modules does not require GUI,
audio, image, AI, or hardware dependencies.

## Development

```bash
python -m pip install -e ".[dev,gui,audio,image,export]"
ruff format .
ruff check .
mypy src
pytest
python -m build
```

## Project structure

```text
SignalProcessingToolkit/
|-- src/
|   `-- signal_processing_toolkit/
|       |-- __init__.py
|       |-- __main__.py
|       |-- main.py
|       |-- ai/
|       |-- audio/
|       |-- core/
|       |-- dsp/
|       |   `-- analysis/
|       |-- hardware/
|       |-- models/
|       |-- plots/
|       |-- repositories/
|       |-- services/
|       |-- streaming/
|       `-- ui/
|-- docs/
|   `-- api/
|-- examples/
|   |-- edge_ai_motor_anomaly/
|   `-- esp32/
|-- tests/
|   |-- test_services/
|   `-- test_ui/
|-- ARCHITECTURE.md
|-- LICENSE
|-- README.md
`-- pyproject.toml
```

Application imports use the `signal_processing_toolkit` package name. The `src` directory is a
packaging boundary and is not itself a Python package.

## UI architecture

The sidebar and central `QStackedWidget` use the same keyed navigation descriptors, so every
sidebar item has exactly one validated page. `ApplicationState` owns the active signal and
propagates generated or loaded data to analysis and export controllers. Signal-dependent pages
show explicit empty, loading, content, and error states. FFT, filtering, sampling, noise,
convolution, correlation, and window processing run through Qt's global thread pool, with results
marshalled back to the UI. Settings and theme choices are persisted through `SettingsManager`.

## Signal data model

Signal arrays are sample-major: mono data uses `(samples,)` and multichannel data uses
`(samples, channels)`. The model supports real and complex samples, channel names, per-channel
physical units, start times, structured metadata, and processing provenance. See the
[Signal API guide](docs/api/signal.md) for validation, alignment, resampling, shifting, and SNR
semantics.

The [DSP algorithms guide](docs/api/dsp.md) documents spectral scaling, polyphase resampling,
SOS and streaming filtering, correlation time origins, and every measurement formula and unit.
The [advanced analysis guide](docs/api/advanced_analysis.md) covers STFT/ISTFT, streaming
spectrograms, coherence, analytic signals, cepstrum, wavelets, band power, and event detection.

The [real-time streaming guide](docs/api/streaming.md) documents bounded pipelines, backpressure,
worker lifecycle, deterministic replay, initial processing nodes, and live plot integration.
The [data-acquisition guide](docs/api/acquisition.md) documents callback audio, serial discovery,
CSV and checksummed binary sensor packets, reconnect behavior, sessions, and ESP32 examples.
The [Edge-AI guide](docs/api/edge_ai.md) documents model metadata, identical training/inference
preprocessing, provider selection, streaming inference, event capture and evaluation.
The [pipeline editor guide](docs/api/pipelines.md) documents typed DAG validation, persistence,
undo/redo, templates and offline/streaming execution.
The [embedded-target guide](docs/api/embedded.md) documents Q7/Q15/Q31 simulation, quantized
filter error analysis, portable/CMSIS/ESP-DSP exports, checksummed vectors, and host/device
comparison. Performance figures are estimates until measured on hardware.

For contributors and release maintainers, see [CONTRIBUTING.md](CONTRIBUTING.md),
[the release checklist](docs/release-checklist.md), and the current
[release-readiness report](docs/release-readiness.md). Dependency and asset
license notes are in [docs/licenses.md](docs/licenses.md). Screenshots and
videos are not bundled yet; they are tracked on the roadmap.

## Optional dependency groups

| Extra | Purpose |
|---|---|
| `gui` | PyQt6 desktop UI, interactive plots, and Matplotlib |
| `audio` | Recording/playback and audio file support |
| `image` | OpenCV-backed image processing |
| `ai` | Lazy ONNX/ORT model execution through ONNX Runtime |
| `hardware` | Serial hardware integration |
| `export` | Excel and PDF exports |
| `dev` | Tests, type checking, formatting, linting, and builds |
| `docs` | Sphinx documentation toolchain |

## License

MIT License. See [LICENSE](LICENSE).

## Links

- [Repository](https://github.com/shrutikbalwan/SignalProcessingToolkit)
- [Issue tracker](https://github.com/shrutikbalwan/SignalProcessingToolkit/issues)
