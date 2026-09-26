import json
import shutil
import subprocess

import numpy as np
import pytest

from signal_processing_toolkit.embedded import (
    FixedPointConfig,
    OverflowMode,
    QFormat,
    RoundingMode,
    compare_results,
    export_filter,
    simulate_fir,
    simulate_fixed,
)


def test_q_formats_and_saturation() -> None:
    result = simulate_fixed(np.array([-2.0, -1.0, 0.25, 1.0, 2.0]), FixedPointConfig(QFormat.Q7))
    assert result.integer.tolist() == [-128, -128, 32, 127, 127]
    assert result.clipped == 3


def test_rounding_and_overflow_modes() -> None:
    config = FixedPointConfig(QFormat.Q7, RoundingMode.TRUNCATE, OverflowMode.WRAP)
    result = simulate_fixed(np.array([1.0, -1.0, 0.5]), config)
    assert result.integer[0] == -128
    with pytest.raises(OverflowError):
        simulate_fixed(np.array([2.0]), FixedPointConfig(QFormat.Q7, overflow=OverflowMode.RAISE))


def test_fir_error_and_export_vectors() -> None:
    samples = np.array([0.0, 0.5, -0.25, 0.75])
    coeffs = np.array([0.5, 0.25])
    simulation = simulate_fir(samples, coeffs)
    assert simulation.output.shape == samples.shape
    assert simulation.macs == samples.size * coeffs.size
    artifact = export_filter(coeffs, sample_rate=8000, frame_size=4, vectors=samples)
    payload = json.loads(artifact.test_vectors)
    assert payload["expected"] == pytest.approx(simulation.output.tolist())
    assert "SHA-256" in artifact.header
    assert "SPT_SAMPLE_RATE 8000f" in artifact.header


def test_result_comparison() -> None:
    report = compare_results(np.array([1.0, 2.0]), np.array([1.0, 2.001]), tolerance=0.01)
    assert report.passed
    assert not compare_results(np.array([1.0]), np.array([1.1]), tolerance=0.01).passed


def test_generated_c_compiles_when_compiler_is_available(tmp_path) -> None:
    compiler = shutil.which("gcc") or shutil.which("clang")
    if compiler is None:
        pytest.skip("no C compiler available")
    artifact = export_filter(np.array([0.5, 0.25]), sample_rate=8000, frame_size=8, name="demo")
    (tmp_path / "demo.h").write_text(artifact.header, encoding="utf-8")
    (tmp_path / "demo.c").write_text(artifact.source, encoding="utf-8")
    result = subprocess.run(
        [
            compiler,
            "-std=c99",
            "-Wall",
            "-Werror",
            "-c",
            str(tmp_path / "demo.c"),
            "-o",
            str(tmp_path / "demo.o"),
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr
