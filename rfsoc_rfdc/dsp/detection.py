from rfsoc_rfdc.txt_logger import get_txt_logger
import matplotlib.pyplot as plt
import numpy as np
import os
import shutil
import logging
import argparse
import h5py
from tqdm import tqdm

# Try to import numba for acceleration
try:
    from numba import jit, prange
    NUMBA_AVAILABLE = True
except ImportError:
    NUMBA_AVAILABLE = False
    logging.warning("Numba not available. Install with: pip install numba")
    # Define dummy decorators if numba is not available

    def jit(*args, **kwargs):
        def decorator(func):
            return func
        return decorator
    prange = range

from rfsoc_rfdc.dsp.ofdm import OFDM
from rfsoc_rfdc.rfdc_config import ZCU216_CONFIG


@jit(nopython=True, parallel=True, fastmath=True, cache=True)
def _compute_correlation_numba(wave, win_len, delta_len, num_positions):
    """
    Numba-accelerated parallel correlation computation.
    Uses prange for automatic parallelization across all available cores.
    """
    corr_all = np.zeros(num_positions)

    # Parallel loop - each iteration is independent
    for pos in prange(num_positions):
        # Extract windows for this position
        window1 = wave[pos:pos + win_len]
        window2 = wave[pos + delta_len:pos + delta_len + win_len]

        # Compute statistics
        product = np.sum(window1 * np.conj(window2))
        sum1 = np.sum(window1)
        sum2 = np.sum(window2)
        energy1 = np.sum(np.abs(window1)**2)
        energy2 = np.sum(np.abs(window2)**2)

        # Normalize correlation
        mean_product = sum1 * np.conj(sum2) / win_len
        var1 = energy1 - np.abs(sum1)**2 / win_len
        var2 = energy2 - np.abs(sum2)**2 / win_len
        denominator = np.sqrt(var1 * var2)

        if denominator < 1e-10:
            corr_all[pos] = 0.0
        else:
            corr_all[pos] = np.abs(product - mean_product) / denominator

    return corr_all


