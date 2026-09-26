"""Service facade with lazy imports for optional feature isolation."""

from __future__ import annotations

from importlib import import_module

_EXPORTS = {
    "AnalysisService": "signal_processing_toolkit.services.analysis_service",
    "SignalService": "signal_processing_toolkit.services.signal_service",
    "AudioService": "signal_processing_toolkit.services.audio_service",
    "ImageService": "signal_processing_toolkit.services.image_service",
    "FilterService": "signal_processing_toolkit.services.filter_service",
    "FFTService": "signal_processing_toolkit.services.fft_service",
    "SamplingService": "signal_processing_toolkit.services.sampling_service",
    "ConvolutionService": "signal_processing_toolkit.services.convolution_service",
    "CorrelationService": "signal_processing_toolkit.services.correlation_service",
    "WindowService": "signal_processing_toolkit.services.window_service",
    "NoiseService": "signal_processing_toolkit.services.noise_service",
}

__all__ = list(_EXPORTS)


def __getattr__(name: str):
    """Import one service without importing unrelated optional integrations."""
    try:
        module_name = _EXPORTS[name]
    except KeyError:
        raise AttributeError(f"module {__name__!r} has no attribute {name!r}") from None
    value = getattr(import_module(module_name), name)
    globals()[name] = value
    return value
