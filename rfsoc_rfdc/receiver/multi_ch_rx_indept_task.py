import concurrent.futures
from rfsoc_rfdc.overlay_task import TASK_STATE
import time
import logging
from rfsoc_rfdc.rfdc_config import ZCU216_CONFIG
from rfsoc_rfdc.receiver.multi_ch_rx_task import MultiChRxTask

from rfsoc_rfdc.receiver.rx_analyzer import Real2IqDriver, Real2RealDriver, OfdmPipeline, Real2RealPipeline
import numpy as np
from rfsoc_rfdc.measurement import LinkMetrics


class MultiChRxIndeptTask(MultiChRxTask):
    """Multi-Channel Rx Independent Task for OFDM"""

    def __init__(self, overlay, mode="real2iq", channel_count=4, dp_vect_dim=1):
        super().__init__(overlay, mode, channel_count, dp_vect_dim, buff_size=2**26)

    def _channel_factory(self):
        super()._channel_factory()

        if self.mode == "real2iq" or self.mode == "iq2iq":
            pipeline = OfdmPipeline(
                channel_id=0, ofdm_scheme=ZCU216_CONFIG['OFDM_SCHEME'], detect_scheme=ZCU216_CONFIG['DETECTION_SCHEME'])
            self.rx_analyzers = Real2IqDriver(pipeline=pipeline, channel_id=0)
        elif self.mode == "real2real":
            pipeline = Real2RealPipeline(channel_id=0)
            self.rx_analyzers = Real2RealDriver(
                pipeline=pipeline, channel_id=0)
        else:
            raise RuntimeError(f"Unrecognized mode {self.mode}")

    def run(self):
        AVG_COUNT = 10
        ch_count = self.channel_count

        metrics_list = [[] for _ in range(ch_count)]

        while not self._stop_event.is_set():
            self._pause_event.wait()
            if self._stop_event.is_set():
                break

            self.rx_ch.transfer()
            self.rx_ch.transfer()  # This is necessary to cleanup samples from previous capture

            raw_mch_data = self.rx_ch.data
            mch_complex_arr = self._layout_factory(raw_mch_data)

            for ch in range(ch_count):

                snr, cfo, evm, ber = self.rx_analyzers.proc_rx(
                    mch_complex_arr[ch])

                if not np.isnan(snr):

                    metrics_list[ch].append(
                        LinkMetrics(snr=snr, evm=evm, ber=ber))

                    if len(metrics_list[ch]) >= AVG_COUNT:
                        # Sort by SNR (highest first)
                        sorted_metrics = LinkMetrics.sort_by_snr(
                            metrics_list[ch])

                        # Calculate statistics
                        avg = LinkMetrics.average(sorted_metrics)
                        med = LinkMetrics.median(sorted_metrics)

                        logging.info(f"--------------------")
                        logging.info(
                            f"CH{ch}: Config: {ZCU216_CONFIG['CONFIG_NAME']}")
                        logging.info(
                            f"CH{ch}: Sorted metrics (by SNR):")
                        # for i, m in enumerate(sorted_metrics):
                        #     logging.info(f"  [{i}] {m}")
                        logging.info(
                            f"CH{ch}: Average: SNR = {avg['snr']:.2f}, EVM = {avg['evm']:.4f}, BER = {avg['ber']:.6f}")
                        logging.info(
                            f"CH{ch}: Median:  SNR = {med['snr']:.2f}, EVM = {med['evm']:.4f}, BER = {med['ber']:.6f}")

                        # Reset for next average batch
                        metrics_list[ch] = []
