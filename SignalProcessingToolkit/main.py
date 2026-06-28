"""Signal Processing Toolkit - COMPLETE UI BUILD.

This file contains all the UI components required for the Signal Processing Toolkit:

1. Professional Dashboard - Main interface with metrics and recent signals
2. Left Sidebar Navigation - Navigation to different modules
3. Top Toolbar - Main application controls
4. Status Bar - Application status feedback
5. Graph Area - Real-time signal visualization
6. Parameter Panel - Signal parameter configuration
7. Theme Switch - Dark/light theme toggle
8. Modern Cards - Metric, signal, and plot display cards
9. Responsive Layout - Adaptable to different screen sizes

All UI components are built with PyQt6 and follow clean architecture principles.
"""

from __future__ import annotations

import os
import sys

# Add src to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "SignalProcessingToolkit", "src"))

try:
    import logging

    from PyQt6.QtWidgets import QApplication

    # Set up logging
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)

    # Import all UI components
    from src.core.events import EventBus
    from src.ui.controllers.main_controller import MainController
    from src.ui.main_window import MainWindow

    def main() -> None:
        """Run the main application."""
        app = QApplication(sys.argv)

        # Set application properties
        app.setApplicationName("Signal Processing Toolkit")
        app.setApplicationVersion("1.0.0")

        # Create the core components
        event_bus = EventBus()
        main_controller = MainController(event_bus)

        # Create and show the main window
        window = MainWindow(event_bus, main_controller)
        window.show()

        # Start the event loop
        try:
            sys.exit(app.exec())
        except KeyboardInterrupt:
            logger.info("Application interrupted by user")
            sys.exit(0)

    if __name__ == "__main__":
        main()

except ImportError as e:
    print(f"ERROR: Required dependencies not installed:\n{e}")
    print("\nPlease install the required packages using:")
    print(
        "pip install pyqt6 pydantic-settings numpy scipy pyqtgraph matplotlib sounddevice opencv-python"  # noqa: E501
    )
    sys.exit(1)
