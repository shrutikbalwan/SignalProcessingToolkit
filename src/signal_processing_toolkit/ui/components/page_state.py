"""Reusable visible empty, loading, error, and content states."""

from __future__ import annotations

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QLabel, QProgressBar, QStackedWidget, QVBoxLayout, QWidget


class StatefulPage(QWidget):
    """Wrap a page with explicit user-visible lifecycle states."""

    def __init__(
        self,
        content: QWidget,
        *,
        empty_message: str,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self.setObjectName(f"{content.objectName() or content.__class__.__name__}StatefulPage")
        self._stack = QStackedWidget(self)
        self._empty = self._message_label(empty_message, "emptyStateLabel")

        loading_page = QWidget(self)
        loading_layout = QVBoxLayout(loading_page)
        loading_layout.addStretch()
        self._loading_label = self._message_label("Processing…", "loadingStateLabel")
        loading_layout.addWidget(self._loading_label)
        progress = QProgressBar(loading_page)
        progress.setRange(0, 0)
        progress.setAccessibleName("Processing progress")
        loading_layout.addWidget(progress)
        loading_layout.addStretch()

        self._error = self._message_label("", "errorStateLabel")
        self.content = content
        self._stack.addWidget(self._empty)
        self._stack.addWidget(loading_page)
        self._stack.addWidget(self._error)
        self._stack.addWidget(content)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self._stack)
        self.show_empty()

    @staticmethod
    def _message_label(text: str, object_name: str) -> QLabel:
        label = QLabel(text)
        label.setObjectName(object_name)
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        label.setWordWrap(True)
        label.setAccessibleName(text or "Page error")
        return label

    def show_empty(self, message: str | None = None) -> None:
        if message is not None:
            self._empty.setText(message)
            self._empty.setAccessibleName(message)
        self._stack.setCurrentIndex(0)

    def show_loading(self, message: str = "Processing…") -> None:
        self._loading_label.setText(message)
        self._loading_label.setAccessibleName(message)
        self._stack.setCurrentIndex(1)

    def show_error(self, message: str) -> None:
        self._error.setText(f"Error: {message}")
        self._error.setAccessibleName(f"Error: {message}")
        self._stack.setCurrentIndex(2)

    def show_content(self) -> None:
        self._stack.setCurrentIndex(3)

    @property
    def state(self) -> str:
        return ("empty", "loading", "error", "content")[self._stack.currentIndex()]
