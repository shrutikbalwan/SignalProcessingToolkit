from __future__ import annotations

import os
import sys
from pathlib import Path


def _is_pytest_process() -> bool:
    executable = Path(sys.argv[0]).name.lower() if sys.argv else ""
    return "pytest" in executable


if _is_pytest_process():
    addopts = os.environ.get("PYTEST_ADDOPTS", "")
    disable_pytestqt = "-p no:pytestqt"
    if disable_pytestqt not in addopts:
        os.environ["PYTEST_ADDOPTS"] = f"{addopts} {disable_pytestqt}".strip()
