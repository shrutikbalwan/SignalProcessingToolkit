from __future__ import annotations

from abc import ABC, abstractmethod
from collections import deque
from collections.abc import Callable
from typing import Generic, Optional, TypeVar

from src.models.signal import Signal

T = TypeVar("T")


class UndoableCommand(ABC, Generic[T]):
    @abstractmethod
    def execute(self) -> T: ...

    @abstractmethod
    def undo(self) -> T: ...

    @abstractmethod
    def redo(self) -> T: ...

    @property
    @abstractmethod
    def description(self) -> str: ...


class SignalCommand(UndoableCommand[Optional[Signal]]):
    def __init__(
        self,
        description: str,
        execute_fn: Callable,
        undo_fn: Optional[Callable] = None,
        redo_fn: Optional[Callable] = None,
    ) -> None:
        self._description = description
        self._execute_fn = execute_fn
        self._undo_fn = undo_fn
        self._redo_fn = redo_fn
        self._result: Optional[Signal] = None
        self._previous: Optional[Signal] = None

    def execute(self) -> Optional[Signal]:
        result = self._execute_fn()
        if result is not None:
            self._result = result
        return self._result

    def undo(self) -> Optional[Signal]:
        if self._undo_fn:
            result = self._undo_fn()
            return result if isinstance(result, Signal) else self._previous
        return self._previous

    def redo(self) -> Optional[Signal]:
        if self._redo_fn:
            result = self._redo_fn()
            return result if isinstance(result, Signal) else self.execute()
        return self.execute()

    @property
    def description(self) -> str:
        return self._description


class UndoRedoManager:
    def __init__(self, max_history: int = 50) -> None:
        self._undo_stack: deque[SignalCommand] = deque(maxlen=max_history)
        self._redo_stack: deque[SignalCommand] = deque(maxlen=max_history)
        self._max_history = max_history

    def execute(self, command: SignalCommand) -> Optional[Signal]:
        result = command.execute()
        self._undo_stack.append(command)
        self._redo_stack.clear()
        return result

    def undo(self) -> Optional[Signal]:
        if not self._undo_stack:
            return None
        command = self._undo_stack.pop()
        result = command.undo()
        self._redo_stack.append(command)
        return result

    def redo(self) -> Optional[Signal]:
        if not self._redo_stack:
            return None
        command = self._redo_stack.pop()
        result = command.redo()
        self._undo_stack.append(command)
        return result

    @property
    def can_undo(self) -> bool:
        return len(self._undo_stack) > 0

    @property
    def can_redo(self) -> bool:
        return len(self._redo_stack) > 0

    @property
    def undo_description(self) -> str:
        if self._undo_stack:
            return f"Undo {self._undo_stack[-1].description}"
        return ""

    @property
    def redo_description(self) -> str:
        if self._redo_stack:
            return f"Redo {self._redo_stack[-1].description}"
        return ""

    def clear(self) -> None:
        self._undo_stack.clear()
        self._redo_stack.clear()
