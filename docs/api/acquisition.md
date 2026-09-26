# Real-world data acquisition

Audio and serial adapters implement the same `StreamSource` contract as synthetic and replay
sources. Device callbacks and serial reads occur outside the Qt thread, and the pipeline retains
its bounded queue and explicit overflow policy. Importing `signal_processing_toolkit.dsp` does not
import `sounddevice` or `serial`.

## Audio

Install `signal-processing-toolkit[audio]`. `enumerate_audio_devices()` reports each device's input
and output channel capacity and default rate. `AudioStreamConfig` selects the input device, sample
rate, channel count, NumPy dtype, callback block size, queue capacity, channel names and units.

`SoundDeviceAudioSource` copies each callback buffer before returning and keeps its original
`(samples, channels)` shape, including a one-column shape for mono device input. Its bounded callback
queue drops the oldest block when acquisition outruns processing. `metrics` reports callback blocks,
input overflows, output underflows and queue drops; every chunk also records callback status flags.

Use a `RecorderNode` before processing and a `RecorderSink` after processing to retain separate raw
and processed recordings:

```python
from signal_processing_toolkit.audio import AudioStreamConfig, SoundDeviceAudioSource
from signal_processing_toolkit.streaming import GainNode, RecorderNode, RecorderSink, StreamPipeline

raw = RecorderSink(stream_name="raw_audio")
processed = RecorderSink(stream_name="processed_audio")
pipeline = StreamPipeline()
pipeline.configure(
    SoundDeviceAudioSource(AudioStreamConfig(sampling_rate=48000, channels=2, block_size=1024)),
    nodes=[RecorderNode(raw), GainNode(0.5)],
    sinks=[processed],
)
pipeline.start()
```

## Serial discovery and connection

Install `signal-processing-toolkit[hardware]`. `enumerate_serial_ports()` reports device names,
descriptions and hardware identifiers. `SerialSourceConfig` selects the port, baud rate, wire
format, sampling rate, channel metadata, read timeout and bounded exponential reconnect policy.
`SerialSensorSource` reports received, corrupt, missing and out-of-order packet counts plus
disconnect/reconnect totals. Connection attempts stop after `reconnect_attempts + 1` total attempts;
failure then propagates to the pipeline instead of retrying forever.

### Newline CSV format

Each ASCII line is one multichannel sample:

```text
sequence,timestamp_seconds,channel_1,...,channel_N\n
```

For example, a three-axis accelerometer can send:

```text
42,1.250000,0.031,-0.012,9.806
```

A single-channel microphone envelope or ADC stream can send:

```text
43,1.251000,-0.127
```

The configured `channel_names` determines `N`. Invalid ASCII, non-finite numbers and incorrect
field counts are counted as corrupt packets.

### Binary format version 1

All integers, the timestamp and payload use little-endian byte order. There is no implicit
alignment or padding.

| Offset | Type | Meaning |
|---:|---|---|
| 0 | 4 bytes | Magic ASCII `SPT!` |
| 4 | `uint8` | Protocol version, currently `1` |
| 5 | `uint32` | Sequence number |
| 9 | `float64` | Device timestamp in seconds |
| 17 | `uint16` | Channel count |
| 19 | `uint32` | Sample count per channel |
| 23 | `float32[]` | Sample-major payload: sample 0 channels, sample 1 channels, ... |
| variable | `uint32` | IEEE CRC-32 of every preceding byte from magic through payload |

The parser accepts arbitrary fragmentation, discards bytes before the next magic value, validates
version and bounded dimensions, and resynchronizes after a checksum failure. Sequence gaps count as
missing packets. Packets behind the latest accepted sequence are marked out of order. Sequence
numbers wrap from `0xffffffff` to zero.

`SensorPacket`, `encode_binary_packet`, `BinaryPacketParser`, and `CSVPacketParser` provide the
reference implementation. The [ESP32 protocol example](../../examples/esp32/README.md) gives
accelerometer and microphone packet examples.

## Recorded sessions and replay

`RecorderSink` stores sample data, device and host timestamps, channel metadata, connection events,
the pipeline configuration and a stream name in a pickle-free NPZ file. Version-one session files
remain readable. JSON-safe chunk attributes are retained. Call `session.replay_source()` and
configure it as the source of the same node chain for deterministic offline replay.
