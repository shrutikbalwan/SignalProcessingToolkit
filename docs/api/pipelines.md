# Visual processing pipelines

`signal_processing_toolkit.pipelines` stores an editor graph as a versioned JSON document:

```json
{
  "schema": "signal-processing-toolkit.pipeline",
  "version": 1,
  "nodes": [{"id": "gain_1", "kind": "gain", "parameters": {"gain": 2.0}}],
  "edges": [{"source": {"node": "input", "port": "out"},
             "target": {"node": "gain_1", "port": "in"}}]
}
```

Nodes expose typed ports with data domain, dtype, sample-major shape, channel count and sampling
rate. Connections reject incompatible ports, multiple consumers of a non-variadic input and cycles.
`PipelineGraph.topological_order()` is deterministic and is the execution order. Extensions can add
typed node kinds with `register_node_definition()`.

`PipelineDocument` records graph snapshots for undo and redo. Opening a version-0 document migrates
the old top-level `connections` form to version 1; unknown future versions are rejected rather than
silently interpreted.

`GraphExecutor` runs the same stateful node instances over offline chunks or streaming chunks.
`GraphProcessingAdapter` embeds a graph in the existing bounded `StreamPipeline` where the graph's
nodes support the `ProcessingNode` contract. Each node exposes enabled, bypass and mute behavior,
runtime latency/status/error data, and the latest bounded preview chunk.

The Pipeline Editor page provides draggable node cards, typed selected-node connections, disconnect,
delete, reorder, parameter inspection, status/latency/error display, intermediate preview,
undo/redo and JSON snapshots. Starter templates are `audio_spectrum_analyzer`,
`noise_removal_chain`, `esp32_vibration_monitor`, `bearing_envelope_analyzer` and
`edge_ai_anomaly_detector`.
