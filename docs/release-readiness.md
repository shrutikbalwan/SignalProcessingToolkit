# Release readiness report

This report records the current repository state. It intentionally does not
label the project production-ready until all release checklist gates pass in a
maintainer-controlled CI run.

## Passed locally

- Core test suite: 133 passed, 1 skipped (latest local run).
- New embedded and predictive-maintenance tests pass.
- Ruff formatting/linting and mypy pass for changed modules.
- Wheel/sdist and Twine validation have passed previously.
- Generated embedded C smoke compilation passes when a C compiler is available.
- Version is sourced from `src/signal_processing_toolkit/_version.py`.
- Local release-gate runner passes formatting, linting, typing, tests, docs,
  build, package metadata, and embedded compilation.
- `pip-audit -r requirements.txt`: no known vulnerabilities found.
- `v1.0.0-rc1` tag created and pushed to `origin`.
- RC wheel installed in a clean temporary virtual environment with mandatory
  dependencies; package import and `spt --help` succeeded.
- Hosted CI run `36256373381` passed on Linux, Windows and macOS for Python
  3.12 and 3.13, including wheel smoke testing, documentation, generated
  embedded-example compilation, pip-audit and CodeQL.

## Pending or environment-dependent

- Technical dependency inventory is documented in `docs/licenses.md`; final
  PyQt6/fpdf2 license approval still requires maintainer or legal sign-off.
  The repository contains no third-party models, datasets, screenshots,
  videos, fonts or other bundled assets.
- Screenshots and short videos are not bundled; they remain documentation work.

The automated release gates are green. The project remains a release candidate
until the maintainer records third-party license sign-off; no production-ready
claim is made on the basis of automated checks alone.
