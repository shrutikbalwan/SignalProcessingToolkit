# Release checklist

A release is not production-ready until every required gate below is checked
by a maintainer and recorded in the release issue.

- [ ] Version updated only in `src/signal_processing_toolkit/_version.py`.
- [ ] Changelog, migration notes, and supported Python versions reviewed.
- [ ] Windows, Linux, and macOS CI green for every supported Python version.
- [ ] Formatting, linting, typing, tests, and the 50% mandatory-core coverage threshold are green.
- [ ] Wheel and sdist build; wheel installs in a clean environment and imports.
- [ ] Generated embedded examples compile and test vectors reproduce outputs.
- [ ] Dependency/license and vulnerability scans reviewed.
- [ ] Security, governance, and release documentation reviewed.
- [ ] Release candidate installed from a clean system and smoke-tested.
- [ ] Tagged release workflow is inspected; publishing remains a manual action.
