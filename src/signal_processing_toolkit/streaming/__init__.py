"""Reusable bounded real-time signal-processing pipelines."""

from signal_processing_toolkit.streaming.buffer import (
    BoundedRingBuffer,
    BufferClosedError,
    BufferSnapshot,
    OverflowPolicy,
)
from signal_processing_toolkit.streaming.interfaces import (
    ProcessingNode,
    StatelessNode,
    StreamSink,
    StreamSource,
)
from signal_processing_toolkit.streaming.model import ChannelMetadata, SessionEvent, StreamChunk
from signal_processing_toolkit.streaming.nodes import (
    DCRemovalNode,
    FeatureExtractionNode,
    FFTNode,
    GainNode,
    PSDNode,
    RecorderNode,
    ResamplerNode,
    SOSFilterNode,
)
from signal_processing_toolkit.streaming.pipeline import (
    PipelineMetrics,
    PipelineState,
    StreamPipeline,
)
from signal_processing_toolkit.streaming.sinks import (
    CallbackSink,
    PlotSink,
    RecordedSession,
    RecorderSink,
)
from signal_processing_toolkit.streaming.sources import AudioSource, ReplaySource, SyntheticSource

__all__ = [
    "AudioSource",
    "BoundedRingBuffer",
    "BufferClosedError",
    "BufferSnapshot",
    "CallbackSink",
    "ChannelMetadata",
    "DCRemovalNode",
    "FFTNode",
    "FeatureExtractionNode",
    "GainNode",
    "OverflowPolicy",
    "PSDNode",
    "PipelineMetrics",
    "PipelineState",
    "PlotSink",
    "ProcessingNode",
    "RecordedSession",
    "RecorderNode",
    "RecorderSink",
    "ReplaySource",
    "ResamplerNode",
    "SOSFilterNode",
    "StatelessNode",
    "StreamChunk",
    "SessionEvent",
    "StreamPipeline",
    "StreamSink",
    "StreamSource",
    "SyntheticSource",
]
