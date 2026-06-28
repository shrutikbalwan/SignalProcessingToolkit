from __future__ import annotations

from pathlib import Path

import numpy as np
import pytest

from src.models.signal import Signal


@pytest.fixture
def sample_sine() -> Signal:
    sr = 1000
    t = np.linspace(0, 1, sr, endpoint=False)
    data = np.sin(2 * np.pi * 10 * t)
    return Signal(time_data=data, sampling_rate=float(sr))


@pytest.fixture
def sample_noise() -> Signal:
    sr = 1000
    rng = np.random.default_rng(42)
    data = rng.normal(0, 0.5, sr)
    return Signal(time_data=data, sampling_rate=float(sr))


@pytest.fixture
def temp_dir(tmp_path: Path) -> Path:
    return tmp_path
