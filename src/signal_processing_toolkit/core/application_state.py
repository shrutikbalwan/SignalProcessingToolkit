"""Shared application state for signal-oriented workflows."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass

from signal_processing_toolkit.models.signal import Signal


@dataclass(frozen=True, slots=True)
class SignalStateChange:
    """A current-signal transition and its provenance."""

    signal: Signal | None
    source: str


SignalStateListener = Callable[[SignalStateChange], None]


class ApplicationState:
    """Own signals shared by generation, analysis, processing, and export pages."""

    def __init__(self) -> None:
        self._current_signal: Signal | None = None
        self._signals: list[Signal] = []
        self._listeners: list[SignalStateListener] = []

    @property
    def current_signal(self) -> Signal | None:
        return self._current_signal

    @property
    def signals(self) -> tuple[Signal, ...]:
        return tuple(self._signals)

    def set_current_signal(self, signal: Signal | None, source: str) -> None:
        """Set the active signal and notify each subscriber once."""
        self._current_signal = signal
        if signal is not None:
            signal_id = signal.metadata.id
            self._signals = [item for item in self._signals if item.metadata.id != signal_id]
            self._signals.append(signal)
        change = SignalStateChange(signal=signal, source=source)
        for listener in tuple(self._listeners):
            listener(change)

    def subscribe(self, listener: SignalStateListener) -> None:
        if listener not in self._listeners:
            self._listeners.append(listener)

    def unsubscribe(self, listener: SignalStateListener) -> None:
        if listener in self._listeners:
            self._listeners.remove(listener)

    def clear(self) -> None:
        self._current_signal = None
        self._signals.clear()
        self._listeners.clear()
