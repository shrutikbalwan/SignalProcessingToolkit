from __future__ import annotations

import csv
from pathlib import Path

import numpy as np

from src.models.signal import Signal, SignalMetadata


class FileSignalRepository:
    def save(self, signal: Signal, path: Path) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        np.savez(
            path,
            time_data=signal.time_data,
            sampling_rate=signal.sampling_rate,
            frequency=signal.frequency,
            amplitude=signal.amplitude,
            phase=signal.phase,
            metadata_name=signal.metadata.name,
            metadata_id=signal.metadata.id,
        )

    def load(self, path: Path) -> Signal:
        if not path.exists():
            raise FileNotFoundError(f"Signal file not found: {path}")
        data = np.load(path)
        return Signal(
            time_data=data["time_data"],
            sampling_rate=float(data["sampling_rate"]),
            frequency=float(data.get("frequency", 0)),
            amplitude=float(data.get("amplitude", 1)),
            phase=float(data.get("phase", 0)),
            metadata=SignalMetadata(
                name=str(data.get("metadata_name", "Loaded Signal")),
                id=str(data.get("metadata_id", "")),
            ),
        )

    def export_csv(self, signal: Signal, path: Path) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(["time", "amplitude"])
            for t, y in zip(signal.time_vector, signal.time_data, strict=False):
                writer.writerow([f"{t:.6f}", f"{y:.6f}"])

    def export_wav(self, signal: Signal, path: Path) -> None:
        from scipy.io.wavfile import write as wav_write

        path.parent.mkdir(parents=True, exist_ok=True)
        normalized = np.int16(signal.time_data / np.max(np.abs(signal.time_data)) * 32767)
        wav_write(str(path), int(signal.sampling_rate), normalized)

    def export_txt(self, signal: Signal, path: Path) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        np.savetxt(
            path,
            np.column_stack([signal.time_vector, signal.time_data]),
            header="time amplitude",
            fmt="%.6f",
        )
