import matplotlib.pyplot as plt
import numpy as np
import scipy.signal as signal


def compute_fft(data, fs):
    """Computes the Fast Fourier Transform of a 1D signal."""
    N = len(data)
    yf = np.fft.fft(data)
    xf = np.fft.fftfreq(N, 1 / fs)
    return xf[: N // 2], 2.0 / N * np.abs(yf[: N // 2])


def compute_stft(data, fs, nperseg=256):
    """Computes the Short-Time Fourier Transform."""
    f, t, Zxx = signal.stft(data, fs, nperseg=nperseg)
    return f, t, np.abs(Zxx)


def plot_spectrogram(f, t, Sxx):
    """Visualizes STFT output as a spectrogram."""
    plt.pcolormesh(t, f, 10 * np.log10(Sxx), shading="gouraud")
    plt.ylabel("Frequency [Hz]")
    plt.xlabel("Time [sec]")
    plt.colorbar(label="Power/Frequency (dB/Hz)")
    plt.show()
