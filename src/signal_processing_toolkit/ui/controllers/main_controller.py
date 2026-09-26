from __future__ import annotations

import logging
from collections import OrderedDict
from pathlib import Path
from typing import Any

from PyQt6.QtWidgets import QLabel, QVBoxLayout, QWidget

from signal_processing_toolkit.core.application_state import ApplicationState, SignalStateChange
from signal_processing_toolkit.core.events import EventBus
from signal_processing_toolkit.core.history import UndoRedoManager
from signal_processing_toolkit.dashboard.controller import DashboardController
from signal_processing_toolkit.dashboard.view import DashboardView
from signal_processing_toolkit.models.signal import Signal
from signal_processing_toolkit.services.signal_service import SignalService
from signal_processing_toolkit.ui.components.page_state import StatefulPage
from signal_processing_toolkit.ui.components.sidebar import NAV_ITEMS
from signal_processing_toolkit.ui.controllers.convolution_controller import ConvolutionController
from signal_processing_toolkit.ui.controllers.correlation_controller import CorrelationController
from signal_processing_toolkit.ui.controllers.export_controller import ExportController
from signal_processing_toolkit.ui.controllers.fft_controller import FFTController
from signal_processing_toolkit.ui.controllers.filters_controller import FilterController
from signal_processing_toolkit.ui.controllers.noise_controller import NoiseController
from signal_processing_toolkit.ui.controllers.sampling_controller import SamplingController
from signal_processing_toolkit.ui.controllers.settings_controller import SettingsController
from signal_processing_toolkit.ui.controllers.signal_generator_controller import (
    SignalGeneratorController,
)
from signal_processing_toolkit.ui.controllers.signal_operations_controller import (
    SignalOperationsController,
)
from signal_processing_toolkit.ui.controllers.windows_controller import WindowController
from signal_processing_toolkit.ui.views.analysis_view import AnalysisView
from signal_processing_toolkit.ui.views.edge_ai_view import EdgeAIView
from signal_processing_toolkit.ui.views.monitor_view import LiveMonitorView
from signal_processing_toolkit.ui.views.pipeline_editor_view import PipelineEditorView
from signal_processing_toolkit.ui.workers import TaskRunner

logger = logging.getLogger(__name__)


