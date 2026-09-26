from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import numpy as np
import pytest

from signal_processing_toolkit.ai.evaluation import (
    classification_report,
    false_positive_indices,
    precision_recall_curve,
    roc_curve,
    threshold_analysis,
)
from signal_processing_toolkit.ai.model import (
    EdgeModel,
    ModelMetadata,
    ModelValidationError,
    TensorSpec,
    compare_models,
    select_execution_providers,
)
from signal_processing_toolkit.ai.preprocessing import PreprocessingPipeline
from signal_processing_toolkit.ai.streaming import (
    DetectionSettings,
    EventDetector,
    InferencePoint,
    SlidingWindowInference,
)
from signal_processing_toolkit.streaming.model import ChannelMetadata, StreamChunk


class DeterministicSession:
    inputs = (TensorSpec("samples", (None, 4, 1), "float32"),)
    outputs = (TensorSpec("probabilities", (None, 2), "float32"),)
    providers = ("CPUExecutionProvider",)

    def run(self, output_names, inputs):
        assert output_names == ["probabilities"]
        average = np.mean(inputs["samples"], axis=(1, 2))
        anomaly = np.clip((average + 1.0) / 2.0, 0.0, 1.0)
        return [np.column_stack((1.0 - anomaly, anomaly)).astype(np.float32)]


class DeterministicBackend:
    def __init__(self, available=("CUDAExecutionProvider", "CPUExecutionProvider")) -> None:
        self.available = available
        self.selected = None

    def available_providers(self):
        return self.available

    def create_session(self, path, providers):
        self.selected = tuple(providers)
        return DeterministicSession()


def metadata() -> ModelMetadata:
    return ModelMetadata(
        labels=("normal", "anomaly"),
        preprocessing=PreprocessingPipeline(sampling_rate=4, window_samples=4),
        input_name="samples",
        output_name="probabilities",
    )


def model(tmp_path: Path) -> EdgeModel:
    path = tmp_path / "deterministic.onnx"
    path.write_bytes(b"deterministic-test-model")
    return EdgeModel(path, metadata(), DeterministicSession(), "abc123")


def chunk(samples, sequence, timestamp) -> StreamChunk:
    return StreamChunk(
        np.asarray(samples, dtype=np.float32),
        sampling_rate=4,
        channels=(ChannelMetadata("vibration", "g"),),
        sequence=sequence,
        device_timestamp=timestamp,
        host_timestamp=timestamp + 100,
    )


def test_time_and_spectrogram_preprocessing_round_trip() -> None:
    source = np.arange(8, dtype=float).reshape(8, 1)
    fitted = PreprocessingPipeline.fit(
        source,
        mode="time",
        sampling_rate=8,
        window_samples=8,
        remove_dc=True,
    )
    restored = PreprocessingPipeline.from_dict(fitted.to_dict())
    assert np.allclose(restored.transform(source), fitted.transform(source))
    assert np.allclose(np.mean(restored.transform(source), axis=0), 0.0)
    batch_fitted = PreprocessingPipeline.fit(
        np.stack((source, source + 10)),
        mode="time",
        sampling_rate=8,
        window_samples=8,
    )
    normalized_batch = batch_fitted.transform_batch(np.stack((source, source + 10)))
    assert np.mean(normalized_batch) == pytest.approx(0.0, abs=1e-7)

    spectrogram = PreprocessingPipeline(
        mode="spectrogram",
        sampling_rate=8,
        window_samples=8,
        stft_length=4,
        stft_overlap=2,
        fft_length=4,
        spectrum="magnitude",
    ).transform(source)
    assert spectrogram.shape == (3, 3, 1)
    assert spectrogram.dtype == np.float32


def test_model_load_validates_metadata_and_provider_fallback(tmp_path: Path) -> None:
    path = tmp_path / "tiny.onnx"
    path.write_bytes(b"tiny deterministic fixture")
    backend = DeterministicBackend()
    with pytest.raises(ModelValidationError, match="metadata"):
        EdgeModel.load(path, backend=backend)

    path.with_suffix(".metadata.json").write_text(json.dumps(metadata().to_dict()))
    loaded = EdgeModel.load(path, providers=["MissingProvider"], backend=backend)
    assert backend.selected == ("CPUExecutionProvider",)
    assert loaded.predict(np.zeros((2, 4, 1))).probabilities.shape == (2, 2)
    assert len(loaded.checksum_sha256) == 64


def test_invalid_model_shapes_are_rejected(tmp_path: Path) -> None:
    class BadSession(DeterministicSession):
        inputs = (TensorSpec("samples", (None, 4), "float32"),)

    with pytest.raises(ModelValidationError, match="batched time or spectrogram"):
        EdgeModel(tmp_path / "bad.onnx", metadata(), BadSession(), "bad")


def test_provider_selection_order_and_fallback() -> None:
    providers = select_execution_providers(
        ["CUDAExecutionProvider", "CPUExecutionProvider"], ["CUDAExecutionProvider"]
    )
    assert providers == ("CUDAExecutionProvider", "CPUExecutionProvider")
    assert select_execution_providers(["CustomProvider"], ["missing"]) == ("CustomProvider",)
    with pytest.raises(RuntimeError):
        select_execution_providers([])


