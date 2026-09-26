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
  build, package metadata, and embedded compilation (7/8 executable checks).
- `pip-audit -r requirements.txt`: no known vulnerabilities found.
- `v1.0.0-rc1` tag created and pushed to `origin`.
- RC wheel installed in a clean temporary virtual environment with mandatory
  dependencies; package import and `spt --help` succeeded.

## Pending or environment-dependent

- Cross-platform GitHub Actions run (Windows, Linux, macOS; Python 3.12/3.13).
- Cross-platform coverage evidence from CI (local mandatory-core coverage is 56.97%, above the 50% gate).
- GitHub-hosted CI and CodeQL results could not be queried from this host because
  GitHub CLI is unauthenticated and outbound GitHub access is unavailable.
- pip-audit and CodeQL results for the release commit.
- Complete upstream license and bundled-asset review.
- Clean-system release-candidate installation.
- Screenshots and short videos are not bundled; they remain documentation work.

Until the pending gates are checked, the release status is **release candidate
preparation**, not production-ready.
