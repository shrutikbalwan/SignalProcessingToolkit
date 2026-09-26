from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

import numpy as np

from signal_processing_toolkit.ai.model import InferenceBatch, ModelMetadata
from signal_processing_toolkit.ai.preprocessing import PreprocessingPipeline
from signal_processing_toolkit.ai.streaming import InferencePoint
from signal_processing_toolkit.models.signal import Signal
from signal_processing_toolkit.ui.views.edge_ai_view import EdgeAIView


def test_edge_ai_page_displays_probabilities_and_emits_detection(qtbot) -> None:
    page = EdgeAIView()
    qtbot.addWidget(page)
    metadata = ModelMetadata(
        labels=("normal", "fault"),
        preprocessing=PreprocessingPipeline(sampling_rate=100, window_samples=16),
        input_name="samples",
        output_name="probabilities",
    )
    model = SimpleNamespace(
        path=Path("motor.onnx"),
        metadata=metadata,
        session=SimpleNamespace(providers=("CPUExecutionProvider",)),
        checksum_sha256="a" * 64,
    )
    page.set_model(model)
    inference = InferencePoint(
        sequence=1,
        device_timestamp=2.0,
        host_timestamp=3.0,
        labels=("normal", "fault"),
        probabilities=(0.1, 0.9),
        confidence=0.9,
        predicted_label="fault",
        latency_seconds=0.002,
    )
    with qtbot.waitSignal(page.event_detected):
        page.append_inference(inference)
    assert page.table.item(1, 1).text() == "0.9000"
    assert "Detected fault" in page.status_label.text()
    assert len(page.plot.plot_widget.listDataItems()) == 3


def test_edge_ai_detection_controls_reconfigure_detector(qtbot) -> None:
    page = EdgeAIView()
    qtbot.addWidget(page)
    metadata = ModelMetadata(
        labels=("normal", "fault"),
        preprocessing=PreprocessingPipeline(sampling_rate=100, window_samples=16),
        input_name="samples",
        output_name="probabilities",
    )
    page.set_model(
        SimpleNamespace(
            path=Path("motor.ort"),
            metadata=metadata,
            session=SimpleNamespace(providers=("CPUExecutionProvider",)),
            checksum_sha256="b" * 64,
        )
    )
    page.threshold.setValue(0.95)
    page.append_inference(
        InferencePoint(1, 0.0, 0.0, metadata.labels, (0.1, 0.9), 0.9, "fault", 0.001)
    )
    assert "Detected" not in page.status_label.text()


def test_selected_signal_runs_windowed_inference_off_the_ui_thread(qtbot) -> None:
    page = EdgeAIView()
    qtbot.addWidget(page)
    metadata = ModelMetadata(
        labels=("normal", "fault"),
        preprocessing=PreprocessingPipeline(sampling_rate=100, window_samples=16),
        input_name="samples",
        output_name="probabilities",
    )

    def predict(windows: np.ndarray) -> InferenceBatch:
        probabilities = np.tile(np.array([[0.25, 0.75]]), (windows.shape[0], 1))
        return InferenceBatch(probabilities, metadata.labels, 0.003, 1000.0, 128)

    page.set_input_signal(Signal(np.ones(32), sampling_rate=100))
    page.set_model(
        SimpleNamespace(
            path=Path("motor.onnx"),
            metadata=metadata,
            session=SimpleNamespace(providers=("CPUExecutionProvider",)),
            checksum_sha256="c" * 64,
            predict=predict,
        )
    )
    qtbot.waitUntil(lambda: not page._tasks.is_busy and page.table.item(1, 1).text() == "0.7500")
    assert len(page._times) == 3
