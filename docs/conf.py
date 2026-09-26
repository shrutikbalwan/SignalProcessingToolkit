project = "SignalProcessingToolkit"
copyright = "2026, SignalProcessingToolkit contributors"
author = "SignalProcessingToolkit contributors"
extensions = ["myst_parser", "sphinx.ext.autodoc", "sphinx.ext.napoleon"]
templates_path = []
exclude_patterns = ["_build"]
html_theme = "sphinx_rtd_theme"
autodoc_mock_imports = ["PyQt6", "pyqtgraph", "sounddevice", "soundfile", "cv2", "onnx", "onnxruntime", "serial"]
