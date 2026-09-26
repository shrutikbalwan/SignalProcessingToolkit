from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Callable


class Observable[T]:
    def __init__(self, value: T) -> None:
        self._value = value
        self._observers: list[Callable[[T], None]] = []

    @property
    def value(self) -> T:
        return self._value

    @value.setter
    def value(self, new_value: T) -> None:
        if self._value is new_value:
            return
        try:
            unchanged = bool(self._value == new_value)
        except (TypeError, ValueError):
            unchanged = False
        if unchanged:
            return
        self._value = new_value
        for observer in tuple(self._observers):
            observer(new_value)

    def observe(self, callback: Callable[[T], None]) -> None:
        if callback not in self._observers:
            self._observers.append(callback)

    def unobserve(self, callback: Callable[[T], None]) -> None:
        if callback in self._observers:
            self._observers.remove(callback)

    def clear_observers(self) -> None:
        self._observers.clear()


class BaseViewModel(ABC):
    def __init__(self) -> None:
        self._disposed = False

    @abstractmethod
    def dispose(self) -> None:
        self._disposed = True

    @property
    def is_disposed(self) -> bool:
        return self._disposed
