# Reproducible motor-vibration anomaly example

This example creates a tiny deterministic time-domain ONNX classifier for synthetic motor
vibration. Normal examples contain shaft rotation plus low noise; anomalous examples add a bearing
fault harmonic and periodic impacts. It commits neither a dataset nor a binary model.

```bash
python -m pip install -e ".[ai]"
python examples/edge_ai_motor_anomaly/build_demo.py --output .tmp/motor-demo
spt
```

Load `.tmp/motor-demo/motor_anomaly.onnx` from the **Edge AI** page. Its required metadata sidecar
is generated beside it. The model and dataset are generated locally and deterministically; the
script and generated synthetic samples are available under the repository MIT license. No external
data or third-party model is downloaded. This toy is for demonstrating integration and evaluation,
not for machine-safety decisions.
