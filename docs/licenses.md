# Dependency and asset licensing

The project itself is MIT licensed. The mandatory runtime dependencies are
distributed under permissive licenses: NumPy (BSD-3-Clause) and SciPy
(BSD-3-Clause). Optional dependencies must be reviewed before redistribution:

| Extra | Dependencies | Release note |
|---|---|---|
| gui | PyQt6, pyqtgraph, Matplotlib, pydantic-settings | PyQt6 is GPLv3/commercial; users must choose a compatible license. |
| audio | sounddevice, soundfile | BSD/MIT-style licenses; platform audio backends remain separate. |
| image | OpenCV Python | Apache-2.0; inspect bundled codec/build licenses for redistribution. |
| ai | ONNX, ONNX Runtime | Apache-2.0; model licenses are separate and must be recorded. |
| hardware | pyserial | BSD-3-Clause. |
| export | fpdf2, openpyxl | fpdf2 is LGPL-3.0-only and openpyxl is MIT; review dynamic-linking and redistribution obligations before shipping the export extra. |

## Inventory performed

On 2026-09-26, `pip-licenses --from=mixed --with-urls` was run against the
release environment. The inventory confirmed the principal runtime and extra
licenses above. The complete transitive inventory is environment-specific and
is intentionally not committed because it changes with dependency resolution;
release builds should archive the command output alongside their artifacts.

Compatibility findings requiring an explicit maintainer decision:

1. The core package is MIT and depends only on NumPy and SciPy (BSD-3-Clause).
2. PyQt6 is GPL-3.0-only or commercial; distributing the GUI application
   requires a compatible licensing choice.
3. fpdf2 is LGPL-3.0-only; distributing binaries using the export extra needs
   an LGPL compliance review.
4. ONNX/ONNX Runtime are Apache-2.0, pyserial is BSD-3-Clause, audio extras
   are MIT/BSD, and OpenCV Python is Apache-2.0. Model, firmware, codec and
   platform-backend licenses remain separate obligations.
5. No third-party model, dataset, screenshot, video, font, or other bundled
   asset is currently included. Synthetic examples are generated under MIT.

This is a technical inventory, not legal advice. A maintainer or counsel must
record final approval for PyQt6 and fpdf2 before calling the project
production-ready.
