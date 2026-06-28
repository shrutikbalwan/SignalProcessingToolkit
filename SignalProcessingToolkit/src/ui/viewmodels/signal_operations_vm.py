from __future__ import annotations

from src.core.history import SignalCommand, UndoRedoManager
from src.models.signal import Signal
from src.services.signal_service import SignalService
from src.ui.viewmodels.base_viewmodel import BaseViewModel, Observable


class SignalOperationsViewModel(BaseViewModel):
    def __init__(
        self,
        signal_service: SignalService,
        undo_manager: UndoRedoManager | None = None,
    ) -> None:
        super().__init__()
        self._signal_service = signal_service
        self._undo_manager = undo_manager or UndoRedoManager()

        self.operation = Observable[str]("add")
        self.input_a = Observable[Signal | None](None)
        self.input_b = Observable[Signal | None](None)
        self.active_signals = Observable[list[Signal]]([])

        self.scale_factor = Observable[float](1.0)
        self.shift_samples = Observable[int](0)
        self.clip_min = Observable[float](-1.0)
        self.clip_max = Observable[float](1.0)
        self.rectify_half = Observable[str]("full")
        self.mix_weights = Observable[list[float]]([])

        self.output = Observable[Signal | None](None)
        self.status_message = Observable[str]("")

        self._available_operations = [
            "add",
            "subtract",
            "multiply",
            "scale",
            "normalize",
            "time_shift",
            "time_reverse",
            "clip",
            "rectify",
            "mix",
        ]

    @property
    def available_operations(self) -> list[str]:
        return self._available_operations

    def execute(self) -> Signal | None:
        op = self.operation.value
        a = self.input_a.value

        if op in ("add", "subtract", "multiply") and a is None:
            self.status_message.value = "Select an input signal"
            return None

        command = SignalCommand(
            description=f"{op} operation",
            execute_fn=lambda: self._do_execute(op, a),
        )
        result = self._undo_manager.execute(command)
        self.output.value = result
        self.status_message.value = f"Executed: {op}"
        return result

    def _do_execute(self, op: str, a: Signal | None) -> Signal | None:
        if a is None:
            return None
        b = self.input_b.value

        if op == "add":
            return self._signal_service.add(a, b) if b else a
        elif op == "subtract":
            return self._signal_service.subtract(a, b) if b else a
        elif op == "multiply":
            return self._signal_service.multiply(a, b) if b else a
        elif op == "scale":
            return self._signal_service.scale(a, self.scale_factor.value)
        elif op == "normalize":
            return self._signal_service.normalize(a)
        elif op == "time_shift":
            return self._signal_service.time_shift(a, self.shift_samples.value)
        elif op == "time_reverse":
            return self._signal_service.time_reverse(a)
        elif op == "clip":
            return self._signal_service.clip(a, self.clip_min.value, self.clip_max.value)
        elif op == "rectify":
            return self._signal_service.rectify(a, self.rectify_half.value)
        elif op == "mix":
            signals = self.active_signals.value
            if len(signals) < 2:
                self.status_message.value = "Need at least 2 signals to mix"
                return None
            weights = self.mix_weights.value or None
            return self._signal_service.mix(signals, weights)
        return None

    def undo(self) -> Signal | None:
        result = self._undo_manager.undo()
        if result is not None:
            self.output.value = result
        self.status_message.value = self._undo_manager.undo_description
        return result

    def redo(self) -> Signal | None:
        result = self._undo_manager.redo()
        if result is not None:
            self.output.value = result
        self.status_message.value = self._undo_manager.redo_description
        return result

    @property
    def can_undo(self) -> bool:
        return self._undo_manager.can_undo

    @property
    def can_redo(self) -> bool:
        return self._undo_manager.can_redo

    def dispose(self) -> None:
        super().dispose()
        self._undo_manager.clear()
        self.output.value = None
