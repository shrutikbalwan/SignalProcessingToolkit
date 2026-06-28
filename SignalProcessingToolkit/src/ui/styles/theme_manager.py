from __future__ import annotations

from PyQt6.QtGui import QColor, QPalette
from PyQt6.QtWidgets import QApplication

from src.config import Theme

DARK_STYLESHEET = """
QMainWindow, QWidget {
    background-color: #1e1e1e;
    color: #d4d4d4;
    font-family: "Segoe UI", Arial, sans-serif;
    font-size: 14px;
}

QMenuBar {
    background-color: #2d2d2d;
    color: #d4d4d4;
    border-bottom: 1px solid #3c3c3c;
    padding: 4px;
}

QMenuBar::item:selected {
    background-color: #3c3c3c;
}

QMenu {
    background-color: #2d2d2d;
    color: #d4d4d4;
    border: 1px solid #3c3c3c;
}

QMenu::item:selected {
    background-color: #094771;
}

QToolBar {
    background-color: #2d2d2d;
    border-bottom: 1px solid #3c3c3c;
    spacing: 4px;
    padding: 8px;
}

QPushButton {
    background-color: #0e639c;
    color: white;
    border: none;
    padding: 6px 16px;
    border-radius: 4px;
    font-weight: bold;
}

QPushButton:hover {
    background-color: #1177bb;
}

QPushButton:pressed {
    background-color: #094771;
}

QPushButton#primaryButton {
    background-color: #0e639c;
    color: white;
    padding: 8px 20px;
    border-radius: 6px;
}

QPushButton#primaryButton:hover {
    background-color: #1177bb;
}

QPushButton#secondaryButton {
    background-color: #3c3c3c;
    color: #d4d4d4;
    padding: 6px 16px;
    border-radius: 4px;
    border: 1px solid #555;
}

QPushButton#secondaryButton:hover {
    background-color: #4d4d4d;
}

QListWidget {
    background-color: #252526;
    border: none;
    outline: none;
    color: #cccccc;
}

QListWidget::item {
    padding: 12px 16px;
    border-left: 3px solid transparent;
}

QListWidget::item:selected {
    background-color: #37373d;
    border-left: 3px solid #0e639c;
    color: white;
}

QListWidget::item:hover {
    background-color: #2a2d2e;
}

QStatusBar {
    background-color: #007acc;
    color: white;
    padding: 6px 12px;
    font-size: 13px;
}

QSplitter::handle {
    background-color: #3c3c3c;
    width: 1px;
}

QLabel#sidebarHeader {
    background-color: #2d2d2d;
    color: white;
    padding: 12px 16px;
    border-bottom: 1px solid #3c3c3c;
    font-size: 16px;
    font-weight: bold;
}

QLabel#sectionTitle {
    font-size: 20px;
    font-weight: bold;
    color: #d4d4d4;
    padding: 10px 0;
}

QLabel#cardTitle {
    font-size: 14px;
    font-weight: bold;
    color: #d4d4d4;
}

QLabel#cardValue {
    font-size: 24px;
    font-weight: bold;
}

QLabel#cardUnit {
    font-size: 14px;
    opacity: 0.7;
    color: #999;
}

QLabel#cardIcon {
    font-size: 20px;
    margin-right: 8px;
}

QGroupBox {
    font-weight: bold;
    border: 1px solid #3c3c3c;
    border-radius: 6px;
    margin-top: 10px;
    padding-top: 20px;
    background-color: #252526;
}

QGroupBox::title {
    subcontrol-origin: margin;
    left: 10px;
    padding: 0 5px;
    color: #d4d4d4;
}

QScrollArea {
    border: none;
    background-color: transparent;
}

QDoubleSpinBox, QSpinBox {
    padding: 4px;
    border: 1px solid #3c3c3c;
    border-radius: 4px;
    background-color: #252526;
    color: #d4d4d4;
}

QComboBox {
    padding: 6px 8px;
    border: 1px solid #3c3c3c;
    border-radius: 4px;
    background-color: #252526;
    color: #d4d4d4;
}

QTabWidget::pane {
    border: 1px solid #3c3c3c;
    background-color: #1e1e1e;
}

QTabBar::tab {
    background-color: #2d2d2d;
    color: #d4d4d4;
    padding: 8px 16px;
    margin-right: 2px;
}

QTabBar::tab:selected {
    background-color: #0e639c;
    color: white;
}

QProgressBar {
    background-color: #3c3c3c;
    height: 8px;
    border-radius: 4px;
    text-align: center;
}

QProgressBar::chunk {
    background-color: #0e639c;
    border-radius: 4px;
}

QLineEdit {
    padding: 6px 8px;
    border: 1px solid #3c3c3c;
    border-radius: 4px;
    background-color: #252526;
    color: #d4d4d4;
}

QTextEdit {
    padding: 6px;
    border: 1px solid #3c3c3c;
    border-radius: 4px;
    background-color: #252526;
    color: #d4d4d4;
}
"""

