"""Qt thread-pool helpers for CPU-bound or blocking UI actions."""

from __future__ import annotations

import logging
import threading
from collections.abc import Callable
from typing import Any

from PyQt6.QtCore import QObject, QRunnable, QThreadPool, pyqtSignal, pyqtSlot

logger = logging.getLogger(__name__)


class WorkerSignals(QObject):
    result = pyqtSignal(object)
    error = pyqtSignal(str)
    finished = pyqtSignal()


class TaskCancelledError(Exception):
    """Internal cooperative-cancellation signal."""


class CancellationToken:
    def __init__(self) -> None:
        self._event = threading.Event()

    @property
    def is_cancelled(self) -> bool:
        return self._event.is_set()

    def cancel(self) -> None:
        self._event.set()

    def raise_if_cancelled(self) -> None:
        if self.is_cancelled:
            raise TaskCancelledError


class FunctionWorker(QRunnable):
    def __init__(self, function: Callable[[CancellationToken], Any]) -> None:
        super().__init__()
        self.function = function
        self.token = CancellationToken()
        self.signals = WorkerSignals()

    @pyqtSlot()
    def run(self) -> None:
        try:
            self.token.raise_if_cancelled()
            result = self.function(self.token)
            self.token.raise_if_cancelled()
        except TaskCancelledError:
            logger.debug("Background processing cancelled")
        except Exception as exc:
            logger.exception("Background processing failed")
            self.signals.error.emit(str(exc))
        else:
            self.signals.result.emit(result)
        finally:
            self.signals.finished.emit()


class TaskRunner(QObject):
    """Own submitted workers and marshal their results back to the UI thread."""

    busy_changed = pyqtSignal(bool)
    error = pyqtSignal(str)

    def __init__(self, parent: QObject | None = None) -> None:
        super().__init__(parent)
        pool = QThreadPool.globalInstance()
        if pool is None:
            raise RuntimeError("Qt global thread pool is unavailable")
        self._pool: QThreadPool = pool
        self._workers: set[FunctionWorker] = set()
        self._closing = False

    def submit(
        self,
        function: Callable[[], Any],
        on_result: Callable[[Any], None],
        on_error: Callable[[str], None] | None = None,
    ) -> bool:
        return self.submit_cancellable(lambda token: function(), on_result, on_error)

    def submit_cancellable(
        self,
        function: Callable[[CancellationToken], Any],
        on_result: Callable[[Any], None],
        on_error: Callable[[str], None] | None = None,
    ) -> bool:
        if self._workers or self._closing:
            return False
        worker = FunctionWorker(function)
        self._workers.add(worker)
        worker.signals.result.connect(on_result)
        worker.signals.error.connect(on_error or self.error.emit)
        worker.signals.finished.connect(lambda: self._finish(worker))
        self.busy_changed.emit(True)
        self._pool.start(worker)
        return True

    def _finish(self, worker: FunctionWorker) -> None:
        self._workers.discard(worker)
        self.busy_changed.emit(bool(self._workers))

    def wait_for_done(self, timeout_ms: int = 5000) -> bool:
        return bool(self._pool.waitForDone(timeout_ms))

    def cancel_all(self) -> None:
        for worker in tuple(self._workers):
            worker.token.cancel()

    def shutdown(self, timeout_ms: int = 5000) -> bool:
        """Cancel cooperative jobs and wait for the shared pool to become idle."""
        self._closing = True
        self.cancel_all()
        completed = self.wait_for_done(timeout_ms)
        if completed:
            self._workers.clear()
            self.busy_changed.emit(False)
        return completed

    @property
    def is_busy(self) -> bool:
        return bool(self._workers)
