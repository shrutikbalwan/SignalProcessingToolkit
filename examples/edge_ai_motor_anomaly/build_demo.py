"""Generate a deterministic toy vibration model; no external data is downloaded."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    try:
        import onnx
        from onnx import TensorProto, helper, numpy_helper
    except ImportError as exc:
        raise SystemExit("Install the ai extra to generate the example") from exc

    args.output.mkdir(parents=True, exist_ok=True)
    sample_count = 256
    # A deterministic linear demonstration model. The anomaly logit responds to
    # alternating samples, which represent higher vibration-frequency energy.
    weights = np.empty((sample_count, 2), dtype=np.float32)
    weights[:, 0] = 0.0
    weights[:, 1] = np.where(np.arange(sample_count) % 2, -0.04, 0.04)
    bias = np.array([0.5, -0.5], dtype=np.float32)
    graph = helper.make_graph(
        [
            helper.make_node("Flatten", ["samples"], ["flat"], axis=1),
            helper.make_node("Gemm", ["flat", "weights", "bias"], ["logits"]),
        ],
        "motor-anomaly-demo",
        [helper.make_tensor_value_info("samples", TensorProto.FLOAT, [None, sample_count, 1])],
        [helper.make_tensor_value_info("logits", TensorProto.FLOAT, [None, 2])],
        [numpy_helper.from_array(weights, "weights"), numpy_helper.from_array(bias, "bias")],
    )
    model = helper.make_model(
        graph,
        producer_name="signal-processing-toolkit",
        opset_imports=[helper.make_operatorsetid("", 18)],
    )
    model.ir_version = min(model.ir_version, 10)
    model_path = args.output / "motor_anomaly.onnx"
    onnx.save(model, model_path)
    metadata = {
        "labels": ["normal", "bearing_fault"],
        "input_name": "samples",
        "output_name": "logits",
        "output_kind": "logits",
        "description": "Deterministic synthetic motor-vibration integration demo",
        "license": "MIT",
        "preprocessing": {
            "mode": "time",
            "sampling_rate": 2048.0,
            "window_samples": sample_count,
            "channel_indices": None,
            "remove_dc": True,
            "mean": None,
            "scale": None,
            "stft_window": "hann",
            "stft_length": 256,
            "stft_overlap": 128,
            "fft_length": None,
            "spectrum": "log_power",
            "log_floor": 1e-12,
        },
    }
    model_path.with_suffix(".metadata.json").write_text(json.dumps(metadata, indent=2))
    print(model_path)


if __name__ == "__main__":
    main()
