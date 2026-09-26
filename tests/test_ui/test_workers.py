from __future__ import annotations

import threading
import time

from PyQt6.QtCore import QObject, pyqtSlot

from signal_processing_toolkit.ui.workers import TaskRunner


class ThreadRecordingReceiver(QObject):
    def __init__(self) -> None:
        super().__init__()
        self.worker_thread: int | None = None
        self.callback_thread: int | None = None

    @pyqtSlot(object)
    def receive(self, worker_thread: int) -> None:
        self.worker_thread = worker_thread
        self.callback_thread = threading.get_ident()


def test_task_runner_executes_work_outside_the_ui_thread(qtbot) -> None:
    main_thread = threading.get_ident()
    receiver = ThreadRecordingReceiver()
    runner = TaskRunner()

    assert runner.submit(threading.get_ident, receiver.receive)
    qtbot.waitUntil(lambda: receiver.worker_thread is not None and not runner.is_busy)

    assert receiver.worker_thread != main_thread
    assert receiver.callback_thread == main_thread
    assert not runner.is_busy


def test_task_runner_cooperatively_cancels_and_suppresses_results(qtbot) -> None:
    runner = TaskRunner()
    results: list[str] = []

    def work(token) -> str:
        while not token.is_cancelled:
            time.sleep(0.001)
        token.raise_if_cancelled()
        return "unexpected"

    assert runner.submit_cancellable(work, results.append)
    qtbot.waitUntil(lambda: runner.is_busy)
    assert runner.shutdown(timeout_ms=2000)
    qtbot.wait(20)
    assert not runner.is_busy
    assert results == []
    assert not runner.submit(lambda: "late", results.append)
