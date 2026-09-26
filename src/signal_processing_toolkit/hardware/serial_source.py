"""Optional serial sensor source with bounded automatic reconnection."""

from __future__ import annotations

import threading
import time
from collections import deque
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, replace
from typing import Any, Protocol, cast

import numpy as np

from signal_processing_toolkit.hardware.protocol import (
    BinaryPacketParser,
    CSVPacketParser,
    SensorPacket,
)
from signal_processing_toolkit.streaming.model import ChannelMetadata, SessionEvent, StreamChunk


@dataclass(frozen=True, slots=True)
class SerialPortInfo:
    device: str
    description: str = ""
    hardware_id: str = ""


@dataclass(frozen=True, slots=True)
class SerialSourceConfig:
    port: str
    baud_rate: int = 115_200
    packet_format: str = "binary"
    sampling_rate: float = 1_000.0
    channel_names: tuple[str, ...] = ("sensor_1",)
    units: tuple[str, ...] | str = ""
    timeout: float = 0.1
    read_size: int = 4096
    reconnect_attempts: int = 3
    reconnect_initial_delay: float = 0.05
    reconnect_max_delay: float = 1.0

    def __post_init__(self) -> None:
        if not self.port.strip():
            raise ValueError("serial port cannot be empty")
        if self.baud_rate < 1:
            raise ValueError("baud_rate must be positive")
        if self.packet_format not in {"binary", "csv"}:
            raise ValueError("packet_format must be 'binary' or 'csv'")
        if not np.isfinite(self.sampling_rate) or self.sampling_rate <= 0:
            raise ValueError("sampling_rate must be finite and positive")
        if not self.channel_names or any(not name.strip() for name in self.channel_names):
            raise ValueError("channel_names must be non-empty")
        if self.timeout <= 0 or self.read_size < 1:
            raise ValueError("timeout and read_size must be positive")
        if self.reconnect_attempts < 0:
            raise ValueError("reconnect_attempts cannot be negative")
        if self.reconnect_initial_delay < 0 or self.reconnect_max_delay < 0:
            raise ValueError("reconnect delays cannot be negative")


@dataclass(frozen=True, slots=True)
class SerialSourceMetrics:
    received_packets: int
    corrupted_packets: int
    missing_packets: int
    out_of_order_packets: int
    disconnects: int
    reconnects: int


class SerialConnection(Protocol):
    def read(self, size: int) -> bytes: ...

    def close(self) -> None: ...


class SerialBackend(Protocol):
    def list_ports(self) -> Sequence[SerialPortInfo]: ...

    def open(self, config: SerialSourceConfig) -> SerialConnection: ...


class PySerialBackend:
    """Lazy adapter for the optional pyserial dependency."""

    @staticmethod
    def _modules():
        try:
            import serial
            from serial.tools import list_ports
        except ModuleNotFoundError as error:
            raise RuntimeError(
                "Serial acquisition requires the 'hardware' extra: "
                'pip install "signal-processing-toolkit[hardware]"'
            ) from error
        return serial, list_ports

    def list_ports(self) -> Sequence[SerialPortInfo]:
        _, list_ports = self._modules()
        return tuple(
            SerialPortInfo(item.device, item.description or "", item.hwid or "")
            for item in list_ports.comports()
        )

    def open(self, config: SerialSourceConfig) -> SerialConnection:
        serial, _ = self._modules()
        return cast(
            SerialConnection,
            serial.Serial(config.port, config.baud_rate, timeout=config.timeout),
        )


def enumerate_serial_ports(backend: SerialBackend | None = None) -> tuple[SerialPortInfo, ...]:
    return tuple((backend or PySerialBackend()).list_ports())


class SerialSensorSource:
    """Read CSV or checksummed binary packets from a reconnecting serial link."""

    def __init__(
        self,
        config: SerialSourceConfig,
        *,
        backend: SerialBackend | None = None,
    ) -> None:
        self.config = config
        self.backend = backend or PySerialBackend()
        self._connection: SerialConnection | None = None
        self._parser: BinaryPacketParser | CSVPacketParser
        self._pending: deque[SensorPacket] = deque()
        self._events: deque[SessionEvent] = deque()
        self._event_lock = threading.Lock()
        self._last_sequence: int | None = None
        self._closed = False
        self._has_connected = False
        self._received = 0
        self._corrupted = 0
        self._missing = 0
        self._out_of_order = 0
        self._disconnects = 0
        self._reconnects = 0
        self._make_parser()

    def _make_parser(self) -> None:
        self._parser = (
            BinaryPacketParser()
            if self.config.packet_format == "binary"
            else CSVPacketParser(len(self.config.channel_names))
        )

    @property
    def exhausted(self) -> bool:
        return self._closed

    def configure(self, settings: Mapping[str, Any] | None = None) -> None:
        if self._connection is not None:
            self._connection.close()
            self._connection = None
        if settings:
            self.config = replace(self.config, **dict(settings))
        self._make_parser()

    def _event(self, kind: str, **details: Any) -> None:
        event = SessionEvent(kind, details=details)
        with self._event_lock:
            self._events.append(event)

    def drain_events(self) -> tuple[SessionEvent, ...]:
        with self._event_lock:
            events = tuple(self._events)
            self._events.clear()
        return events

    def _connect(self, cancel: threading.Event) -> None:
        last_error: BaseException | None = None
        for attempt in range(self.config.reconnect_attempts + 1):
            if cancel.is_set() or self._closed:
                return
            if attempt:
                delay = min(
                    self.config.reconnect_initial_delay * (2 ** (attempt - 1)),
                    self.config.reconnect_max_delay,
                )
                if cancel.wait(delay):
                    return
            try:
                self._connection = self.backend.open(self.config)
            except (OSError, ConnectionError) as error:
                last_error = error
                self._event("connection_attempt_failed", attempt=attempt + 1, error=str(error))
                continue
            reconnect = self._has_connected
            self._has_connected = True
            self._reconnects += int(reconnect)
            self._event("reconnected" if reconnect else "connected", port=self.config.port)
            return
        raise ConnectionError(
            f"Unable to connect to {self.config.port} after "
            f"{self.config.reconnect_attempts + 1} attempt(s)"
        ) from last_error

    def _disconnect(self, error: BaseException) -> None:
        self._disconnects += 1
        self._event("disconnected", port=self.config.port, error=str(error))
        if self._connection is not None:
            self._connection.close()
        self._connection = None

    def _packet_to_chunk(self, packet: SensorPacket) -> StreamChunk:
        channels = packet.samples.shape[1]
        configured_names = self.config.channel_names
        names = (
            configured_names
            if len(configured_names) == channels
            else tuple(f"sensor_{index + 1}" for index in range(channels))
        )
        configured_units = self.config.units
        units = (
            (configured_units,) * channels
            if isinstance(configured_units, str)
            else configured_units
        )
        if len(units) != channels:
            raise ValueError("units must contain one value per packet channel")
        missing = 0
        out_of_order = False
        if self._last_sequence is not None:
            expected = (self._last_sequence + 1) & 0xFFFFFFFF
            distance = (packet.sequence - expected) & 0xFFFFFFFF
            if distance == 0:
                pass
            elif distance < 0x80000000:
                missing = distance
                self._missing += missing
            else:
                out_of_order = True
                self._out_of_order += 1
        if not out_of_order:
            self._last_sequence = packet.sequence
        self._received += 1
        return StreamChunk(
            packet.samples,
            self.config.sampling_rate,
            tuple(ChannelMetadata(name, unit) for name, unit in zip(names, units, strict=True)),
            packet.sequence,
            packet.timestamp,
            time.time(),
            {
                "source": "serial",
                "port": self.config.port,
                "packet_format": self.config.packet_format,
                "missing_before": missing,
                "out_of_order": out_of_order,
            },
        )

    def read(self, cancel: threading.Event) -> StreamChunk | None:
        while not cancel.is_set() and not self._closed:
            if self._pending:
                return self._packet_to_chunk(self._pending.popleft())
            if self._connection is None:
                self._connect(cancel)
                if self._connection is None:
                    return None
            try:
                data = self._connection.read(self.config.read_size)
            except (OSError, ConnectionError) as error:
                self._disconnect(error)
                continue
            if not data:
                return None
            previous_corruption = self._parser.corrupted_packets
            self._pending.extend(self._parser.feed(data))
            new_corruption = self._parser.corrupted_packets - previous_corruption
            if new_corruption:
                self._corrupted += new_corruption
                self._event("corrupted_packet", count=new_corruption)
        return None

    def reset(self) -> None:
        if self._connection is not None:
            self._connection.close()
        self._connection = None
        self._pending.clear()
        self._make_parser()
        self._last_sequence = None
        self._closed = False
        self._has_connected = False
        self._received = self._corrupted = self._missing = self._out_of_order = 0
        self._disconnects = self._reconnects = 0
        self.drain_events()

    def close(self) -> None:
        self._closed = True
        if self._connection is not None:
            self._connection.close()
            self._connection = None
        self._event("closed", port=self.config.port)

    @property
    def metrics(self) -> SerialSourceMetrics:
        return SerialSourceMetrics(
            self._received,
            self._corrupted,
            self._missing,
            self._out_of_order,
            self._disconnects,
            self._reconnects,
        )
