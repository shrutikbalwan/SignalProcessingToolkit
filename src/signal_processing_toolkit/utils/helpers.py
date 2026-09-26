from __future__ import annotations


def format_frequency(hz: float) -> str:
    if hz >= 1_000_000:
        return f"{hz / 1_000_000:.2f} MHz"
    elif hz >= 1_000:
        return f"{hz / 1_000:.2f} kHz"
    return f"{hz:.2f} Hz"


def format_duration(seconds: float) -> str:
    if seconds >= 60:
        return f"{seconds / 60:.2f} min"
    elif seconds >= 1:
        return f"{seconds:.2f} s"
    elif seconds >= 0.001:
        return f"{seconds * 1000:.2f} ms"
    return f"{seconds * 1_000_000:.2f} us"


def format_samples(n: int) -> str:
    if n >= 1_000_000:
        return f"{n / 1_000_000:.2f} M"
    elif n >= 1_000:
        return f"{n / 1_000:.2f} K"
    return str(n)


def clamp(value: float, min_val: float, max_val: float) -> float:
    return max(min_val, min(value, max_val))


def db_to_linear(db: float) -> float:
    return 10 ** (db / 20.0)


def linear_to_db(linear: float) -> float:
    import numpy as np

    return float(20 * np.log10(max(linear, 1e-10)))
