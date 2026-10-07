import scipy.signal as signal

def design_butterworth(order, cutoff, fs, btype='low'):
    """Designs a digital Butterworth filter."""
    nyq = 0.5 * fs
    normal_cutoff = cutoff / nyq
    b, a = signal.butter(order, normal_cutoff, btype=btype, analog=False)
    return b, a

def design_chebyshev(order, rp, cutoff, fs, btype='low'):
    """Designs a digital Chebyshev Type I filter."""
    nyq = 0.5 * fs
    normal_cutoff = cutoff / nyq
    b, a = signal.cheby1(order, rp, normal_cutoff, btype=btype, analog=False)
    return b, a