class Detection:

    def __init__(self, sample_rate=1e9, debug_mode=False):
        super(Detection, self).__init__()
        self.sample_rate = sample_rate
        self.debug_mode = debug_mode

        # Access the logger from global config
        self.logger = ZCU216_CONFIG['LOGGER']

        # Initialize file paths using logger
        self.txFile = self.logger.get_file_path('Tx.npy')
        self.txMatVarKey = "waveTx"
        self.rxFile = self.logger.get_file_path('Rx.npy')
        self.rxMatVarKey = "waveRx"

        # DSP-related
        self.zadoff_set = [139, 839]  # ascent

    def _check_saturation(self, packet, threshold=1):
        """Check if the packet is saturated."""
        ratio = np.sum(np.abs(packet) > threshold) / np.shape(packet)[0]
        if ratio > 0:
            logging.info(f'Warning: Packet Saturated for {ratio*100:.2f}%')

    def _zadoff_detection(self, wave, win_len, delta_len, threshold):
        """Perform Zadoff-Chu sequence detection using efficient vectorized approach."""
        wave_len = len(wave)

        # Check if waveform is long enough
        if wave_len < delta_len + win_len:
            raise ValueError(f"Waveform too short for detection: "
                             f"got {wave_len} samples, need at least {delta_len + win_len}")

        # Compute correlation using vectorized sliding window
        num_positions = wave_len - delta_len - win_len + 1
        corr_all = self._compute_sliding_correlation(
            wave, win_len, delta_len, num_positions)

        # Print statistics
        if self.debug_mode:
            logging.info(f"Correlation stats:")
            logging.info(
                f"  Min: {np.min(corr_all):.4f}, Max: {np.max(corr_all):.4f}")
            logging.info(
                f"  Mean: {np.mean(corr_all):.4f}, Median: {np.median(corr_all):.4f}")
            logging.info(
                f"  Values above threshold ({threshold}): {np.sum(corr_all > threshold)}")

        # Find peaks
        offset_list, corr_list = self._find_peaks(
            corr_all, threshold, neighbor=10)

        if self.debug_mode:
            # Plot correlation
            self._plot_correlation(corr_all, threshold)
            logging.info(
                f"  Found {len(offset_list)} peaks above threshold {threshold}")
            if offset_list:
                logging.info(f"  Peak offsets: {offset_list[:10]}...")
                logging.info(
                    f"  Peak correlations: {[f'{c:.3f}' for c in corr_list[:10]]}...")

        return offset_list, corr_list

    def _compute_sliding_correlation(self, wave, win_len, delta_len, num_positions):
        """Compute normalized correlation for all window positions using Numba-accelerated parallel processing."""
        if self.debug_mode:
            accel_type = "Numba (parallel)" if NUMBA_AVAILABLE else "Python (no acceleration)"
            logging.info(
                f"Computing correlation for {num_positions} positions using {accel_type}")

        # Call the JIT-compiled parallel function with progress indicator
        with tqdm(total=num_positions, desc="Computing correlations", unit="pos", leave=False) as pbar:
            corr_all = _compute_correlation_numba(
                wave, win_len, delta_len, num_positions)
            pbar.update(num_positions)  # Update to completion

        return corr_all

    def _normalize_correlation(self, product, sum1, sum2, energy1, energy2, win_len):
        """Compute normalized correlation coefficient."""
        mean_product = sum1 * np.conj(sum2) / win_len
        var1 = energy1 - np.abs(sum1)**2 / win_len
        var2 = energy2 - np.abs(sum2)**2 / win_len

        # Avoid division by zero
        denominator = np.sqrt(var1 * var2)
        if denominator < 1e-10:
            return 0.0

        return np.abs(product - mean_product) / denominator

    def _find_peaks(self, corr_all, threshold, neighbor=10):
        """Find local maxima above threshold."""
        offset_list = []
        corr_list = []
        corr_len = len(corr_all)

        for offset in range(corr_len):
            corr = corr_all[offset]

            # Skip if below threshold
            if corr <= threshold:
                continue

            # Check if local maximum
            start = max(0, offset - neighbor)
            end = min(corr_len, offset + neighbor + 1)

            # Must be strictly greater than all neighbors
            is_peak = True
            if start < offset and corr <= np.max(corr_all[start:offset]):
                is_peak = False
            if end > offset + 1 and corr < np.max(corr_all[offset + 1:end]):
                is_peak = False

            if is_peak:
                offset_list.append(offset)
                corr_list.append(corr)

        return offset_list, corr_list

    def _plot_correlation(self, corr_all, threshold):
        """Plot correlation values."""
        plt.figure(figsize=(12, 4))
        plt.plot(corr_all, linewidth=0.5)
        plt.axhline(y=threshold, color='r', linestyle='--',
                    linewidth=2, label=f'Threshold={threshold}')
        plt.title(f"Zadoff-Chu Correlation")
        plt.xlabel("Offset (samples)")
        plt.ylabel("Normalized Correlation")
        plt.legend()
        plt.grid(True, alpha=0.3)
        plt.tight_layout()

        filename = f"correlation_plot.png"
        file_path = self.logger.get_file_path(filename)
        plt.savefig(file_path, dpi=150)
        plt.show()
        plt.close()

        logging.info(f"Saved correlation plot to {file_path}")

    def _get_energy(self, wave):
        """Calculate the energy of the wave."""
        wave_cal = wave  # - np.mean(wave)
        energy = np.mean(np.abs(wave_cal)**2)
        return energy

    def proc_tx(self, packet_tx):
        """Pad preamble to Tx packet"""
        self._check_saturation(packet_tx)
        self.packet_len = np.shape(packet_tx)[0]
        # int(max(1e-3*self.sample_rate, round(0.1*self.packet_len)))
        self.pad_len = 10000

        head_tx = np.zeros((sum(self.zadoff_set) * 3), dtype=np.complex64)
        offset = 0
        for zadoff_len in self.zadoff_set:
            zadoff_single = np.exp(
                1j * 2 * np.pi * np.random.rand(1, zadoff_len))
            zadoff_double = np.tile(zadoff_single, 2)
            head_tx[offset:offset + 2 * zadoff_len] = zadoff_double
            offset += 3 * zadoff_len
        pad_tx = np.zeros((self.pad_len))
        wave_tx = np.concatenate((pad_tx, head_tx, packet_tx, pad_tx), axis=0)

        return wave_tx

    def proc_rx(self, wave_rx):
        """Detect preamble received packet"""
        cap_num = 3
        noise_num = 1000
        head_len = sum(self.zadoff_set) * 3
        wave_len = 2 * self.pad_len + head_len + self.packet_len

        # Extract the last portion of the waveform for detection
        # Use cap_num windows to search for repeating patterns
        search_len = min(len(wave_rx), cap_num * wave_len)
        wave_rx_search = wave_rx[-search_len:]

        if self.debug_mode:
            # Visualize the search window
            plt.figure(figsize=(14, 5))
            time_axis = np.arange(len(wave_rx_search))
            plt.subplot(2, 1, 1)
            plt.plot(time_axis, np.real(wave_rx_search),
                     label='I (Real)', alpha=0.7)
            plt.plot(time_axis, np.imag(wave_rx_search),
                     label='Q (Imaginary)', alpha=0.7)
            plt.xlabel('Sample Index')
            plt.ylabel('ADC Reading')
            plt.title(
                f'Search Window - Time Domain (I/Q components, {len(wave_rx_search)} samples)')
            plt.legend()
            plt.grid(True, alpha=0.3)

            plt.subplot(2, 1, 2)
            magnitude_db = 20 * np.log10(np.abs(wave_rx_search) + 1e-10)
            plt.plot(time_axis, magnitude_db)
            plt.xlabel('Sample Index')
            plt.ylabel('Magnitude (dB)')
            plt.title('Search Window - Magnitude')
            plt.grid(True, alpha=0.3)
            plt.ylim(bottom=0, top=100)

            plt.tight_layout()
            search_window_file = 'search_window_visualization.png'
            file_path = self.logger.get_file_path(search_window_file)
            plt.savefig(file_path)
            plt.show()
            plt.close()
            logging.info(f"Saved correlation plot to {file_path}")

        offset_list, corr_list = self._zadoff_detection(
            wave_rx_search, self.zadoff_set[-1], self.zadoff_set[-1], 0.7)

        if not offset_list:
            logging.error("Failed to detect peaks in waveform")
            return None, np.nan, np.nan

        # Use the strongest peak
        offset_idx = np.argmax(np.array(corr_list))
        detected_offset = offset_list[offset_idx]

        if self.debug_mode:
            logging.info(
                f"  Strongest peak found at offset {detected_offset} with correlation {corr_list[offset_idx]:.4f}")

        offset_zadoff = detected_offset - 3 * sum(self.zadoff_set[:-1])
        offset_packet = offset_zadoff + head_len

        if offset_zadoff < 0:
            logging.warning(f"Calculated preamble start is negative ({offset_zadoff}). "
                            f"Preamble may be truncated or detection is incorrect.")
            logging.info(f"Using detected offset directly: {detected_offset}")
            offset_zadoff = detected_offset
            offset_packet = offset_zadoff + head_len

        if self.debug_mode:
            logging.info(f"  Preamble starts at offset {offset_zadoff}")
            logging.info(f"  Packet data starts at offset {offset_packet}")

        cfo_set = []
        offset = offset_zadoff

        # Ensure we have enough samples for CFO calculation
        if offset_packet + self.packet_len > len(wave_rx_search):
            logging.error(f"Packet extends beyond search window: "
                          f"packet ends at {offset_packet + self.packet_len}, "
                          f"but search window is only {len(wave_rx_search)} samples")
            return None, np.nan, np.nan

        for idx, zadoff_len in enumerate(self.zadoff_set):
            # Check bounds
            if offset + 2 * zadoff_len > len(wave_rx_search):
                if self.debug_mode:
                    logging.info(
                        f"Warning: Not enough samples for Zadoff sequence {idx+1} CFO calculation")
                break

            zadoff_1 = wave_rx_search[offset:offset + zadoff_len]
            zadoff_2 = wave_rx_search[offset +
                                      zadoff_len:offset + 2 * zadoff_len]

            cfo_temp = (-self.sample_rate / zadoff_len *
                        np.angle(np.sum(zadoff_1 * np.conj(zadoff_2))) / 2 / np.pi)
            cfo_set.append(cfo_temp)

            # Apply CFO correction to this section of the preamble
            section_len = 3 * zadoff_len
            if offset + section_len <= len(wave_rx_search):
                wave_rx_search[offset:offset + section_len] = (
                    wave_rx_search[offset:offset + section_len] *
                    np.exp(-1j * 2 * np.pi * np.arange(section_len) /
                           self.sample_rate * cfo_temp)
                )

            offset += 3 * zadoff_len

            if self.debug_mode:
                logging.info(
                    f"Zadoff sequence {idx+1}/{len(self.zadoff_set)}: CFO = {cfo_temp:.2f} Hz")

        cfo = 0  # This line turn off CFO
        # cfo = sum(cfo_set)

        # Extract the packet from the search window
        packet_rx = wave_rx_search[offset_packet:offset_packet +
                                   self.packet_len]

        # Apply additional CFO correction to the packet if needed
        packet_rx = packet_rx * \
            np.exp(-1j * 2 * np.pi * np.arange(self.packet_len) /
                   self.sample_rate * cfo)

        noise_list = []
        iterator = range(noise_num)
        iterator = tqdm(
            iterator, desc="Computing noise samples", unit="samples", leave=False)

        for noise_idx in iterator:
            start_idx = round(len(wave_rx_search) / noise_num * noise_idx)
            end_idx = round(len(wave_rx_search) / noise_num *
                            noise_idx) + int(np.ceil(100))
            if end_idx > len(wave_rx_search):
                continue
            noise_sym = wave_rx_search[start_idx:end_idx]
            noise = self._get_energy(noise_sym)
            noise_list.append(noise)

        noise = np.percentile(noise_list, 10)
        signal = self._get_energy(packet_rx) - noise
        snr = 10 * np.log10(signal / noise)

        logging.info(
            f"SNR: {snr:.2f} dB, Signal: {10*np.log10(signal):.2f} dB, Noise: {10*np.log10(noise):.2f} dB")

        plt.ioff()
        fig, ax = plt.subplots(figsize=(12, 6))
        ax.plot(np.arange(len(wave_rx_search)), 20 *
                np.log10(np.abs(wave_rx_search) + 1e-10))
        ax.axvline(offset_zadoff, color='g', linestyle='--', linewidth=2,
                   label=f'Preamble start (offset={offset_zadoff})')
        ax.axvline(offset_packet, color='b', linestyle='--', linewidth=2,
                   label=f'Packet start (offset={offset_packet})')
        ax.axvline(offset_packet + self.packet_len, color='r', linestyle='--', linewidth=2,
                   label=f'Packet end (offset={offset_packet + self.packet_len})')
        ax.set_ylim(bottom=0, top=100)
        ax.set_xlabel('Sample Index')
        ax.set_ylabel('Magnitude (dB)')
        ax.set_title(
            f'SNR: {snr:.2f}dB Signal: {10*np.log10(signal):.2f} Noise: {10*np.log10(noise):.2f} CFO:{cfo:.2f}Hz')
        ax.legend()
        ax.grid(True)

        detection_file = self.logger.get_file_path(
            ZCU216_CONFIG['CONFIG_NAME']+'_detection.png')
        fig.savefig(detection_file)
        plt.close()
        if self.debug_mode:
            logging.info(f"  SNR plot saved to {detection_file}")

        # Store internal attributes for child classes to access
        self._last_offset_packet = offset_packet
        self._last_search_len = search_len

        return packet_rx, snr, cfo


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='OFDM Detection Algorithm')
    parser.add_argument('--mode', type=str, default='simulate',
                        choices=['simulate', 'h5file'],
                        help='Mode: simulate (generate test waveform) or h5file (load from h5 file)')
    parser.add_argument('--h5_file', type=str, default=None,
                        help='Path to h5 file containing waveform data')
    parser.add_argument('--h5_dataset', type=str, default='iq_samples',
                        help='Dataset name in h5 file (default: iq_samples)')
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO,
                        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

    np.random.seed(0)

    ofdm = OFDM(sym_num=100, fft_size=64, sub_num=48,
                modu='16QAM', cp_rate=0.125)
    packet_tx = ofdm.generate()

    det = Detection(sample_rate=2.5e9, debug_mode=False)

    wave_tx = det.proc_tx(packet_tx)

    if args.mode == 'simulate':

        logging.info("Running in simulation mode...")
        det.txFile = det.logger.get_file_path('Tx.npy')
        det.rxFile = det.logger.get_file_path('Tx.npy')

        noise = 0.001 * \
            (np.random.randn(wave_tx.shape[0]) +
             1j * np.random.randn(wave_tx.shape[0]))
        wave_tx = wave_tx + noise

        for i in range(4):
            wave_tx = np.append(wave_tx, wave_tx)

        np.save(det.txFile, wave_tx)
        wave_rx = np.load(det.rxFile)

    elif args.mode == 'h5file':
        # Load from h5 file for debugging
        if args.h5_file is None:
            raise ValueError(
                "--h5_file argument is required when mode is 'h5file'")

        if not os.path.exists(args.h5_file):
            raise FileNotFoundError(f"H5 file not found: {args.h5_file}")

        logging.info(f"Loading waveform from h5 file: {args.h5_file}")

        with h5py.File(args.h5_file, 'r') as f:
            if args.h5_dataset not in f:
                logging.info(
                    f"Available datasets in h5 file: {list(f.keys())}")
                raise KeyError(
                    f"Dataset '{args.h5_dataset}' not found in h5 file")

            wave_rx = f[args.h5_dataset][:]

            logging.info(f"Loaded waveform shape: {wave_rx.shape}")

            # Convert to complex if needed
            if not np.iscomplexobj(wave_rx):
                if wave_rx.shape[-1] == 2:
                    # Assume last dimension is [I, Q]
                    wave_rx = wave_rx[..., 0] + 1j * wave_rx[..., 1]
                    logging.info(
                        "Converted real array with I/Q components to complex")
                else:
                    logging.info(
                        "Warning: Waveform is not complex and doesn't have I/Q structure")

    packet_rx, snr, cfo = det.proc_rx(wave_rx)

    evm, ber = ofdm.analyze(packet_rx)

    logging.info(
        f"SNR: {snr:.5f} dB, CFO: {cfo:.5f} Hz, EVM: {evm:.5f}, BER: {ber:.5f}")
    logging.info('Done!')
