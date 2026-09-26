# Contributing to SignalProcessingToolkit

Thank you for improving the toolkit. Please open an issue before large
architectural changes and describe the user-visible behavior, scientific
assumptions, and optional dependencies involved.

## Development setup

```bash
python -m venv .venv
python -m pip install -U pip
python -m pip install -e ".[dev,docs,gui,audio,image,ai,hardware,export]"
```

Run the same checks used by CI:

```bash
ruff format --check src tests
ruff check src tests
mypy src
pytest -q
python -m build
```

DSP changes must include deterministic numerical tests and document units,
sample/channel axes, boundary behavior, and assumptions. Keep hardware, GUI,
audio, image, and AI imports optional. Do not commit datasets, credentials,
generated build directories, or model binaries.

Pull requests should be focused, explain compatibility impact, and include
documentation updates. A maintainer will review scientific correctness,
backward compatibility, security, and test coverage before merging.
