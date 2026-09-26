"""Run release checks available on the current host.

This complements, rather than replaces, the cross-platform GitHub workflow.
Checks that require hosted services are reported as pending.
"""

from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def run(label: str, command: list[str]) -> bool:
    print(f"[RUN] {label}: {' '.join(command)}")
    result = subprocess.run(command, cwd=ROOT, check=False)
    print(f"[{'PASS' if result.returncode == 0 else 'FAIL'}] {label}")
    return result.returncode == 0


def main() -> int:
    python = sys.executable
    checks = [
        ("format", [python, "-m", "ruff", "format", "--check", "src", "tests", "tools"]),
        ("lint", [python, "-m", "ruff", "check", "src", "tests", "tools"]),
        ("types", [python, "-m", "mypy", "src"]),
        ("tests", [python, "-m", "pytest", "-q"]),
        ("docs", [python, "-m", "sphinx", "-W", "-b", "html", "docs", "docs/_build/html"]),
        ("build", [python, "-m", "build"]),
        (
            "package metadata",
            [python, "-m", "twine", "check", *(str(path) for path in (ROOT / "dist").glob("*"))],
        ),
        ("embedded C", [python, "tools/compile_embedded_example.py"]),
    ]
    passed = sum(run(label, command) for label, command in checks)
    audit = shutil.which("pip-audit")
    if audit:
        passed += int(run("dependency audit", [audit, "-r", "requirements.txt"]))
    else:
        print("[PENDING] dependency audit: install pip-audit or use CI")
    print(f"\n{passed}/{len(checks) + int(bool(audit))} executable checks passed")
    print("[PENDING] GitHub-hosted OS matrix, CodeQL, legal review, and release tagging")
    return 0 if passed == len(checks) + int(bool(audit)) else 1


if __name__ == "__main__":
    raise SystemExit(main())
