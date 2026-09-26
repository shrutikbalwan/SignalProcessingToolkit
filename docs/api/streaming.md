# Real-time streaming engine

The streaming package implements a reusable bounded pipeline:

```text
StreamSource -> BoundedRingBuffer -> ProcessingNode(s) -> StreamSink(s)
```

The source and processing stages run on dedicated Python worker threads. Sinks must not mutate Qt
widgets from those threads. `LiveMonitorView` uses a bounded `PlotSink`; a single Qt timer copies its
latest snapshot into one persistent `PlotDataItem`, so curves are updated without clearing and
recreating the plot.

## Stream chunks

`StreamChunk.samples` follows the toolkit's sample-major convention:

- mono: `(samples,)`;
- multichannel: `(samples, channels)`.

Every chunk carries a positive sampling rate, ordered `ChannelMetadata`, a non-negative source
sequence number, a device timestamp, and a host Unix timestamp. Nodes use `with_samples()` so these
identifiers and timestamps survive processing. Published sample arrays are immutable by convention:
a source must not modify an array after placing its chunk in the pipeline.

## Lifecycle and backpressure

`StreamPipeline` supports `configure`, `start`, `pause`, `resume`, `stop`, `reset`, and `close`.
`stop` signals both workers and joins them; `close` also releases the source and sinks. `reset`
clears node delay states, recordings, queued frames, metrics, and replay position.
Replacing a configuration first validates the new source and nodes, then closes superseded sources
and sinks. If configuration fails, the replacement source is closed and the previous configuration
is retained. On finite natural input, node `flush()` output is propagated through every downstream
node and sink before the pipeline stops; explicit cancellation does not synthesize a tail.

The ring buffer has fixed capacity and one explicit `OverflowPolicy`:

- `BLOCK`: wait for capacity without unbounded allocation;
- `DROP_OLDEST`: discard the oldest queued chunk to minimize display latency;
- `DROP_NEWEST`: preserve queued history and reject the arriving chunk;
- `RAISE`: fail immediately with `BufferError`.

Metrics report produced, processed and dropped frames, current and maximum queue depth, and mean,
maximum and most recent node/sink processing latency. Latency is measured with the monotonic clock
around the complete node-and-sink path.

## Nodes and numerical assumptions

- `GainNode` applies a finite scalar gain.
- `DCRemovalNode` is the causal first-order blocker
  `y[n] = x[n] - x[n-1] + alpha*y[n-1]`, where
  `alpha = exp(-2*pi*cutoff/sampling_rate)`.
- `SOSFilterNode` rejects unstable poles and preserves `sosfilt` delay state independently per
  channel.
- `ResamplerNode` reduces the rational rate ratio, zero-inserts, applies a windowed-sinc FIR at the
  upsampled rate, and retains FIR and decimation-phase state. It is causal and therefore reports its
group delay; unlike offline `resample_poly`, it does not remove delay using future samples.
  When finite input ends, it flushes exactly the FIR tail once so samples delayed across the last
  chunk are not lost.
- `FFTNode` uses the corrected, coherent-gain-compensated FFT core and keeps the complex spectrum.
- `PSDNode` uses the corrected Welch PSD implementation.
- `FeatureExtractionNode` adds RMS, peak, crest factor, and real-part zero-crossing rate to chunk
  attributes while retaining the original samples.

`SyntheticSource` is phase-continuous and optionally real-time paced. `AudioSource` is a
dependency-free interface intended for adapters in the optional audio package; importing the core
does not import `sounddevice`. `RecorderSink` creates a `RecordedSession`, which can be saved as a
pickle-free NPZ file and replayed in exact recorded order by `ReplaySource`.

## Example

```python
from signal_processing_toolkit.streaming import (
    GainNode,
    OverflowPolicy,
    PlotSink,
    StreamPipeline,
    SyntheticSource,
)

pipeline = StreamPipeline(queue_capacity=8, overflow_policy=OverflowPolicy.DROP_OLDEST)
pipeline.configure(
    SyntheticSource(frequency=1000, chunk_size=1024),
    nodes=[GainNode(0.5)],
    sinks=[PlotSink(maximum_samples=8192)],
)
pipeline.start()
# pipeline.pause(); pipeline.resume(); pipeline.stop(); pipeline.reset()
pipeline.close()
```

Recorded sessions preserve samples, rates, channel identity, sequence numbers, and timestamps.
JSON-safe chunk attributes are serialized. Non-JSON application objects are represented as text;
large derived arrays should remain in analysis results rather than chunk attributes.

Real microphone and serial sensor sources, raw/processed recording, connection events, and the
versioned sensor wire formats are documented in [Real-world data acquisition](acquisition.md).

Any source, node, or sink exception transitions the pipeline to `FAILED`, cancels both workers,
wakes blocked ring-buffer calls, and is retained as `pipeline.error`. `stop()` joins both threads;
`close()` then releases source and sink resources.
