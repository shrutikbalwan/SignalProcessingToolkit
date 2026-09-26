"""Model metadata, runtime validation, and optional ONNX Runtime loading."""

from __future__ import annotations

import hashlib
import json
import time
import tracemalloc
from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Literal, Protocol

import numpy as np

from signal_processing_toolkit.ai.preprocessing import PreprocessingPipeline


class ModelValidationError(ValueError):
    """Raised before execution when model or metadata contracts are invalid."""


@dataclass(frozen=True, slots=True)
class TensorSpec:
    name: str
    shape: tuple[int | None, ...]
    dtype: str


@dataclass(frozen=True, slots=True)
class ModelMetadata:
    labels: tuple[str, ...]
    preprocessing: PreprocessingPipeline
    input_name: str
    output_name: str
    output_kind: Literal["probabilities", "logits"] = "probabilities"
    description: str = ""
    license: str = ""

    def __post_init__(self) -> None:
        if len(self.labels) < 2 or any(not label.strip() for label in self.labels):
            raise ModelValidationError("Model metadata requires at least two non-empty labels")
        if len(set(self.labels)) != len(self.labels):
            raise ModelValidationError("Model labels must be unique")
        if not self.input_name or not self.output_name:
            raise ModelValidationError("Model input and output names are required")

    def to_dict(self) -> dict[str, Any]:
        return {
            "labels": list(self.labels),
            "preprocessing": self.preprocessing.to_dict(),
            "input_name": self.input_name,
            "output_name": self.output_name,
            "output_kind": self.output_kind,
            "description": self.description,
            "license": self.license,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> ModelMetadata:
        required = {"labels", "preprocessing", "input_name", "output_name"}
        missing = sorted(required - data.keys())
        if missing:
            raise ModelValidationError(f"Missing model metadata: {', '.join(missing)}")
        return cls(
            labels=tuple(data["labels"]),
            preprocessing=PreprocessingPipeline.from_dict(data["preprocessing"]),
            input_name=str(data["input_name"]),
            output_name=str(data["output_name"]),
            output_kind=data.get("output_kind", "probabilities"),
            description=str(data.get("description", "")),
            license=str(data.get("license", "")),
        )


@dataclass(frozen=True, slots=True)
class InferenceBatch:
    probabilities: np.ndarray
    labels: tuple[str, ...]
    latency_seconds: float
    throughput_windows_per_second: float
    peak_python_bytes: int

    @property
    def predicted_indices(self) -> np.ndarray:
        return np.argmax(self.probabilities, axis=1)


class RuntimeSession(Protocol):
    @property
    def inputs(self) -> Sequence[TensorSpec]: ...

    @property
    def outputs(self) -> Sequence[TensorSpec]: ...

    @property
    def providers(self) -> Sequence[str]: ...

    def run(
        self, output_names: Sequence[str], inputs: dict[str, np.ndarray]
    ) -> list[np.ndarray]: ...


class RuntimeBackend(Protocol):
    def available_providers(self) -> Sequence[str]: ...

    def create_session(self, path: Path, providers: Sequence[str]) -> RuntimeSession: ...


def select_execution_providers(
    available: Sequence[str], preferred: Sequence[str] | None = None
) -> tuple[str, ...]:
    """Select requested providers in order, with CPU as a safe fallback."""
    available_unique = tuple(dict.fromkeys(available))
    if not available_unique:
        raise RuntimeError("No ONNX Runtime execution provider is available")
    selected = [item for item in (preferred or ()) if item in available_unique]
    if "CPUExecutionProvider" in available_unique and "CPUExecutionProvider" not in selected:
        selected.append("CPUExecutionProvider")
    if not selected:
        selected.append(available_unique[0])
    return tuple(selected)


class OnnxRuntimeBackend:
    """Lazy ONNX Runtime adapter; importing this module does not require ORT."""

    @staticmethod
    def _ort() -> Any:
        try:
            import onnxruntime as ort
        except ImportError as exc:
            raise RuntimeError(
                "ONNX inference requires the 'ai' extra: "
                "pip install 'signal-processing-toolkit[ai]'"
            ) from exc
        return ort

    def available_providers(self) -> Sequence[str]:
        return tuple(self._ort().get_available_providers())

    def create_session(self, path: Path, providers: Sequence[str]) -> RuntimeSession:
        ort = self._ort()
        session = ort.InferenceSession(str(path), providers=list(providers))
        return _OrtSession(session)


class _OrtSession:
    def __init__(self, session: Any) -> None:
        self._session = session

    @staticmethod
    def _spec(value: Any) -> TensorSpec:
        shape = tuple(item if isinstance(item, int) and item > 0 else None for item in value.shape)
        dtype = {"tensor(float)": "float32", "tensor(double)": "float64"}.get(
            value.type, value.type
        )
        return TensorSpec(value.name, shape, dtype)

    @property
    def inputs(self) -> Sequence[TensorSpec]:
        return tuple(self._spec(value) for value in self._session.get_inputs())

    @property
    def outputs(self) -> Sequence[TensorSpec]:
        return tuple(self._spec(value) for value in self._session.get_outputs())

    @property
    def providers(self) -> Sequence[str]:
        return tuple(self._session.get_providers())

    def run(self, output_names: Sequence[str], inputs: dict[str, np.ndarray]) -> list[np.ndarray]:
        return list(self._session.run(list(output_names), inputs))


@dataclass(frozen=True, slots=True)
class ModelReference:
    path: str
    checksum_sha256: str
    labels: tuple[str, ...]
    preprocessing: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        return {
            "path": self.path,
            "checksum_sha256": self.checksum_sha256,
            "labels": list(self.labels),
            "preprocessing": self.preprocessing,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> ModelReference:
        return cls(
            path=str(data["path"]),
            checksum_sha256=str(data["checksum_sha256"]),
            labels=tuple(data["labels"]),
            preprocessing=dict(data["preprocessing"]),
        )


class EdgeModel:
    """Validated ONNX/ORT model plus its immutable preprocessing contract."""

    def __init__(
        self,
        path: Path,
        metadata: ModelMetadata,
        session: RuntimeSession,
        checksum_sha256: str,
    ) -> None:
        self.path = path
        self.metadata = metadata
        self.session = session
        self.checksum_sha256 = checksum_sha256
        self._validate_contract()

    @classmethod
    def load(
        cls,
        path: str | Path,
        *,
        metadata_path: str | Path | None = None,
        providers: Sequence[str] | None = None,
        backend: RuntimeBackend | None = None,
    ) -> EdgeModel:
        model_path = Path(path)
        if model_path.suffix.lower() not in {".onnx", ".ort"}:
            raise ModelValidationError("Model must use the .onnx or .ort extension")
        if not model_path.is_file():
            raise FileNotFoundError(model_path)
        sidecar = Path(metadata_path) if metadata_path else model_path.with_suffix(".metadata.json")
        if not sidecar.is_file():
            raise ModelValidationError(f"Required preprocessing metadata not found: {sidecar}")
        metadata = ModelMetadata.from_dict(json.loads(sidecar.read_text(encoding="utf-8")))
        runtime = backend or OnnxRuntimeBackend()
        selected = select_execution_providers(runtime.available_providers(), providers)
        session = runtime.create_session(model_path, selected)
        checksum = hashlib.sha256(model_path.read_bytes()).hexdigest()
        return cls(model_path, metadata, session, checksum)

    def _validate_contract(self) -> None:
        inputs = {item.name: item for item in self.session.inputs}
        outputs = {item.name: item for item in self.session.outputs}
        if self.metadata.input_name not in inputs:
            raise ModelValidationError(f"Model has no input named {self.metadata.input_name!r}")
        if self.metadata.output_name not in outputs:
            raise ModelValidationError(f"Model has no output named {self.metadata.output_name!r}")
        input_spec = inputs[self.metadata.input_name]
        output_spec = outputs[self.metadata.output_name]
        if input_spec.dtype not in {"float32", "tensor(float)"}:
            raise ModelValidationError("Only float32 model inputs are supported")
        if len(input_spec.shape) not in {3, 4}:
            raise ModelValidationError("Model input must be batched time or spectrogram data")
        expected_rank = 3 if self.metadata.preprocessing.mode == "time" else 4
        if len(input_spec.shape) != expected_rank:
            raise ModelValidationError(
                f"{self.metadata.preprocessing.mode} preprocessing requires "
                f"rank-{expected_rank} input"
            )
        if len(output_spec.shape) != 2:
            raise ModelValidationError("Model output must have shape (batch, classes)")
        if output_spec.shape[-1] not in {None, len(self.metadata.labels)}:
            raise ModelValidationError("Model output class count does not match metadata labels")

    def predict(self, windows: np.ndarray) -> InferenceBatch:
        features = self.metadata.preprocessing.transform_batch(windows)
        spec = next(item for item in self.session.inputs if item.name == self.metadata.input_name)
        self._validate_array_shape(features, spec)
        tracemalloc.start()
        started = time.perf_counter()
        try:
            outputs = self.session.run(
                [self.metadata.output_name], {self.metadata.input_name: features}
            )
            elapsed = time.perf_counter() - started
            _, peak = tracemalloc.get_traced_memory()
        finally:
            tracemalloc.stop()
        if len(outputs) != 1:
            raise ModelValidationError("Runtime did not return the requested single output")
        scores = np.asarray(outputs[0], dtype=np.float64)
        if scores.shape != (features.shape[0], len(self.metadata.labels)):
            raise ModelValidationError(
                f"Expected output shape {(features.shape[0], len(self.metadata.labels))}, "
                f"got {scores.shape}"
            )
        if not np.all(np.isfinite(scores)):
            raise ModelValidationError("Model output contains NaN or infinite values")
        probabilities = self._probabilities(scores)
        return InferenceBatch(
            probabilities=probabilities,
            labels=self.metadata.labels,
            latency_seconds=elapsed,
            throughput_windows_per_second=features.shape[0] / max(elapsed, np.finfo(float).eps),
            peak_python_bytes=peak,
        )

    @staticmethod
    def _validate_array_shape(values: np.ndarray, spec: TensorSpec) -> None:
        if values.ndim != len(spec.shape):
            raise ModelValidationError(
                f"Input rank mismatch: model expects {len(spec.shape)}, got {values.ndim}"
            )
        for axis, (actual, expected) in enumerate(zip(values.shape, spec.shape, strict=True)):
            if expected is not None and actual != expected:
                raise ModelValidationError(f"Input axis {axis} expects {expected}, got {actual}")

    def _probabilities(self, scores: np.ndarray) -> np.ndarray:
        if self.metadata.output_kind == "logits":
            shifted = scores - np.max(scores, axis=1, keepdims=True)
            exponent = np.exp(shifted)
            return np.asarray(exponent / np.sum(exponent, axis=1, keepdims=True))
        if np.any(scores < 0) or np.any(scores > 1):
            raise ModelValidationError("Probability output contains values outside [0, 1]")
        totals = np.sum(scores, axis=1)
        if not np.allclose(totals, 1.0, atol=1e-5):
            raise ModelValidationError("Probability rows must sum to one")
        return scores

    @property
    def reference(self) -> ModelReference:
        return ModelReference(
            path=str(self.path),
            checksum_sha256=self.checksum_sha256,
            labels=self.metadata.labels,
            preprocessing=self.metadata.preprocessing.to_dict(),
        )


@dataclass(frozen=True, slots=True)
class ModelComparison:
    float_checksum: str
    quantized_checksum: str
    label_agreement: float
    mean_absolute_probability_error: float
    maximum_absolute_probability_error: float
    float_latency_seconds: float
    quantized_latency_seconds: float
    float_size_bytes: int
    quantized_size_bytes: int


def compare_models(
    float_model: EdgeModel, quantized_model: EdgeModel, windows: np.ndarray
) -> ModelComparison:
    if float_model.metadata.labels != quantized_model.metadata.labels:
        raise ModelValidationError("Models must use identical labels for comparison")
    first = float_model.predict(windows)
    second = quantized_model.predict(windows)
    difference = np.abs(first.probabilities - second.probabilities)
    return ModelComparison(
        float_checksum=float_model.checksum_sha256,
        quantized_checksum=quantized_model.checksum_sha256,
        label_agreement=float(np.mean(first.predicted_indices == second.predicted_indices)),
        mean_absolute_probability_error=float(np.mean(difference)),
        maximum_absolute_probability_error=float(np.max(difference)),
        float_latency_seconds=first.latency_seconds,
        quantized_latency_seconds=second.latency_seconds,
        float_size_bytes=float_model.path.stat().st_size,
        quantized_size_bytes=quantized_model.path.stat().st_size,
    )
