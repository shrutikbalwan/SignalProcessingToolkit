"""End-to-end ESP32 predictive-maintenance workbench demonstration.

The default source is deterministic and uses the production binary packet
parser, so the workflow is useful without hardware.  Replace the source with
``SerialSensorSource`` and a real ``EdgeModel`` for an ESP32 deployment.
"""

from __future__ import annotations

import argparse
import json
import time
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

import numpy as np
from scipy import signal as scipy_signal

from signal_processing_toolkit.ai.model import InferenceBatch
from signal_processing_toolkit.dsp.analysis.analytic import signal_envelope
from signal_processing_toolkit.dsp.analysis.spectral import band_power
from signal_processing_toolkit.dsp.fft import compute_fft
from signal_processing_toolkit.embedded import ExportArtifact, export_filter
from signal_processing_toolkit.hardware.protocol import (
    BinaryPacketParser,
    SensorPacket,
    encode_binary_packet,
)
from signal_processing_toolkit.models.signal import Signal
from signal_processing_toolkit.streaming.model import ChannelMetadata, StreamChunk


@dataclass(frozen=True, slots=True)
class ExperimentConfig:
    sampling_rate: float = 2_000.0
    channels: int = 1
    frame_size: int = 128
    duration_seconds: float = 2.048
    low_cut_hz: float = 80.0
    high_cut_hz: float = 450.0
    calibration_scale: float = 1.0
    calibration_offset: float = 0.0
    model_window: int = 256
    model_hop: int = 128
    seed: int = 7
    faulty: bool = False

    def __post_init__(self) -> None:
        if self.sampling_rate <= 0 or self.channels != 1 or self.frame_size <= 0:
            raise ValueError("sampling_rate, frame_size and one channel are required")
        if (
            self.duration_seconds <= 0
            or not 0 < self.low_cut_hz < self.high_cut_hz < self.sampling_rate / 2
        ):
            raise ValueError("invalid duration or band-pass limits")
        if self.model_window <= 0 or not 0 < self.model_hop <= self.model_window:
            raise ValueError("invalid inference window/hop")


class SimulatedMaintenanceSource:
    """Deterministic healthy/faulty accelerometer source using binary packets."""

    def __init__(self, config: ExperimentConfig) -> None:
        self.config = config

    def packets(self) -> tuple[SensorPacket, ...]:
        count = int(round(self.config.duration_seconds * self.config.sampling_rate))
        time_axis = np.arange(count) / self.config.sampling_rate
        rng = np.random.default_rng(self.config.seed)
        values = 0.35 * np.sin(2 * np.pi * 180 * time_axis)
        values += 0.02 * rng.standard_normal(count)
        values += 0.02  # deterministic sensor bias for calibration/DC removal
        if self.config.faulty:
            values += (
                0.22 * np.sin(2 * np.pi * 30 * time_axis) * np.sin(2 * np.pi * 180 * time_axis)
            )
            for index in range(180, count, 400):
                values[index : index + 5] += np.hanning(min(5, count - index)) * 0.9
        packets: list[SensorPacket] = []
        for sequence, start in enumerate(range(0, count, self.config.frame_size)):
            samples = values[start : start + self.config.frame_size, np.newaxis]
            if len(samples):
                packets.append(SensorPacket(sequence, start / self.config.sampling_rate, samples))
        return tuple(packets)

    def chunks(self) -> tuple[StreamChunk, ...]:
        return tuple(
            StreamChunk(
                packet.samples,
                self.config.sampling_rate,
                (ChannelMetadata("accelerometer_z", "g"),),
                packet.sequence,
                packet.timestamp,
            )
            for packet in self.packets()
        )

    def encoded_fragments(self) -> tuple[bytes, ...]:
        """Return packet bytes fragmented as a serial link commonly delivers them."""
        fragments: list[bytes] = []
        for packet in self.packets():
            encoded = encode_binary_packet(packet)
            fragments.extend(encoded[index : index + 37] for index in range(0, len(encoded), 37))
        return tuple(fragments)


class DeterministicAnomalyModel:
    """Small local model substitute; an ONNX model can implement the same protocol."""

    labels = ("healthy", "fault")

    def predict(self, windows: np.ndarray) -> InferenceBatch:
        started = time.perf_counter()
        scores: list[list[float]] = []
        for window in np.asarray(windows):
            values = np.asarray(window, dtype=float).reshape(-1)
            rms = float(np.sqrt(np.mean(values**2)))
            crest = float(np.max(np.abs(values)) / max(rms, 1e-12))
            fault = float(
                np.clip(0.55 * max(crest - 1.8, 0.0) + 3.0 * max(rms - 0.20, 0.0), 0.0, 1.0)
            )
            scores.append([1.0 - fault, fault])
        probabilities = np.asarray(scores, dtype=float)
        elapsed = time.perf_counter() - started
        return InferenceBatch(
            probabilities=probabilities,
            labels=self.labels,
            latency_seconds=elapsed,
            throughput_windows_per_second=len(scores) / max(elapsed, np.finfo(float).eps),
            peak_python_bytes=0,
        )


