from enum import Enum, auto


class WaveformType(Enum):
    SINE = "sine"
    COSINE = "cosine"
    SQUARE = "square"
    TRIANGLE = "triangle"
    SAWTOOTH = "sawtooth"
    PULSE = "pulse"
    CHIRP = "chirp"
    GAUSSIAN = "gaussian"
    NOISE = "noise"
    DC = "dc"


class WindowType(Enum):
    RECTANGULAR = "rectangular"
    HAMMING = "hamming"
    HANNING = "hanning"
    BLACKMAN = "blackman"
    BARTLETT = "bartlett"
    KAISER = "kaiser"


class FilterType(Enum):
    LOWPASS = "lowpass"
    HIGHPASS = "highpass"
    BANDPASS = "bandpass"
    BANDSTOP = "bandstop"


class ResponseType(Enum):
    FIR = "fir"
    IIR = "iir"


class DesignMethod(Enum):
    BUTTERWORTH = "butterworth"
    CHEBYSHEV1 = "chebyshev1"
    CHEBYSHEV2 = "chebyshev2"
    ELLIPTIC = "elliptic"
    WINDOW = "window"
    EQUIRIPPLE = "equiripple"
    LEAST_SQUARES = "least_squares"


class NoiseType(Enum):
    WHITE = "white"
    PINK = "pink"
    BROWNIAN = "brownian"
    IMPULSE = "impulse"


class SignalDomain(Enum):
    TIME = "time"
    FREQUENCY = "frequency"
    TIME_FREQUENCY = "time_frequency"


class CorrelationType(Enum):
    AUTO = auto()
    CROSS = auto()