def test_batch_and_fragmented_streaming_inference_match(tmp_path: Path) -> None:
    edge_model = model(tmp_path)
    values = np.array([-1, -1, -1, -1, 1, 1, 1, 1], dtype=np.float32)[:, None]
    batch = edge_model.predict(values.reshape(2, 4, 1)).probabilities
    streaming = SlidingWindowInference(edge_model, window_samples=4, hop_samples=4)
    points = []
    points.extend(streaming.process(chunk(values[:3], 0, 10.0)))
    points.extend(streaming.process(chunk(values[3:6], 1, 10.75)))
    points.extend(streaming.process(chunk(values[6:], 2, 11.5)))
    assert np.allclose(np.asarray([point.probabilities for point in points]), batch)
    assert [point.device_timestamp for point in points] == [10.0, 11.0]


def test_float_and_quantized_comparison_reports_accuracy_and_size(tmp_path: Path) -> None:
    first = model(tmp_path)
    second_path = tmp_path / "quantized.ort"
    second_path.write_bytes(b"smaller")
    second = EdgeModel(second_path, metadata(), DeterministicSession(), "def456")
    comparison = compare_models(first, second, np.zeros((2, 4, 1)))
    assert comparison.label_agreement == 1.0
    assert comparison.maximum_absolute_probability_error == 0.0
    assert comparison.quantized_size_bytes < comparison.float_size_bytes


def point(probability: float, timestamp: float) -> InferencePoint:
    probabilities = (1 - probability, probability)
    index = int(probability >= 0.5)
    labels = ("normal", "anomaly")
    return InferencePoint(
        sequence=int(timestamp * 10),
        device_timestamp=timestamp,
        host_timestamp=timestamp,
        labels=labels,
        probabilities=probabilities,
        confidence=probabilities[index],
        predicted_label=labels[index],
        latency_seconds=0.001,
    )


def test_threshold_smoothing_cooldown_and_context_save(tmp_path: Path) -> None:
    detector = EventDetector(
        ("normal", "anomaly"),
        DetectionSettings(
            threshold=0.7,
            smoothing_window=2,
            cooldown_seconds=2,
            enabled_labels=("anomaly",),
        ),
    )
    assert detector.update(point(0.6, 0.0)) is None
    first = detector.update(point(0.9, 1.0))
    assert first is not None and first.label == "anomaly"
    assert detector.update(point(0.9, 2.0)) is None
    second = detector.update(point(0.9, 3.0))
    assert second is not None
    contextual = second.with_context(
        np.arange(10),
        sampling_rate=10,
        channels=(ChannelMetadata("x", "g"),),
        trigger_sample=5,
        before_samples=2,
        after_samples=3,
    )
    json_path, sample_path = contextual.save(tmp_path)
    assert json.loads(json_path.read_text())["label"] == "anomaly"
    assert np.load(sample_path)["samples"].tolist() == [3, 4, 5, 6, 7, 8]


def test_classification_curves_thresholds_and_false_positive_inspection() -> None:
    truth = np.array([0, 0, 1, 1])
    scores = np.array([0.1, 0.8, 0.7, 0.9])
    predicted = (scores >= 0.5).astype(int)
    report = classification_report(truth, predicted, 2)
    assert report.confusion_matrix.tolist() == [[1, 1], [0, 2]]
    assert report.precision[1] == pytest.approx(2 / 3)
    assert roc_curve(truth, scores).x.shape == (6,)
    assert precision_recall_curve(truth, scores).x.shape == (6,)
    analysis = threshold_analysis(truth, scores, np.array([0.5, 0.85]))
    assert analysis[0].false_positives == 1
    assert false_positive_indices(truth, scores, 0.5).tolist() == [1]


def test_dsp_core_import_does_not_import_onnx_runtime() -> None:
    command = [
        sys.executable,
        "-c",
        "import sys; sys.path.insert(0, 'src'); import signal_processing_toolkit.dsp; "
        "assert 'onnxruntime' not in sys.modules; assert 'onnx' not in sys.modules",
    ]
    subprocess.run(command, check=True)  # noqa: S603 - fixed interpreter and source text


def test_generated_deterministic_onnx_model_executes(tmp_path: Path) -> None:
    pytest.importorskip("onnx")
    pytest.importorskip("onnxruntime")
    subprocess.run(  # noqa: S603 - fixed interpreter and repository script
        [
            sys.executable,
            "examples/edge_ai_motor_anomaly/build_demo.py",
            "--output",
            str(tmp_path),
        ],
        check=True,
    )
    loaded = EdgeModel.load(tmp_path / "motor_anomaly.onnx")
    result = loaded.predict(np.zeros((2, 256, 1), dtype=np.float32))
    assert result.probabilities.shape == (2, 2)
    assert np.allclose(np.sum(result.probabilities, axis=1), 1.0)
