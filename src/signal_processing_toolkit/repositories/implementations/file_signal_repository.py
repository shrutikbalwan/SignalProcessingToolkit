from __future__ import annotations

import csv
import json
from datetime import datetime
from pathlib import Path

import numpy as np

from signal_processing_toolkit.models.signal import ProcessingStep, Signal, SignalMetadata


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
            channel_names=np.asarray(signal.channel_names),
            units=np.asarray(signal.units),
            start_time=signal.start_time,
            metadata_description=signal.metadata.description,
            metadata_tags=np.asarray(signal.metadata.tags),
            metadata_source=signal.metadata.source,
            metadata_attributes=json.dumps(signal.metadata.attributes, default=str),
            metadata_provenance=json.dumps(
                [
                    {
                        "operation": step.operation,
                        "parameters": step.parameters,
                        "timestamp": step.timestamp.isoformat(),
                    }
                    for step in signal.metadata.provenance
                ],
                default=str,
            ),
        )

    def load(self, path: Path) -> Signal:
        if not path.exists():
            raise FileNotFoundError(f"Signal file not found: {path}")
        data = np.load(path, allow_pickle=False)
        metadata_id = str(data.get("metadata_id", ""))
        provenance_data = json.loads(str(data.get("metadata_provenance", "[]")))
        metadata = SignalMetadata(
            name=str(data.get("metadata_name", "Loaded Signal")),
            description=str(data.get("metadata_description", "")),
            tags=[str(value) for value in data.get("metadata_tags", [])],
            source=str(data.get("metadata_source", "")),
            attributes=json.loads(str(data.get("metadata_attributes", "{}"))),
            provenance=tuple(
                ProcessingStep(
                    operation=item["operation"],
                    parameters=item.get("parameters", {}),
                    timestamp=datetime.fromisoformat(item["timestamp"]),
                )
                for item in provenance_data
            ),
        )
        if metadata_id:
            metadata.id = metadata_id
        return Signal(
            time_data=data["time_data"],
            sampling_rate=float(data["sampling_rate"]),
            frequency=float(data.get("frequency", 0)),
            amplitude=float(data.get("amplitude", 1)),
            phase=float(data.get("phase", 0)),
            metadata=metadata,
            channel_names=tuple(str(value) for value in data.get("channel_names", [])) or None,
            units=tuple(str(value) for value in data.get("units", [""])),
            start_time=float(data.get("start_time", 0.0)),
        )

    def export_csv(self, signal: Signal, path: Path) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("w", newline="") as f:
            writer = csv.writer(f)
            value_headers = ("amplitude",) if signal.is_mono else (signal.channel_names or ())
            writer.writerow(["time", *value_headers])
            for t, y in zip(signal.time_vector, signal.time_data, strict=False):
                writer.writerow([f"{t:.9g}", *np.atleast_1d(y).tolist()])

    def export_wav(self, signal: Signal, path: Path) -> None:
        from scipy.io.wavfile import write as wav_write

        path.parent.mkdir(parents=True, exist_ok=True)
        if signal.is_complex:
            raise TypeError("WAV export does not support complex-valued signals")
        peak = np.max(np.abs(signal.time_data)) if signal.n_samples else 0.0
        normalized = (
            np.zeros_like(signal.time_data, dtype=np.int16)
            if peak == 0
            else np.int16(signal.time_data / peak * 32767)
        )
        wav_write(str(path), int(signal.sampling_rate), normalized)

    def export_txt(self, signal: Signal, path: Path) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        np.savetxt(
            path,
            np.column_stack([signal.time_vector, signal.time_data]),
            header="time amplitude",
            fmt="%.6f",
        )
