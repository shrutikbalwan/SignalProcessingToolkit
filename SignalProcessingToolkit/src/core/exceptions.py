class DSPError(Exception):
    """Base exception for all DSP-related errors."""


class SignalProcessingError(DSPError):
    """Raised when a signal processing operation fails."""


class FilterDesignError(DSPError):
    """Raised when filter design or application fails."""


class FileFormatError(DSPError):
    """Raised when file format is unsupported or malformed."""


class AudioError(DSPError):
    """Raised during audio playback or recording errors."""


class ImageError(DSPError):
    """Raised during image processing errors."""


class ValidationError(DSPError):
    """Raised when input validation fails."""


class ConfigurationError(DSPError):
    """Raised when application configuration is invalid."""


class PluginError(DSPError):
    """Raised when a plugin operation fails."""
