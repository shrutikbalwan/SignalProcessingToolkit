from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Callable
from typing import Generic, TypeVar

T = TypeVar("T")


class Observable(Generic[T]):
    def __init__(self, value: T) -> None:
        self._value = value
        self._observers: list[Callable[[T], None]] = []

    @property
    def value(self) -> T:
        return self._value

    @value.setter
    def value(self, new_value: T) -> None:
        if self._value != new_value:
            self._value = new_value
            for observer in self._observers:
                observer(new_value)

    def observe(self, callback: Callable[[T], None]) -> None:
        self._observers.append(callback)

    def unobserve(self, callback: Callable[[T], None]) -> None:
        self._observers.remove(callback)


class BaseViewModel(ABC):
    def __init__(self) -> None:
        self._disposed = False

    @abstractmethod
    def dispose(self) -> None:
        self._disposed = True

    @property
    def is_disposed(self) -> bool:
        return self._disposed
