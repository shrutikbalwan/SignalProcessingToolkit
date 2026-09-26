from typing import Final

DEFAULT_SAMPLING_RATE: Final = 44100.0
DEFAULT_DURATION: Final = 1.0
FFT_SIZE: Final = 4096
MAX_SIGNAL_LENGTH: Final = 1_000_000
NYQUIST_RATIO: Final = 0.5

SUPPORTED_AUDIO_FORMATS: Final = {".wav", ".mp3", ".flac", ".ogg", ".aiff"}
SUPPORTED_IMAGE_FORMATS: Final = {".png", ".jpg", ".jpeg", ".bmp", ".tiff"}
SUPPORTED_EXPORT_FORMATS: Final = {".csv", ".xlsx", ".txt", ".mat"}

WINDOW_TYPES: Final = [
    "rectangular",
    "hamming",
    "hanning",
    "blackman",
    "bartlett",
    "kaiser",
]

WAVEFORM_TYPES: Final = [
    "sine",
    "cosine",
    "square",
    "triangle",
    "sawtooth",
    "pulse",
    "chirp",
    "gaussian",
    "noise",
    "dc",
]

FILTER_TYPES: Final = ["lowpass", "highpass", "bandpass", "bandstop"]
RESPONSE_TYPES: Final = ["fir", "iir"]
IIR_DESIGN_METHODS: Final = ["butterworth", "chebyshev1", "chebyshev2", "elliptic"]

APP_NAME: Final = "Signal Processing Toolkit"
APP_VERSION: Final = "1.0.0"
ORG_NAME: Final = "SPT"
