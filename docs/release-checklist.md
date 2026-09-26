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

## License sign-off record

This section must be completed by an authorized maintainer or legal reviewer;
automated inventory is not legal approval.

- [ ] PyQt6 distribution model selected: GPL-3.0-compatible distribution or
      commercial PyQt6 license.
- [ ] PyQt6 notices and obligations reviewed for the intended distribution.
- [ ] fpdf2 LGPL-3.0-only obligations reviewed for the export extra.
- [ ] Optional dependency licenses and platform/backend licenses reviewed.
- [ ] Bundled models, datasets, fonts, screenshots, videos and firmware assets
      reviewed (or confirmed absent).
- [ ] Approval recorded in the release issue or repository governance record.

Reviewer: ____________________  Date: ____________________

Decision: _____________________  Release/version: __________
- [ ] Release candidate installed from a clean system and smoke-tested.
- [ ] Tagged release workflow is inspected; publishing remains a manual action.
