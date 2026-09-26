from signal_processing_toolkit.core.constants import (
    DEFAULT_DURATION,
    DEFAULT_SAMPLING_RATE,
    FFT_SIZE,
    SUPPORTED_AUDIO_FORMATS,
    SUPPORTED_EXPORT_FORMATS,
    SUPPORTED_IMAGE_FORMATS,
)
from signal_processing_toolkit.core.events import EventBus
from signal_processing_toolkit.core.exceptions import (
    AudioError,
    DSPError,
    FileFormatError,
    FilterDesignError,
    ImageError,
    SignalProcessingError,
)


def __getattr__(name: str):
    """Load configuration support only when it is requested."""
    if name == "SettingsManager":
        from signal_processing_toolkit.core.settings import SettingsManager

        return SettingsManager
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


__all__ = [
    "EventBus",
    "SettingsManager",
    "DSPError",
    "SignalProcessingError",
    "FilterDesignError",
    "FileFormatError",
    "AudioError",
    "ImageError",
    "DEFAULT_SAMPLING_RATE",
    "DEFAULT_DURATION",
    "FFT_SIZE",
    "SUPPORTED_AUDIO_FORMATS",
    "SUPPORTED_IMAGE_FORMATS",
    "SUPPORTED_EXPORT_FORMATS",
]
