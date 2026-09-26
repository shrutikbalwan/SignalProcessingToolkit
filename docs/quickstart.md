# Quick start

```bash
python -m venv .venv
python -m pip install -e .
python -c "from signal_processing_toolkit.models.signal import Signal; print(Signal([1, 2, 3], 1000).duration)"
```

Install optional capabilities only when needed, for example
`pip install -e ".[gui,ai,hardware]"`. Run the deterministic predictive-
maintenance demo with `python -m signal_processing_toolkit.demo.predictive_maintenance`.