@dataclass(frozen=True, slots=True)
class ExperimentResult:
    config: ExperimentConfig
    packet_count: int
    packet_loss: int
    dsp_latency_seconds: float
    inference_latency_seconds: float
    measurements: dict[str, float]
    predictions: tuple[str, ...]
    events: tuple[dict[str, Any], ...]
    raw_samples: np.ndarray = field(repr=False)
    processed_samples: np.ndarray = field(repr=False)

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data.pop("raw_samples", None)
        data.pop("processed_samples", None)
        data["config"] = asdict(self.config)
        return data


@dataclass(frozen=True, slots=True)
class DashboardSnapshot:
    packet_loss: int
    dsp_latency_seconds: float
    inference_latency_seconds: float
    latest_prediction: str
    event_count: int


class PredictiveMaintenanceWorkbench:
    """Compose acquisition, stateful DSP, analysis, inference and reporting."""

    def __init__(self, config: ExperimentConfig | None = None, model: Any | None = None) -> None:
        self.config = config or ExperimentConfig()
        self.model = model or DeterministicAnomalyModel()
        self._sos = scipy_signal.butter(
            4,
            (self.config.low_cut_hz, self.config.high_cut_hz),
            btype="bandpass",
            fs=self.config.sampling_rate,
            output="sos",
        )

    @classmethod
    def with_onnx_model(
        cls,
        model_path: str | Path,
        *,
        metadata_path: str | Path | None = None,
        config: ExperimentConfig | None = None,
    ) -> PredictiveMaintenanceWorkbench:
        """Create a workbench backed by the validated optional ONNX runtime."""
        from signal_processing_toolkit.ai.model import EdgeModel

        model = EdgeModel.load(model_path, metadata_path=metadata_path)
        selected = config or ExperimentConfig(sampling_rate=2_048.0)
        if not np.isclose(model.metadata.preprocessing.sampling_rate, selected.sampling_rate):
            raise ValueError("Workbench and model preprocessing sampling rates must match")
        return cls(selected, model)

    def run(self, chunks: tuple[StreamChunk, ...] | None = None) -> ExperimentResult:
        source = SimulatedMaintenanceSource(self.config)
        source_chunks = source.chunks() if chunks is None else chunks
        parser = BinaryPacketParser()
        parsed = sum((parser.feed(fragment) for fragment in source.encoded_fragments()), ())
        packet_loss = max(0, len(source.packets()) - len(parsed))
        filter_state: np.ndarray | None = None
        dc_state: np.ndarray | None = None
        processed_parts: list[np.ndarray] = []
        raw_parts: list[np.ndarray] = []
        dsp_started = time.perf_counter()
        for chunk in source_chunks:
            values = (
                chunk.samples[:, 0] * self.config.calibration_scale - self.config.calibration_offset
            )
            alpha = float(np.exp(-2 * np.pi * 5.0 / chunk.sampling_rate))
            values, dc_state = scipy_signal.lfilter(
                [1.0, -1.0],
                [1.0, -alpha],
                values,
                zi=np.zeros(1) if dc_state is None else dc_state,
            )
            values, filter_state = scipy_signal.sosfilt(
                self._sos,
                values,
                zi=(np.zeros((len(self._sos), 2)) if filter_state is None else filter_state),
            )
            raw_parts.append(chunk.samples[:, 0].copy())
            processed_parts.append(values)
        raw = np.concatenate(raw_parts) if raw_parts else np.empty(0)
        processed = np.concatenate(processed_parts) if processed_parts else np.empty(0)
        dsp_latency = time.perf_counter() - dsp_started
        signal = Signal(
            processed, self.config.sampling_rate, channel_names=("filtered",), units=("g",)
        )
        envelope = signal_envelope(signal)
        detrended_envelope = envelope.updated(
            time_data=envelope.time_data - np.mean(envelope.time_data),
            operation="envelope_detrend",
        )
        spectrum = compute_fft(detrended_envelope, window="hann")
        measurements = {
            "rms_g": float(np.sqrt(np.mean(processed**2))) if processed.size else 0.0,
            "crest_factor": float(
                np.max(np.abs(processed)) / max(np.sqrt(np.mean(processed**2)), 1e-12)
            )
            if processed.size
            else 0.0,
            "envelope_band_power": float(band_power(envelope, 10.0, 100.0)),
            "envelope_peak_hz": float(spectrum.frequencies[int(np.argmax(spectrum.magnitude))]),
        }
        inference_started = time.perf_counter()
        predictions: list[str] = []
        events: list[dict[str, Any]] = []
        for start in range(
            0, max(0, len(processed) - self.config.model_window + 1), self.config.model_hop
        ):
            batch = self.model.predict(
                processed[start : start + self.config.model_window][np.newaxis, :]
            )
            predicted = self.model.labels[int(np.argmax(batch.probabilities[0]))]
            predictions.append(predicted)
            if predicted == "fault":
                events.append(
                    {
                        "sample": start,
                        "label": predicted,
                        "confidence": float(batch.probabilities[0, 1]),
                    }
                )
        inference_latency = time.perf_counter() - inference_started
        return ExperimentResult(
            self.config,
            len(parsed),
            packet_loss,
            dsp_latency,
            inference_latency,
            measurements,
            tuple(predictions),
            tuple(events),
            raw,
            processed,
        )

    def save(self, result: ExperimentResult, directory: str | Path) -> Path:
        target = Path(directory)
        target.mkdir(parents=True, exist_ok=True)
        np.savez_compressed(
            target / "recording.npz", raw=result.raw_samples, processed=result.processed_samples
        )
        (target / "experiment.json").write_text(
            json.dumps(result.to_dict(), indent=2), encoding="utf-8"
        )
        (target / "diagnostic_report.md").write_text(self.report(result), encoding="utf-8")
        artifact = self.export_filter()
        (target / "filter.h").write_text(artifact.header, encoding="utf-8")
        (target / "filter.c").write_text(artifact.source, encoding="utf-8")
        (target / "vectors.json").write_text(artifact.test_vectors, encoding="utf-8")
        return target

    @classmethod
    def reopen(cls, directory: str | Path) -> ExperimentResult:
        target = Path(directory)
        payload = json.loads((target / "experiment.json").read_text(encoding="utf-8"))
        config = ExperimentConfig(**payload["config"])
        arrays = np.load(target / "recording.npz")
        return ExperimentResult(
            config,
            payload["packet_count"],
            payload["packet_loss"],
            payload["dsp_latency_seconds"],
            payload["inference_latency_seconds"],
            payload["measurements"],
            tuple(payload["predictions"]),
            tuple(payload["events"]),
            arrays["raw"],
            arrays["processed"],
        )

    @classmethod
    def replay(cls, directory: str | Path) -> ExperimentResult:
        saved = cls.reopen(directory)
        chunks = tuple(
            StreamChunk(
                saved.raw_samples[start : start + saved.config.frame_size, np.newaxis],
                saved.config.sampling_rate,
                (ChannelMetadata("accelerometer_z", "g"),),
                sequence,
                start / saved.config.sampling_rate,
            )
            for sequence, start in enumerate(
                range(0, len(saved.raw_samples), saved.config.frame_size)
            )
        )
        return cls(saved.config).run(chunks)

    @staticmethod
    def dashboard_snapshot(result: ExperimentResult) -> DashboardSnapshot:
        return DashboardSnapshot(
            result.packet_loss,
            result.dsp_latency_seconds,
            result.inference_latency_seconds,
            result.predictions[-1] if result.predictions else "idle",
            len(result.events),
        )

    def report(self, result: ExperimentResult) -> str:
        return "\n".join(
            [
                "# ESP32 Predictive Maintenance Diagnostic Report",
                "",
                f"- Packets: {result.packet_count}",
                f"- Packet loss: {result.packet_loss}",
                f"- DSP latency (host measurement): {result.dsp_latency_seconds:.6f} s",
                f"- Inference latency (host measurement): {result.inference_latency_seconds:.6f} s",
                "- Performance values are host measurements, not cycle-accurate target claims.",
                "",
                "## Engineering measurements",
                *(f"- {name}: {value:.6g}" for name, value in result.measurements.items()),
                "",
                f"Events detected: {len(result.events)}",
            ]
        )

    def export_filter(self) -> ExportArtifact:
        return export_filter(
            self._sos,
            sample_rate=self.config.sampling_rate,
            frame_size=self.config.frame_size,
            channels=self.config.channels,
            name="esp32_bandpass",
            kind="sos",
            backend="cmsis",
        )


def main() -> int:
    parser = argparse.ArgumentParser(description="Run the deterministic ESP32 maintenance demo")
    parser.add_argument("--faulty", action="store_true", help="simulate a faulty bearing")
    parser.add_argument("--save", type=Path, help="save the complete experiment directory")
    args = parser.parse_args()
    workbench = PredictiveMaintenanceWorkbench(ExperimentConfig(faulty=args.faulty))
    result = workbench.run()
    if args.save:
        workbench.save(result, args.save)
    print(workbench.report(result))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
