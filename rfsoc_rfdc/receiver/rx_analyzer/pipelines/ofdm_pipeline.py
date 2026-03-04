import numpy as np
import logging
from rfsoc_rfdc.receiver.rx_analyzer.pipelines.base_pipeline import BasePipeline
from rfsoc_rfdc.receiver.rx_analyzer.components.time_domain_visualizer import TimeDomainVisualizer, TimeDomainPacketVisualizer
from rfsoc_rfdc.receiver.rx_analyzer.components.spectrum_visualizer import SpectrumVisualizer
from rfsoc_rfdc.receiver.rx_analyzer.components.ofdm_metrics_calculator import OfdmMetricsCalculator
from rfsoc_rfdc.rfdc_config import ZCU216_CONFIG


class OfdmPipeline(BasePipeline):
    """Pipeline for OFDM Signal Processing"""

    def __init__(self, channel_id, ofdm_scheme, detect_scheme):
        super().__init__(channel_id)
        path2wave = str(detect_scheme.logger.get_log_dir())

        self.waveform_visualizer = TimeDomainVisualizer(
            channel_id, mode="real2iq")
        # self.packet_visualizer = TimeDomainPacketVisualizer(
        #     channel_id)
        # self.spectrum_visualizer = SpectrumVisualizer(channel_id)
        self.ofdm_calculator = OfdmMetricsCalculator(channel_id,
                                                     ofdm_scheme, detect_scheme)  # Pass detect_scheme if needed by calculator

    def process(self, data, run_async_func):
        thd_list = []
        thd_list.append(self.waveform_visualizer.plot_thd(data))
        # thd_list.append(self.waveform_visualizer.io_logging_thd(data))

        # Run initial visualization threads
        run_async_func(thd_list)

        raw_iq = data

        try:
            rx_packet, snr, cfo, evm, ber = self.ofdm_calculator.analyze_packet(
                raw_iq)
        except Exception as e:
            logging.error(
                f"Rx #{self.channel_id} Failed to decode Rx packet: {e}")
            return np.nan, np.nan, np.nan, np.nan

        # # Visualization for decoded packet
        # if rx_packet is not None:
        #     thd_list = []
        #     thd_list.append(self.packet_visualizer.plot_thd(rx_packet))
        #     thd_list.append(self.packet_visualizer.io_logging_thd(rx_packet))
        #     # thd_list.append(self.spectrum_visualizer.plot_thd(rx_packet))

        #     run_async_func(thd_list)

        return snr, cfo, evm, ber

    def close(self):
        self.waveform_visualizer.close()
        # self.packet_visualizer.close()
        # self.spectrum_visualizer.close()

    def __del__(self):
        self.close()
