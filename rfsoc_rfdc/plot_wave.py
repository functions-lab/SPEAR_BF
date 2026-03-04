#!/usr/bin/env python3
"""
Plot RFSoC captures stored as HDF5/NumPy/Matlab files.

Time-domain plots always render, while the FFT plot can be toggled via
--fft. Uses the shared HDF5 logging backend so waveforms are read exactly
as they were captured.
"""

import argparse
from pathlib import Path
from typing import Tuple

import matplotlib.pyplot as plt
import numpy as np
from numpy.fft import fft, fftfreq, fftshift
from scipy.io import loadmat

from rfsoc_rfdc.sample_logger import HDF5Logger


def load_samples(path: Path, dataset: str) -> Tuple[np.ndarray, dict]:
    """Load IQ samples plus metadata from .h5/.npy/.mat files."""
    suffix = path.suffix.lower()

    if suffix == ".h5":
        loader = HDF5Logger()
        data, metadata = loader.load(str(path), dataset_name=dataset)
        return data, metadata

    if suffix == ".npy":
        data = np.load(path)
        return data, {}

    if suffix == ".mat":
        mat = loadmat(path)
        for key in ("wave", "iq_samples", "data"):
            if key in mat:
                data = np.asarray(mat[key]).squeeze()
                return data, {}
        raise KeyError(
            f"No supported variable (wave/iq_samples/data) in {path}")

    raise ValueError(f"Unsupported file type: {path.suffix}")


def select_window(data: np.ndarray, start: int, count: int = None) -> np.ndarray:
    """Return a slice of the data, handling bounds gracefully."""
    n = data.shape[0]
    if start >= n:
        raise ValueError(f"Start index {start} exceeds capture length {n}")
    end = start + count if count is not None else n
    return data[start:end]


def plot_time_domain(samples: np.ndarray,
                     sample_rate: float = None,
                     title: str = None):
    """Plot real and imaginary components of the samples."""
    num_samples = samples.shape[0]
    if sample_rate:
        time_axis = np.arange(num_samples) / sample_rate
        xlabel = "Time (s)"
    else:
        time_axis = np.arange(num_samples)
        xlabel = "Sample Index"

    plt.figure(figsize=(12, 5))
    plt.plot(time_axis, samples.real, label="I (real)")
    plt.plot(time_axis, samples.imag, label="Q (imag)")
    plt.xlabel(xlabel)
    plt.ylabel("Amplitude")
    plt.title(title or "Captured Waveform")
    plt.legend()
    plt.grid(True, alpha=0.3)


def plot_fft(samples: np.ndarray, sample_rate: float):
    """Plot magnitude spectrum using FFT."""
    if sample_rate is None:
        raise ValueError("--sample-rate is required for FFT plots.")

    windowed = samples * np.hanning(len(samples))
    spectrum = fftshift(fft(windowed))
    freq_axis = fftshift(fftfreq(len(samples), d=1.0 / sample_rate))

    plt.figure(figsize=(12, 5))
    plt.plot(freq_axis / 1e6, 20 * np.log10(np.abs(spectrum) + 1e-12))
    plt.xlabel("Frequency (MHz)")
    plt.ylabel("Magnitude (dBFS)")
    plt.title("FFT Magnitude")
    plt.grid(True, alpha=0.3)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Plot IQ captures stored as .h5/.npy/.mat files.")
    parser.add_argument("filename", type=Path,
                        help="Path to the capture file.")
    parser.add_argument("--dataset", default="iq_samples",
                        help="Dataset name for .h5 files (default: iq_samples).")
    parser.add_argument("--sample-rate", type=float, default=None,
                        help="Sample rate in Hz for time axis / FFT.")
    parser.add_argument("--start", type=int, default=0,
                        help="Starting sample index.")
    parser.add_argument("--count", type=int, default=None,
                        help="Number of samples to plot/read.")
    parser.add_argument("--fft", action="store_true",
                        help="Also show FFT magnitude.")
    parser.add_argument("--title", default=None,
                        help="Custom title for the time-domain plot.")
    return parser.parse_args()


def main():
    args = parse_args()
    data, metadata = load_samples(args.filename, args.dataset)
    window = select_window(data, args.start, args.count)

    if args.title is None and metadata.get("timestamp"):
        title = f"{args.filename.name} @ {metadata['timestamp']}"
    else:
        title = args.title

    plot_time_domain(window, sample_rate=args.sample_rate, title=title)

    if args.fft:
        plot_fft(window, sample_rate=args.sample_rate)

    plt.show()


if __name__ == "__main__":
    main()
