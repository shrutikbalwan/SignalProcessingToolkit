from PyQt6.QtWidgets import QApplication

from signal_processing_toolkit.dashboard.widgets.metric_card import MetricCard


def test_metric_card_updates(qapp: QApplication) -> None:
    card = MetricCard("RMS")
    card.set_value("1.0 V")
    assert card.value.text() == "1.0 V"