class MainController:
    """Compose pages and propagate a single authoritative signal state."""

    def __init__(
        self,
        event_bus: EventBus,
        state: ApplicationState | None = None,
        settings_path: Path | None = None,
    ) -> None:
        self.event_bus = event_bus
        self.state = state or ApplicationState()
        self.signal_service = SignalService()
        self.undo_manager = UndoRedoManager()
        self.signal_generator = SignalGeneratorController(event_bus, self.signal_service)
        self.signal_operations = SignalOperationsController(
            event_bus, self.signal_service, self.undo_manager
        )
        self.sampling = SamplingController(event_bus)
        self.convolution = ConvolutionController(event_bus)
        self.correlation = CorrelationController(event_bus)
        self.fft = FFTController(event_bus)
        self.windows = WindowController(event_bus)
        self.filters = FilterController(event_bus)
        self.noise = NoiseController(event_bus)
        self.audio = self._create_audio_controller(event_bus)
        self.image = self._create_image_controller(event_bus)
        self.export = ExportController(event_bus)
        self.settings = SettingsController(event_bus, settings_path)
        self.dashboard_controller = DashboardController()
        self.dashboard = DashboardView(self.dashboard_controller)
        self.analysis = AnalysisView()
        self.edge_ai = EdgeAIView()
        self.pipeline_editor = PipelineEditorView()
        self.monitor = LiveMonitorView()
        self._pages: OrderedDict[str, QWidget] | None = None
        self._stateful_pages: dict[str, StatefulPage] = {}
        self._cleaned_up = False

        self._generated_listener = self._on_generated_signal
        self._operations_listener = self._on_operations_signal
        self.signal_generator._viewmodel.generated_signal.observe(self._generated_listener)
        self.signal_operations._viewmodel.output.observe(self._operations_listener)
        self.state.subscribe(self._propagate_signal)
        for event in ("signal:generated", "signal:loaded", "signal:operations_result"):
            self.event_bus.subscribe(event, self._on_signal_event)
        self.event_bus.subscribe("signal:loading", self._on_signal_loading)
        self.event_bus.subscribe("signal:error", self._on_signal_error)

    @staticmethod
    def _create_audio_controller(event_bus: EventBus) -> Any | None:
        try:
            from signal_processing_toolkit.ui.controllers.audio_controller import AudioController

            return AudioController(event_bus)
        except ImportError as exc:
            logger.info("Audio features unavailable: %s", exc)
            return None

    @staticmethod
    def _create_image_controller(event_bus: EventBus) -> Any | None:
        try:
            from signal_processing_toolkit.ui.controllers.image_controller import ImageController

            return ImageController(event_bus)
        except ImportError as exc:
            logger.info("Image features unavailable: %s", exc)
            return None

    def get_pages(self) -> OrderedDict[str, QWidget]:
        if self._pages is not None:
            return self._pages

        raw_pages: dict[str, QWidget] = {
            "dashboard": self.dashboard,
            "generator": self.signal_generator.get_view(),
            "operations": self.signal_operations.get_view(),
            "sampling": self.sampling.get_view(),
            "convolution": self.convolution.get_view(),
            "correlation": self.correlation.get_view(),
            "fft": self.fft.get_view(),
            "analysis": self.analysis,
            "edge_ai": self.edge_ai,
            "pipelines": self.pipeline_editor,
            "windows": self.windows.get_view(),
            "filters": self.filters.get_view(),
            "noise": self.noise.get_view(),
            "audio": self.audio.get_view()
            if self.audio is not None
            else self._unavailable_page("Audio", "audio"),
            "image": self.image.get_view()
            if self.image is not None
            else self._unavailable_page("Image processing", "image"),
            "monitor": self.monitor,
            "settings": self.settings.get_view(),
        }

        signal_pages = {
            "operations",
            "sampling",
            "convolution",
            "correlation",
            "fft",
            "analysis",
            "windows",
            "filters",
            "noise",
        }
        for key in signal_pages:
            shell = StatefulPage(
                raw_pages[key],
                empty_message="Generate or load a signal to use this page.",
            )
            self._stateful_pages[key] = shell
            for runner in raw_pages[key].findChildren(TaskRunner):
                runner.busy_changed.connect(
                    lambda busy, page=shell: page.show_loading() if busy else page.show_content()
                )
                runner.error.connect(shell.show_error)
            raw_pages[key] = shell

        expected = tuple(item.key for item in NAV_ITEMS)
        if set(raw_pages) != set(expected):
            missing = sorted(set(expected) - set(raw_pages))
            extra = sorted(set(raw_pages) - set(expected))
            raise RuntimeError(f"Navigation/page mismatch: missing={missing}, extra={extra}")
        self._pages = OrderedDict((key, raw_pages[key]) for key in expected)
        if self.state.current_signal is not None:
            self._propagate_signal(SignalStateChange(self.state.current_signal, "initial"))
        return self._pages

    @staticmethod
    def _unavailable_page(feature: str, extra: str) -> QWidget:
        page = QWidget()
        page.setObjectName(f"{extra}UnavailablePage")
        layout = QVBoxLayout(page)
        label = QLabel(f"{feature} requires the '{extra}' optional dependency.")
        label.setWordWrap(True)
        label.setAccessibleName(f"{feature} unavailable")
        layout.addWidget(label)
        layout.addStretch()
        return page

    def page(self, key: str) -> QWidget:
        return self.get_pages()[key]

    def _on_generated_signal(self, signal: Signal | None) -> None:
        if signal is not None:
            self.state.set_current_signal(signal, "generator")

    def _on_operations_signal(self, signal: Signal | None) -> None:
        if signal is not None:
            self.state.set_current_signal(signal, "operations")

    def _on_signal_event(self, signal: Signal | None = None, **kwargs: object) -> None:
        if signal is not None:
            source = str(kwargs.get("source", "event"))
            self.state.set_current_signal(signal, source)

    def _propagate_signal(self, change: SignalStateChange) -> None:
        signal = change.signal
        self.dashboard.set_signal(signal)
        self.edge_ai.set_input_signal(signal)
        self.pipeline_editor.set_input_signal(signal)
        if signal is None:
            for page in self._stateful_pages.values():
                page.show_empty()
            return

        signals = list(self.state.signals)
        operations_vm = self.signal_operations._viewmodel
        operations_vm.active_signals.value = signals
        self.signal_operations.get_view().update_signal_list(signals)
        self.convolution.get_view().update_signal_list(signals)
        self.correlation.get_view().update_signal_list(signals)
        self.sampling.get_view().set_input_signal(signal)
        self.fft.get_view().set_input_signal(signal)
        self.analysis.set_input_signal(signal)
        self.windows.get_view().set_input_signal(signal)
        self.filters.get_view().set_input_signal(signal)
        self.noise.get_view().set_input_signal(signal)
        self.analysis.update_signal_list(signals)
        self.export.get_viewmodel().signal.value = signal
        for page in self._stateful_pages.values():
            page.show_content()
        self.event_bus.publish("state:signal_changed", signal=signal, source=change.source)

    def _on_signal_loading(self, **kwargs: object) -> None:
        del kwargs
        self.dashboard.show_loading()
        for page in self._stateful_pages.values():
            page.show_loading("Loading signal…")

    def _on_signal_error(self, message: str = "Unable to load signal", **kwargs: object) -> None:
        del kwargs
        self.dashboard.show_error(message)
        for page in self._stateful_pages.values():
            page.show_error(message)

    def cleanup(self) -> None:
        if self._cleaned_up:
            return
        self._cleaned_up = True
        self.monitor.shutdown()
        self.dashboard_controller.cleanup()
        if self._pages is not None:
            for page in self._pages.values():
                for runner in page.findChildren(TaskRunner):
                    if not runner.shutdown():
                        logger.warning("Background task did not stop before shutdown timeout")
        self.signal_generator._viewmodel.generated_signal.unobserve(self._generated_listener)
        self.signal_operations._viewmodel.output.unobserve(self._operations_listener)
        self.state.unsubscribe(self._propagate_signal)
        controllers = [
            self.signal_generator,
            self.signal_operations,
            self.sampling,
            self.convolution,
            self.correlation,
            self.fft,
            self.windows,
            self.filters,
            self.noise,
            self.export,
        ]
        if self.audio is not None:
            controllers.append(self.audio)
        if self.image is not None:
            controllers.append(self.image)
        for controller in controllers:
            controller.cleanup()
        self.state.clear()

    @property
    def is_cleaned_up(self) -> bool:
        return self._cleaned_up
