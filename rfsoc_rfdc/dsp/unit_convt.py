import numpy as np


def dB2Amp(atten_db):
    """Convert dB to amplitude. Output shall be a positive number between 0.0 and 1.0"""
    if atten_db < 0:
        raise Exception(f"Attenuation in dB: {atten_db} cannot be negative")
    return 1 / (10**(atten_db / 20))


def amp2dB(amp):
    """Convert amplitude to dB"""
    return 20 * np.log10(np.abs(amp))
