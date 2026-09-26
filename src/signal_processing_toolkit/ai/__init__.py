"""Optional Edge-AI APIs, isolated from the numerical DSP package."""

from signal_processing_toolkit.ai.evaluation import (
    ClassificationReport,
    Curve,
    ThresholdResult,
    classification_report,
    false_positive_indices,
    precision_recall_curve,
    roc_curve,
    threshold_analysis,
)
from signal_processing_toolkit.ai.model import (
    EdgeModel,
    InferenceBatch,
    ModelComparison,
    ModelMetadata,
    ModelReference,
    ModelValidationError,
    OnnxRuntimeBackend,
    TensorSpec,
    compare_models,
    select_execution_providers,
)
from signal_processing_toolkit.ai.preprocessing import PreprocessingPipeline
from signal_processing_toolkit.ai.streaming import (
    DetectedEvent,
    DetectionSettings,
    EdgeAINode,
    EventDetector,
    InferencePoint,
    SlidingWindowInference,
)

__all__ = [
    "EdgeModel",
    "EdgeAINode",
    "DetectedEvent",
    "DetectionSettings",
    "EventDetector",
    "InferenceBatch",
    "InferencePoint",
    "ModelComparison",
    "ModelMetadata",
    "ModelReference",
    "ModelValidationError",
    "OnnxRuntimeBackend",
    "PreprocessingPipeline",
    "SlidingWindowInference",
    "TensorSpec",
    "ClassificationReport",
    "Curve",
    "ThresholdResult",
    "classification_report",
    "false_positive_indices",
    "precision_recall_curve",
    "roc_curve",
    "threshold_analysis",
    "compare_models",
    "select_execution_providers",
]
