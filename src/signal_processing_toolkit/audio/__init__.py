"""Optional audio integrations; importing this package does not import sounddevice."""

from signal_processing_toolkit.audio.streaming import (
    AudioBackend,
    AudioDevice,
    AudioSourceMetrics,
    AudioStreamConfig,
    SoundDeviceAudioSource,
    SoundDeviceBackend,
    enumerate_audio_devices,
)

__all__ = [
    "AudioBackend",
    "AudioDevice",
    "AudioSourceMetrics",
    "AudioStreamConfig",
    "SoundDeviceAudioSource",
    "SoundDeviceBackend",
    "enumerate_audio_devices",
]
