from __future__ import annotations

from pathlib import Path

from PyQt6.QtWidgets import QWidget


class PlotExporter:
    @staticmethod
    def export_png(plot_widget: QWidget, path: Path) -> None:

        pixmap = plot_widget.grab()
        pixmap.save(str(path), "PNG")

    @staticmethod
    def export_svg(plot_widget: QWidget, path: Path) -> None:
        import pyqtgraph.exporters as exporters

        plot_item = getattr(plot_widget, "plotItem", None)
        if plot_item is None:
            raise ValueError("Plot widget does not have a plotItem")
        exporter = exporters.SVGExporter(plot_item)
        exporter.export(str(path))
