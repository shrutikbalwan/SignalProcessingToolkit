from __future__ import annotations

import json

import pytest

from signal_processing_toolkit.models.project import Project
from signal_processing_toolkit.repositories.implementations.file_project_repository import (
    FileProjectRepository,
)


def test_project_round_trips_edge_model_identity(tmp_path) -> None:
    path = tmp_path / "analysis.spt"
    project = Project("analysis", path=str(path))
    reference = {
        "path": "models/anomaly.onnx",
        "checksum_sha256": "a" * 64,
        "labels": ["normal", "anomaly"],
        "preprocessing": {"mode": "time", "window_samples": 256},
    }
    project.add_ai_model_reference(reference)
    FileProjectRepository().save(project)
    restored = FileProjectRepository().load(path)
    assert restored.ai_models == [reference]
    assert json.loads(path.read_text())["ai_models"] == [reference]


def test_project_rejects_incomplete_ai_model_reference() -> None:
    with pytest.raises(ValueError, match="checksum_sha256"):
        Project("analysis").add_ai_model_reference({"path": "model.onnx"})
