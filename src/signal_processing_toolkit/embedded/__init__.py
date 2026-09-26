"""Embedded-target fixed-point simulation and portable code generation.

The module is deliberately dependency-free beyond NumPy.  Generated timing
figures are estimates; target measurements are required for cycle accuracy.
"""

from .compare import ComparisonReport, compare_results
from .export import ExportArtifact, export_filter
from .filters import simulate_fir, simulate_sos
from .fixed import (
    FixedPointConfig,
    FixedPointResult,
    OverflowMode,
    QFormat,
    RoundingMode,
    simulate_fixed,
)

__all__ = [
    "ComparisonReport",
    "ExportArtifact",
    "FixedPointConfig",
    "FixedPointResult",
    "OverflowMode",
    "RoundingMode",
    "QFormat",
    "compare_results",
    "export_filter",
    "simulate_fixed",
    "simulate_fir",
    "simulate_sos",
]
