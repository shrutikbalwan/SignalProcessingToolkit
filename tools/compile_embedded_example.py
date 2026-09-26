"""Compile a generated embedded export with the host C compiler."""

from __future__ import annotations

import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main() -> int:
    import numpy as np

    sys.path.insert(0, str(ROOT / "src"))
    from signal_processing_toolkit.embedded import export_filter

    compiler = shutil.which("gcc") or shutil.which("clang")
    if compiler is None:
        raise SystemExit("No C compiler found")
    artifact = export_filter(
        np.array([0.5, 0.25]), sample_rate=8_000, frame_size=32, name="example"
    )
    with tempfile.TemporaryDirectory() as directory:
        root = Path(directory)
        (root / "example.h").write_text(artifact.header, encoding="utf-8")
        (root / "example.c").write_text(artifact.source, encoding="utf-8")
        subprocess.run(
            [
                compiler,
                "-std=c99",
                "-Wall",
                "-Werror",
                "-c",
                str(root / "example.c"),
                "-o",
                str(root / "example.o"),
            ],
            check=True,
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
