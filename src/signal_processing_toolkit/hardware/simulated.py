"""Dependency-free simulated serial devices for tests and demonstrations."""

from __future__ import annotations

from collections import deque
from collections.abc import Iterable, Sequence

from signal_processing_toolkit.hardware.serial_source import (
    SerialConnection,
    SerialPortInfo,
    SerialSourceConfig,
)


class SimulatedSerialConnection:
    def __init__(self, fragments: Iterable[bytes | BaseException]) -> None:
        self._fragments = deque(fragments)
        self.closed = False

    def read(self, size: int) -> bytes:
        if self.closed:
            raise ConnectionError("simulated port is closed")
        if not self._fragments:
            return b""
        item = self._fragments.popleft()
        if isinstance(item, BaseException):
            raise item
        if len(item) > size:
            self._fragments.appendleft(item[size:])
            return item[:size]
        return item

    def close(self) -> None:
        self.closed = True


class SimulatedSerialBackend:
    """Return scripted connections or failures on successive open calls."""

    def __init__(
        self,
        scripts: Iterable[SerialConnection | BaseException],
        *,
        ports: Sequence[SerialPortInfo] = (SerialPortInfo("SIM0", "Simulated sensor"),),
    ) -> None:
        self._scripts = deque(scripts)
        self._ports = tuple(ports)
        self.open_count = 0

    def list_ports(self) -> Sequence[SerialPortInfo]:
        return self._ports

    def open(self, config: SerialSourceConfig) -> SerialConnection:
        del config
        self.open_count += 1
        if not self._scripts:
            raise ConnectionError("no simulated connection remains")
        item = self._scripts.popleft()
        if isinstance(item, BaseException):
            raise item
        return item
