import numpy as np
import logging
import threading
from tqdm import tqdm
import matplotlib.pyplot as plt
from rfsoc_rfdc.receiver.rx_analyzer.pipelines.base_pipeline import BasePipeline
from rfsoc_rfdc.dsp.fmcw import FMCW
from rfsoc_rfdc.rfdc_config import ZCU216_CONFIG


class FmcwPipeline(BasePipeline):
    """Pipeline for FMCW Radar Processing"""

    def __init__(self, channel_id, detect_scheme):
        super().__init__(channel_id)

        self.detect_scheme = detect_scheme
        self.fmcw = FMCW()
        # The packet_len for detection must match the generated FMCW waveform length
        self.detect_scheme.packet_len = self.fmcw.chirp_num * self.fmcw.duration
        self.detect_scheme.pad_len = 10000

    def process(self, lbp_ch, ota_ch, run_async_func):

        lpb_pkt, snr, cfo, start_idx, end_idx = self.detect_scheme.proc_rx(
            lbp_ch)

        if lpb_pkt is None:
            logging.error(
                "FMCW pipeline: Failed to detect packet in loopback channel.")
            return np.nan, np.nan

        ota_pkt = ota_ch[start_idx:end_idx]

        # Ensure sliced packet has the expected length
        if len(ota_pkt) != len(lpb_pkt):
            logging.warning(
                f"OTA packet length ({len(ota_pkt)}) does not match loopback packet length ({len(lpb_pkt)}).")
            # Truncate or pad as necessary, here we truncate the longer one
            min_len = min(len(ota_pkt), len(lpb_pkt))
            ota_pkt = ota_pkt[:min_len]
            lpb_pkt = lpb_pkt[:min_len]

        sample_rate = ZCU216_CONFIG['ADCSampleRate'] / \
            ZCU216_CONFIG['ADCInterpolationRate'] * 1e6
        delay_axis, chirp_mat = self.fmcw.analyze_digital(
            lpb_pkt, ota_pkt, sample_rate=sample_rate)

        # Plotting results, following fmcw.py example
        # Define limits for plots, e.g. 2x the chirp duration
        limit_time = (self.fmcw.duration / sample_rate) * 2
        limit_idx = np.searchsorted(delay_axis, limit_time)
        limit_samples = int(limit_time * sample_rate)

        logger = self.detect_scheme.logger
        config_name = ZCU216_CONFIG['CONFIG_NAME']

        # Plot signals
        fig, ax = plt.subplots()
        ax.plot(np.arange(len(lpb_pkt))[:limit_samples], np.real(
            lpb_pkt)[:limit_samples], label='Loopback Packet')
        ax.plot(np.arange(len(ota_pkt))[:limit_samples], np.real(
            ota_pkt)[:limit_samples], label='OTA Packet')
        ax.plot(np.arange(len(ota_pkt))[:limit_samples], np.real(
            ota_pkt * np.conj(lpb_pkt))[:limit_samples], label='Mixed')
        ax.legend()
        ax.set_xlabel('Time (samples)')
        ax.set_ylabel('Amplitude')
        fig.savefig(logger.get_file_path(f'{config_name}_fmcw_wave.png'))
        path = logger.get_file_path(f'{config_name}_fmcw_wave.png')
        print(f"saved to {path}")
        plt.close(fig)

        # Plot single chirp response
        fig, ax = plt.subplots()
        ax.plot(delay_axis[:limit_idx], 20 *
                np.log10(chirp_mat[0, :limit_idx] + 1e-9))
        ax.set_xlabel('Delay (s)')
        ax.set_ylabel('Magnitude (dB)')
        fig.savefig(logger.get_file_path(
            f'{config_name}_fmcw_single_chirp.png'))
        plt.close(fig)

        # Plot range map
        fig, ax = plt.subplots()
        im = ax.imshow(20 * np.log10(chirp_mat[:, :limit_idx] + 1e-9), aspect='auto', cmap='viridis',
                       extent=[0, delay_axis[limit_idx - 1], chirp_mat.shape[0], 0])
        fig.colorbar(im, ax=ax, label='Magnitude (dB)')
        ax.set_title('Range Map')
        ax.set_xlabel('Delay (s)')
        ax.set_ylabel('Chirp Number')
        fig.savefig(logger.get_file_path(f'{config_name}_fmcw_range_map.png'))
        plt.close(fig)

        return snr, cfo

    def close(self):
        # In case any visualizers are added back or other resources need closing
        pass

    def __del__(self):
        self.close()
