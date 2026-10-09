import matplotlib.pyplot as plt
import numpy as np
import scipy.signal as signal


def compute_fft(data, fs):
    """Compute the Fast Fourier Transform of a 1D signal."""
    n = len(data)
    yf = np.fft.fft(data)
    xf = np.fft.fftfreq(n, 1 / fs)
    return xf[: n // 2], 2.0 / n * np.abs(yf[: n // 2])


def compute_stft(data, fs, nperseg=256):
    """Compute the Short-Time Fourier Transform."""
    f, t, zxx = signal.stft(data, fs, nperseg=nperseg)
    return f, t, np.abs(zxx)


def plot_spectrogram(f, t, sxx):
    """Visualizes STFT output as a spectrogram."""
    plt.pcolormesh(t, f, 10 * np.log10(sxx), shading="gouraud")
