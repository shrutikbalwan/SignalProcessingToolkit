from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

import signal_processing_toolkit
from signal_processing_toolkit.main import main


def test_public_package_identity() -> None:
    assert signal_processing_toolkit.__name__ == "signal_processing_toolkit"
    assert signal_processing_toolkit.__version__ == "1.0.0"


def test_cli_version(capsys) -> None:
    try:
        main(["--version"])
    except SystemExit as exc:
        assert exc.code == 0
    assert capsys.readouterr().out.strip() == "spt 1.0.0"


def test_module_entry_point() -> None:
    project_root = Path(__file__).parents[1]
    env = os.environ.copy()
    env["PYTHONPATH"] = str(project_root / "src")
    result = subprocess.run(  # noqa: S603 - executable is the running Python interpreter
        [sys.executable, "-m", "signal_processing_toolkit", "--version"],
        cwd=project_root,
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr
    assert result.stdout.strip() == "spt 1.0.0"


def test_core_imports_do_not_load_optional_dependencies() -> None:
    project_root = Path(__file__).parents[1]
    code = """
import sys
import signal_processing_toolkit
from signal_processing_toolkit.models.signal import Signal
from signal_processing_toolkit.dsp.fft import compute_fft
from signal_processing_toolkit.streaming import StreamPipeline, SyntheticSource
from signal_processing_toolkit.audio import SoundDeviceAudioSource
from signal_processing_toolkit.hardware import SerialSensorSource
blocked = {'cv2', 'sounddevice', 'onnxruntime', 'PyQt6', 'serial'}
loaded = blocked.intersection(sys.modules)
if loaded:
    raise SystemExit(f'optional modules loaded: {sorted(loaded)}')
"""
    env = os.environ.copy()
    env["PYTHONPATH"] = str(project_root / "src")
    result = subprocess.run(  # noqa: S603 - executable is the running Python interpreter
        [sys.executable, "-c", code],
        cwd=project_root,
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr
