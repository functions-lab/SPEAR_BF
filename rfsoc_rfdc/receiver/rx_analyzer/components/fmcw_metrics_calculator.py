import threading
from rfsoc_rfdc.rfdc_config import ZCU216_CONFIG
from rfsoc_rfdc.receiver.rx_analyzer.components.base_component import BaseComponent
import matplotlib.pyplot as plt
import numpy as np


class FmcwMetricsCalculator(BaseComponent):
    """Calculator for FMCW-specific processing (assume real2iq mode)"""

    def __init__(self, channel_id, fmcw_scheme):
        super().__init__(channel_id)
        self.fmcw_scheme = fmcw_scheme

    def io_logging_thd(self, raw_iq):
        pass

    def plot_thd(self, raw_iq):
        thd = threading.Thread(
            target=self.detect_scheme.update_plot, args=(raw_iq,))
        return thd

    def analyze_packet(self, rx_packet_ref, rx_packet_air):
        """Perform FMCW analysis"""
        adc_iq_samp_rate = ZCU216_CONFIG['ADCSampleRate'] / \
            ZCU216_CONFIG['ADCInterpolationRate']
        config_name = ZCU216_CONFIG['CONFIG_NAME']

        delay_axis, chirp_mat = self.fmcw_scheme.analyze_digital(
            rx_packet_ref, rx_packet_air, sample_rate=adc_iq_samp_rate)

        # Plot single chirp response
        fig, ax = plt.subplots()
        ax.plot(delay_axis, 20 * np.log10(chirp_mat[0, :]))
        ax.set_xlabel('Delay (s)')
        ax.set_ylabel('Magnitude (dB)')
        fig.savefig(
            f"{self.detect_scheme.path2wave}/{config_name}_FMCW_chirp_response.png")
        plt.close(fig)

        # Plot range map
        fig, ax = plt.subplots()
        ax.imshow(chirp_mat, aspect='auto')
        ax.set_title('Range Map')
        ax.set_xlabel('Delay (samples)')
        ax.set_ylabel('Chirp Number')
        fig.savefig(
            f"{self.detect_scheme.path2wave}/{config_name}_FMCW_range_map.png")
        plt.close(fig)
