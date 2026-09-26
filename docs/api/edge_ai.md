# Edge AI

The optional `signal_processing_toolkit.ai` package is outside the DSP import path. Installing the
numerical core does not install or import ONNX Runtime. Install real model execution support with:

```bash
python -m pip install -e ".[ai]"
```

## Model contract

`EdgeModel.load()` accepts `.onnx` and ONNX Runtime `.ort` files. Each model must have a sidecar
named `<model-stem>.metadata.json`. Missing or inconsistent metadata is an error before execution.
The file contains unique class labels, input/output tensor names, whether output values are logits
or probabilities, licensing information, and a serialized `PreprocessingPipeline`.

Raw signal arrays are sample-major. Time models receive `(batch, samples, channels)` float32 data.
Spectrogram models receive `(batch, frequency, frame, channel)` float32 data. DC removal,
normalization values, channel selection, STFT window, overlap, FFT length, scaling and log floor are
all persisted. `PreprocessingPipeline.fit()` accepts one sample-major training window or a batch
of `(batch, samples, channels)` windows and computes per-channel statistics. Both training and
inference must call that same persisted pipeline's `transform()` method.

Execution providers are selected from those actually reported by ONNX Runtime. Requested providers
retain their order and CPU is appended when available as a deterministic fallback. Tensor names,
ranks, static dimensions, dtypes, class counts, finite outputs, probability bounds and row sums are
validated.

## Streaming and events

`SlidingWindowInference` retains samples across `StreamChunk` boundaries and advances by a
configured hop. `EdgeAINode` executes in the existing pipeline processing worker and attaches
inference points and detected events to chunk attributes, never the Qt thread. `EventDetector`
offers moving-average smoothing, confidence thresholds, optional label selection and per-class
cooldowns. `DetectedEvent.with_context()` attaches samples before and after a trigger and `save()`
writes JSON metadata plus compressed NumPy samples.

The Edge AI page loads and validates models in a Qt thread-pool task and displays current class
probabilities, confidence, provider, checksum, latency and bounded probability histories.

## Measurement and evaluation

Each inference batch reports wall-clock latency, windows/second and peak Python allocation measured
by `tracemalloc`. This memory value excludes provider-native allocations and is therefore not total
process RSS. `compare_models()` compares class agreement, probability error, latency, file size and
checksums for floating-point and quantized models.

Evaluation helpers provide confusion matrices, per-class precision/recall/F1, binary ROC and PR
points, per-threshold statistics, and false-positive indexes for event inspection. Classes with no
predicted or actual positives receive a score of zero rather than NaN.

## Project storage

`Project.ai_models` stores serialized `ModelReference` dictionaries containing the model path,
SHA-256 checksum, labels and full preprocessing definition. Projects intentionally reference model
files instead of embedding potentially large or restrictively licensed binaries.
