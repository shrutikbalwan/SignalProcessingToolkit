from __future__ import annotations

from pathlib import Path

from src.models.fft_result import FFTResult
from src.models.project import Project
from src.models.signal import Signal
from src.plots.base import BasePlotWidget
from src.services.export_service import ExportOptions, ExportService
from src.ui.viewmodels.base_viewmodel import BaseViewModel, Observable


class ExportViewModel(BaseViewModel):
    def __init__(self, export_service: ExportService) -> None:
        super().__init__()
        self._service = export_service

        self.signal = Observable[Signal | None](None)
        self.fft_result = Observable[FFTResult | None](None)
        self.plot_widgets = Observable[list[BasePlotWidget]]([])
        self.project = Observable[Project | None](None)

        self.export_format = Observable[str]("csv")
        self.include_metadata = Observable[bool](True)
        self.precision = Observable[int](6)
        self.dpi = Observable[int](150)

        self.status_message = Observable[str]("")

    def export_signal(self, path: Path) -> bool:
        signal = self.signal.value
        if signal is None:
            self.status_message.value = "No signal to export"
            return False
        opts = ExportOptions(
            format=self.export_format.value,
            include_metadata=self.include_metadata.value,
            precision=self.precision.value,
            dpi=self.dpi.value,
        )
        try:
            self._service.export_signal(signal, path, opts)
            self.status_message.value = f"Exported to {path.name}"
            return True
        except Exception as e:
            self.status_message.value = f"Export failed: {e}"
            return False

    def export_plot(self, plot: BasePlotWidget, path: Path) -> bool:
        try:
            self._service.export_plot(plot, path, dpi=self.dpi.value)
            self.status_message.value = f"Plot saved to {path.name}"
            return True
        except Exception as e:
            self.status_message.value = f"Plot export failed: {e}"
            return False

    def export_report(self, path: Path, title: str = "Signal Processing Report") -> bool:
        try:
            self._service.export_report_pdf(
                self.signal.value,
                self.fft_result.value,
                self.plot_widgets.value,
                path,
                title,
            )
            self.status_message.value = f"Report saved to {path.name}"
            return True
        except Exception as e:
            self.status_message.value = f"Report failed: {e}"
            return False

    def save_project(self) -> bool:
        proj = self.project.value
        if proj is None:
            self.status_message.value = "No project to save"
            return False
        try:
            self._service.save_project(proj)
            self.status_message.value = f"Project saved: {proj.name}"
            return True
        except Exception as e:
            self.status_message.value = f"Project save failed: {e}"
            return False

    def dispose(self) -> None:
        super().dispose()