LIGHT_STYLESHEET = """
QMainWindow, QWidget {
    background-color: #ffffff;
    color: #1e1e1e;
    font-family: "Segoe UI", Arial, sans-serif;
    font-size: 14px;
}

QMenuBar {
    background-color: #f3f3f3;
    color: #1e1e1e;
    border-bottom: 1px solid #e0e0e0;
    padding: 4px;
}

QMenuBar::item:selected {
    background-color: #e0e0e0;
}

QMenu {
    background-color: #ffffff;
    color: #1e1e1e;
    border: 1px solid #e0e0e0;
}

QMenu::item:selected {
    background-color: #0078d4;
    color: white;
}

QToolBar {
    background-color: #f3f3f3;
    border-bottom: 1px solid #e0e0e0;
    spacing: 4px;
    padding: 8px;
}

QPushButton {
    background-color: #0078d4;
    color: white;
    border: none;
    padding: 6px 16px;
    border-radius: 4px;
    font-weight: bold;
}

QPushButton:hover {
    background-color: #1a8ad4;
}

QPushButton:pressed {
    background-color: #005a9e;
}

QPushButton#primaryButton {
    background-color: #0078d4;
    color: white;
    padding: 8px 20px;
    border-radius: 6px;
}

QPushButton#primaryButton:hover {
    background-color: #1a8ad4;
}

QPushButton#secondaryButton {
    background-color: #f3f3f3;
    color: #1e1e1e;
    padding: 6px 16px;
    border-radius: 4px;
    border: 1px solid #d0d0d0;
}

QPushButton#secondaryButton:hover {
    background-color: #ebebeb;
}

QListWidget {
    background-color: #f8f8f8;
    border: none;
    outline: none;
    color: #1e1e1e;
}

QListWidget::item {
    padding: 12px 16px;
    border-left: 3px solid transparent;
}

QListWidget::item:selected {
    background-color: #e0e0e0;
    border-left: 3px solid #0078d4;
    color: #1e1e1e;
}

QListWidget::item:hover {
    background-color: #ebebeb;
}

QStatusBar {
    background-color: #0078d4;
    color: white;
    padding: 6px 12px;
    font-size: 13px;
}

QSplitter::handle {
    background-color: #e0e0e0;
    width: 1px;
}

QLabel#sidebarHeader {
    background-color: #f3f3f3;
    color: #1e1e1e;
    padding: 12px 16px;
    border-bottom: 1px solid #e0e0e0;
    font-size: 16px;
    font-weight: bold;
}

QLabel#sectionTitle {
    font-size: 20px;
    font-weight: bold;
    color: #1e1e1e;
    padding: 10px 0;
}

QLabel#cardTitle {
    font-size: 14px;
    font-weight: bold;
    color: #1e1e1e;
}

QLabel#cardValue {
    font-size: 24px;
    font-weight: bold;
}

QLabel#cardUnit {
    font-size: 14px;
    opacity: 0.7;
    color: #666;
}

QLabel#cardIcon {
    font-size: 20px;
    margin-right: 8px;
}

QGroupBox {
    font-weight: bold;
    border: 1px solid #e0e0e0;
    border-radius: 6px;
    margin-top: 10px;
    padding-top: 20px;
    background-color: #f8f8f8;
}

QGroupBox::title {
    subcontrol-origin: margin;
    left: 10px;
    padding: 0 5px;
    color: #1e1e1e;
}

QScrollArea {
    border: none;
    background-color: transparent;
}

QDoubleSpinBox, QSpinBox {
    padding: 4px;
    border: 1px solid #e0e0e0;
    border-radius: 4px;
    background-color: #f8f8f8;
    color: #1e1e1e;
}

QComboBox {
    padding: 6px 8px;
    border: 1px solid #e0e0e0;
    border-radius: 4px;
    background-color: #f8f8f8;
    color: #1e1e1e;
}

QTabWidget::pane {
    border: 1px solid #e0e0e0;
    background-color: #ffffff;
}

QTabBar::tab {
    background-color: #f3f3f3;
    color: #1e1e1e;
    padding: 8px 16px;
    margin-right: 2px;
}

QTabBar::tab:selected {
    background-color: #0078d4;
    color: white;
}

QProgressBar {
    background-color: #e0e0e0;
    height: 8px;
    border-radius: 4px;
    text-align: center;
}

QProgressBar::chunk {
    background-color: #0078d4;
    border-radius: 4px;
}

QLineEdit {
    padding: 6px 8px;
    border: 1px solid #e0e0e0;
    border-radius: 4px;
    background-color: #f8f8f8;
    color: #1e1e1e;
}

QTextEdit {
    padding: 6px;
    border: 1px solid #e0e0e0;
    border-radius: 4px;
    background-color: #f8f8f8;
    color: #1e1e1e;
}
"""


