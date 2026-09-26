from __future__ import annotations

import os
from pathlib import Path

import numpy as np
import pytest
from scipy import signal as sp_signal

from signal_processing_toolkit.models.signal import Signal

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")


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
def sine_signal() -> Signal:
    sampling_rate = 2048.0
    time = np.arange(2048) / sampling_rate
    return Signal(1.5 * np.sin(2 * np.pi * 128 * time), sampling_rate)


@pytest.fixture
def multitone_signal() -> Signal:
    sampling_rate = 4096.0
    time = np.arange(4096) / sampling_rate
    data = np.sin(2 * np.pi * 64 * time) + 0.1 * np.sin(2 * np.pi * 192 * time)
    return Signal(data, sampling_rate)


@pytest.fixture
def impulse_signal() -> Signal:
    data = np.zeros(256)
    data[0] = 1.0
    return Signal(data, 1024.0)


@pytest.fixture
def chirp_signal() -> Signal:
    sampling_rate = 2048.0
    time = np.arange(2048) / sampling_rate
    return Signal(sp_signal.chirp(time, 20, time[-1], 700), sampling_rate)


@pytest.fixture
def noise_signal() -> Signal:
    return Signal(np.random.default_rng(20260926).normal(size=4096), 4096.0)


@pytest.fixture
def temp_dir(tmp_path: Path) -> Path:
    return tmp_path
