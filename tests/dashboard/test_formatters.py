from signal_processing_toolkit.dashboard.formatters import duration, percentage, value


def test_formatters_handle_values_and_unavailable() -> None:
    assert value(1.23456, "V", 2) == "1.23 V"
    assert value(None) == "—"
    assert percentage(0.875) == "87.5 %"
    assert duration(65.5) == "01:05.5"
