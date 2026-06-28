from __future__ import annotations

from pathlib import Path

import numpy as np
import pytest

from src.models.signal import Signal

pytest.importorskip("PyQt6")

from src.services.export_service import ExportService  # noqa: E402


@pytest.fixture
def service() -> ExportService:
    return ExportService()


@pytest.fixture
def sine() -> Signal:
    sr = 1000
    t = np.linspace(0, 1, sr, endpoint=False)
    return Signal(time_data=np.sin(2 * np.pi * 10 * t), sampling_rate=float(sr))


class TestExportService:
    def test_export_signal_csv(self, service: ExportService, sine: Signal, tmp_path: Path) -> None:
        path = tmp_path / "test.csv"
        service.export_signal(sine, path, {"format": "csv"})
        assert path.exists()
        content = path.read_text()
        assert "amplitude" in content

    def test_export_signal_txt(self, service: ExportService, sine: Signal, tmp_path: Path) -> None:
        path = tmp_path / "test.txt"
        service.export_signal(sine, path, {"format": "txt"})
        assert path.exists()

    def test_export_signal_npz(self, service: ExportService, sine: Signal, tmp_path: Path) -> None:
        path = tmp_path / "test.npz"
        service.export_signal(sine, path, {"format": "npz"})
        assert path.exists()
        loaded = np.load(path)
        assert "time_data" in loaded
        assert "sampling_rate" in loaded