class ThemeManager:
    def __init__(self) -> None:
        self._current_theme: Theme = "dark"

    def apply_theme(self, widget: object, theme: Theme | None = None) -> None:
        theme = theme or self._current_theme
        stylesheet = DARK_STYLESHEET if theme == "dark" else LIGHT_STYLESHEET
        app = QApplication.instance()
        if isinstance(app, QApplication):
            app.setStyleSheet(stylesheet)
            if theme == "dark":
                self._apply_dark_palette(app)
            else:
                self._apply_light_palette(app)

    def set_theme(self, theme: Theme) -> None:
        self._current_theme = theme

    @property
    def current_theme(self) -> Theme:
        return self._current_theme

    def _apply_dark_palette(self, app: QApplication) -> None:
        palette = QPalette()
        palette.setColor(QPalette.ColorRole.Window, QColor("#1e1e1e"))
        palette.setColor(QPalette.ColorRole.WindowText, QColor("#d4d4d4"))
        palette.setColor(QPalette.ColorRole.Base, QColor("#252526"))
        palette.setColor(QPalette.ColorRole.Text, QColor("#d4d4d4"))
        palette.setColor(QPalette.ColorRole.Button, QColor("#2d2d2d"))
        palette.setColor(QPalette.ColorRole.ButtonText, QColor("#d4d4d4"))
        palette.setColor(QPalette.ColorRole.Highlight, QColor("#094771"))
        palette.setColor(QPalette.ColorRole.HighlightedText, QColor("#ffffff"))
        app.setPalette(palette)

    def _apply_light_palette(self, app: QApplication) -> None:
        palette = QPalette()
        palette.setColor(QPalette.ColorRole.Window, QColor("#ffffff"))
        palette.setColor(QPalette.ColorRole.WindowText, QColor("#1e1e1e"))
        palette.setColor(QPalette.ColorRole.Base, QColor("#f8f8f8"))
        palette.setColor(QPalette.ColorRole.Text, QColor("#1e1e1e"))
        palette.setColor(QPalette.ColorRole.Button, QColor("#f3f3f3"))
        palette.setColor(QPalette.ColorRole.ButtonText, QColor("#1e1e1e"))
        palette.setColor(QPalette.ColorRole.Highlight, QColor("#0078d4"))
        palette.setColor(QPalette.ColorRole.HighlightedText, QColor("#ffffff"))
        app.setPalette(palette)
