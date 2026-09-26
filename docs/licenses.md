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
| export | fpdf2, openpyxl | Permissive licenses; verify fonts and generated assets separately. |

This is a release review starting point, not legal advice. CI scans dependency
versions for known vulnerabilities; maintainers must review complete upstream
license notices before publishing a binary distribution. No third-party model,
dataset, screenshot, video, font, or other bundled asset is currently included.
Synthetic examples are generated under the repository MIT license.
