from PyQt6.QtWidgets import QApplication

from signal_processing_toolkit.dashboard.widgets.source_selector import SourceSelector


def test_source_selector_emits_selected_source(qapp: QApplication) -> None:
    selector = SourceSelector()
    selected: list[str] = []
    selector.source_requested.connect(selected.append)
    selector.source.setCurrentIndex(1)
    selector.refresh.click()
    assert selected == ["audio"]
