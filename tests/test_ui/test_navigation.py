from __future__ import annotations

from signal_processing_toolkit.ui.components.sidebar import NAV_ITEMS


def test_every_sidebar_item_selects_its_exact_page(main_window, qtbot) -> None:
    for row, descriptor in enumerate(NAV_ITEMS):
        main_window.sidebar.list_widget.setCurrentRow(row)
        qtbot.waitUntil(lambda row=row: main_window.stacked_widget.currentIndex() == row)
        assert main_window.stacked_widget.currentWidget() is main_window.pages[descriptor.key]
        assert (
            main_window.stacked_widget.currentWidget().property("navigationKey") == descriptor.key
        )


def test_page_registry_matches_sidebar_exactly(main_window) -> None:
    expected = [item.key for item in NAV_ITEMS]
    assert list(main_window.pages) == expected
    assert main_window.stacked_widget.count() == len(expected)
    assert len({id(page) for page in main_window.pages.values()}) == len(expected)
