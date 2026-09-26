"""Wire formats for serial sensor acquisition."""

from __future__ import annotations

import struct
import zlib
from dataclasses import dataclass

import numpy as np

BINARY_MAGIC = b"SPT!"
BINARY_VERSION = 1
_HEADER = struct.Struct("<4sBIdHI")
_CHECKSUM = struct.Struct("<I")


@dataclass(frozen=True, slots=True)
class SensorPacket:
    sequence: int
    timestamp: float
    samples: np.ndarray

    def __post_init__(self) -> None:
        values = np.asarray(self.samples, dtype=np.float32)
        if values.ndim != 2 or values.shape[0] < 1 or values.shape[1] < 1:
            raise ValueError("sensor samples must have shape (samples, channels)")
        if not np.all(np.isfinite(values)):
            raise ValueError("sensor samples must be finite")
        if not 0 <= self.sequence <= 0xFFFFFFFF:
            raise ValueError("sequence must fit an unsigned 32-bit integer")
        if not np.isfinite(self.timestamp):
            raise ValueError("timestamp must be finite")
        object.__setattr__(self, "samples", values)


def encode_binary_packet(packet: SensorPacket) -> bytes:
    """Encode version-one little-endian float32 sensor data with CRC-32."""
    sample_count, channel_count = packet.samples.shape
    header = _HEADER.pack(
        BINARY_MAGIC,
        BINARY_VERSION,
        packet.sequence,
        packet.timestamp,
        channel_count,
        sample_count,
    )
    payload = np.asarray(packet.samples, dtype="<f4").tobytes(order="C")
    body = header + payload
    return body + _CHECKSUM.pack(zlib.crc32(body) & 0xFFFFFFFF)


class BinaryPacketParser:
    """Incrementally reassemble fragmented binary packets and resynchronize."""

    def __init__(self, *, maximum_channels: int = 256, maximum_samples: int = 1_000_000) -> None:
        self.maximum_channels = maximum_channels
        self.maximum_samples = maximum_samples
        self._buffer = bytearray()
        self.corrupted_packets = 0
        self.discarded_bytes = 0

    def reset(self) -> None:
        self._buffer.clear()
        self.corrupted_packets = 0
        self.discarded_bytes = 0

    def feed(self, data: bytes) -> tuple[SensorPacket, ...]:
        self._buffer.extend(data)
        packets: list[SensorPacket] = []
        while True:
            magic_index = self._buffer.find(BINARY_MAGIC)
            if magic_index < 0:
                retain = min(len(self._buffer), len(BINARY_MAGIC) - 1)
                discarded = len(self._buffer) - retain
                if discarded:
                    del self._buffer[:discarded]
                    self.discarded_bytes += discarded
                break
            if magic_index:
                del self._buffer[:magic_index]
                self.discarded_bytes += magic_index
            if len(self._buffer) < _HEADER.size:
                break
            magic, version, sequence, timestamp, channels, samples = _HEADER.unpack_from(
                self._buffer
            )
            if (
                magic != BINARY_MAGIC
                or version != BINARY_VERSION
                or channels < 1
                or channels > self.maximum_channels
                or samples < 1
                or samples > self.maximum_samples
                or not np.isfinite(timestamp)
            ):
                self.corrupted_packets += 1
                del self._buffer[0]
                continue
            payload_size = channels * samples * np.dtype("<f4").itemsize
            packet_size = _HEADER.size + payload_size + _CHECKSUM.size
            if len(self._buffer) < packet_size:
                break
            body = bytes(self._buffer[: _HEADER.size + payload_size])
            expected_checksum = _CHECKSUM.unpack_from(self._buffer, _HEADER.size + payload_size)[0]
            if zlib.crc32(body) & 0xFFFFFFFF != expected_checksum:
                self.corrupted_packets += 1
                del self._buffer[0]
                continue
            payload = np.frombuffer(body, dtype="<f4", offset=_HEADER.size).copy()
            if not np.all(np.isfinite(payload)):
                self.corrupted_packets += 1
                del self._buffer[:packet_size]
                continue
            packets.append(SensorPacket(sequence, timestamp, payload.reshape(samples, channels)))
            del self._buffer[:packet_size]
        return tuple(packets)


class CSVPacketParser:
    """Parse ``sequence,timestamp,ch1,...,chN`` newline-delimited samples."""

    def __init__(self, channel_count: int) -> None:
        if channel_count < 1:
            raise ValueError("channel_count must be positive")
        self.channel_count = channel_count
        self._buffer = bytearray()
        self.corrupted_packets = 0

    def reset(self) -> None:
        self._buffer.clear()
        self.corrupted_packets = 0

    def feed(self, data: bytes) -> tuple[SensorPacket, ...]:
        self._buffer.extend(data)
        packets: list[SensorPacket] = []
        while b"\n" in self._buffer:
            raw, _, remainder = self._buffer.partition(b"\n")
            self._buffer = bytearray(remainder)
            raw = raw.strip()
            if not raw:
                continue
            try:
                fields = raw.decode("ascii").split(",")
                if len(fields) != self.channel_count + 2:
                    raise ValueError("wrong field count")
                sequence = int(fields[0])
                timestamp = float(fields[1])
                values = np.asarray([float(value) for value in fields[2:]], dtype=np.float32)
                packets.append(SensorPacket(sequence, timestamp, values.reshape(1, -1)))
            except (UnicodeDecodeError, ValueError, OverflowError):
                self.corrupted_packets += 1
        return tuple(packets)


def encode_csv_packet(packet: SensorPacket) -> bytes:
    if packet.samples.shape[0] != 1:
        raise ValueError("CSV packets contain exactly one sample per channel")
    fields = [str(packet.sequence), format(packet.timestamp, ".9g")]
    fields.extend(format(float(value), ".9g") for value in packet.samples[0])
    return (",".join(fields) + "\n").encode("ascii")
