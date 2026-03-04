import threading
from rfsoc_rfdc.rfdc_config import ZCU216_CONFIG
from rfsoc_rfdc.receiver.rx_analyzer.components.base_component import BaseComponent

import numpy as np


class OfdmMetricsCalculator(BaseComponent):
    """Calculator for OFDM-specific processing (assume real2iq mode)"""

    def __init__(self, channel_id, ofdm_scheme, detect_scheme):
        super().__init__(channel_id)
        self.ofdm_scheme = ofdm_scheme
        self.detect_scheme = detect_scheme

    def io_logging_thd(self, raw_iq):
        pass

    def plot_thd(self, raw_iq):
        thd = threading.Thread(
            target=self.detect_scheme.update_plot, args=(raw_iq,))
        return thd

    def analyze_packet(self, raw_iq):
        """Perform packet detection and OFDM analysis"""
        rx_packet, snr, cfo = self.detect_scheme.proc_rx(raw_iq)

        if rx_packet is None:
            return None, snr, cfo, np.nan, np.nan

        evm, ber = self.ofdm_scheme.analyze(rx_packet, self.channel_id)

        # Log results using logger from config
        logger = ZCU216_CONFIG['LOGGER']
        config_name = ZCU216_CONFIG['CONFIG_NAME']
        log_line = f"{snr:.3f}, {cfo:.3f}, {evm:.3f}, {ber:.10f}"
        logger.log_metrics(
            f"{config_name}_CH{self.channel_id}_res.log", log_line)

        return rx_packet, snr, cfo, evm, ber
