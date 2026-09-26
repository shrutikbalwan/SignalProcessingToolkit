# Signal Processing Toolkit architecture

## Repository layout

```text
SignalProcessingToolkit/
|-- src/
|   `-- signal_processing_toolkit/
|       |-- __init__.py
|       |-- __main__.py
|       |-- app.py
|       |-- main.py
|       |-- audio/
|       |-- ai/
|       |-- pipelines/
|       |-- core/
|       |-- dsp/
|       |-- hardware/
|       |-- models/
|       |-- plots/
|       |-- repositories/
|       |-- services/
|       |-- streaming/
|       `-- ui/
|           |-- components/
|           |-- controllers/
|           |-- styles/
|           |-- viewmodels/
|           |-- views/
|           |-- main_window.py
|           `-- workers.py
|-- docs/api/
|-- examples/esp32/
|-- tests/
|   |-- test_services/
|   `-- test_ui/
|-- LICENSE
|-- README.md
`-- pyproject.toml
```

`src` is the packaging boundary, not an importable application package. All application imports
start with `signal_processing_toolkit` or are package-relative.

## Layer responsibilities

- `models` contains signal and analysis data structures.
- `dsp` contains numerical algorithms with no Qt dependency.
- `services` coordinate DSP operations and repositories.
- `core` contains settings, events, application state, history, logging, and plugins.
- `ui/viewmodels` exposes observable state and invokes services.
- `ui/views` owns widgets and presentation only.
- `ui/controllers` composes views and routes application events.

Optional audio, image, AI, and hardware integrations remain outside the DSP import path. The main
controller loads audio and image controllers only when their optional dependencies are available.

The `ai` package owns serializable preprocessing, runtime adapters, streaming inference and
evaluation. It imports ONNX Runtime only when a real backend is queried. The DSP and streaming core
do not import the AI package; `EdgeAINode` adapts AI inference to the existing processing-node
contract. Model projects retain checksums and preprocessing references rather than embedding model
binaries.

`pipelines` is a dependency-light graph layer above the streaming node contract. It owns typed DAG
validation, schema migration, editor history, templates and a graph executor. The executor reuses
the existing stateful processing nodes, so a reopened graph uses the same chunk-boundary behavior in
offline previews and streaming adapters.

## UI composition and navigation

`MainWindow` uses one `QStackedWidget` as its primary content area. `NAV_ITEMS` is the ordered,
keyed source of truth for both sidebar entries and page registration. Startup validates that page
keys and order match the navigation descriptors, and each page is assigned a `navigationKey`
property. A bad index/key pairing raises an error instead of selecting an unrelated page.

Dashboard, Live Monitor, and Settings are concrete pages in the same stack. Signal-dependent pages
are wrapped by `StatefulPage`, which provides visible empty, loading, error, and content states.

## Signal state and data flow

`ApplicationState` owns the authoritative current signal and the deduplicated list of signals. The
main controller accepts generated signals, loaded-signal events, and operation results, then
propagates the state to:

- signal operations;
- convolution and correlation selectors;
- sampling, FFT, windows, filters, and noise analysis;
- export;
- the dashboard summary.

This keeps individual pages independent while ensuring they all analyze the same selected signal.
Observable values use array-safe equality and explicit observer removal during shutdown.

## Background work and lifecycle

`TaskRunner` submits expensive FFT, filtering, sampling, noise, convolution, correlation, and
window operations to Qt's global thread pool. Completion and error signals return presentation
updates to the UI thread. A page cannot submit overlapping work through the same runner. Shutdown
sets cooperative cancellation tokens, suppresses late results, and waits for every worker. Compound
advanced-analysis jobs inspect the token between numerical stages; a single native SciPy call is
not forcefully interrupted, because terminating native code is unsafe.

Live Monitor connects its timer once during construction; start and stop are idempotent. Closing
the application stops the monitor, waits for active workers, disposes view models/controllers,
unsubscribes shared state, and clears the event bus.

## Themes and accessibility

Dark and light themes are applied centrally by `ThemeManager`, while `SettingsManager` persists the
selection. Sidebar shortcuts provide keyboard navigation, and interactive controls receive
accessible names where a view has not supplied a more specific one.

## DSP implementation boundaries

Numerical kernels live under `signal_processing_toolkit.dsp`; application services are facades
and do not maintain competing FFT, sampling, or filtering formulas. Spectral results retain raw
complex transforms, rate conversion is polyphase, IIR filters use second-order sections, and
streaming delay state belongs to `StatefulFilter` rather than a controller.

Advanced time-frequency and feature extraction live in `dsp.analysis`. Typed result objects carry
the parameters needed to interpret or reconstruct each result. `AnalysisService` performs region
selection and composes these kernels, while `AnalysisView` only schedules work, presents linked
cursors and result tabs, and exports measurement tables.

## Real-time streaming engine

`signal_processing_toolkit.streaming` implements the bounded path `StreamSource -> Ring Buffer ->
ProcessingNode(s) -> StreamSink(s)`. Source reads and processing execute on dedicated worker threads;
Qt only snapshots the bounded `PlotSink` and updates an existing curve. Overflow behavior is an
explicit pipeline choice, and metrics expose drops, queue depth, and processing latency. Stateful
nodes own their filter, DC-blocker, resampler, and decimation-phase state and clear it through the
pipeline reset lifecycle. Recorded sessions retain sequence and timing information for deterministic
replay. Optional audio implementations depend only on the `AudioSource` interface, keeping hardware
libraries outside the streaming core.

Optional acquisition adapters live in `audio.streaming` and `hardware`. Both depend on small
backend protocols and import sounddevice or pyserial only when a real backend operation is invoked,
allowing simulated devices to exercise callback, fragmentation, corruption, and reconnect behavior.
Recorder taps preserve raw chunks before nodes while normal sinks retain processed chunks. Session
files include connection events and a pipeline configuration snapshot and replay through the normal
`ReplaySource` path.

Reconfiguration is transactional: a replacement is configured before the previous source and
sinks are released. Natural source exhaustion flushes finite stateful-node tails through all
downstream nodes and sinks. Failures are recorded as `FAILED`, wake blocked workers, and remain
available through `pipeline.error`.
