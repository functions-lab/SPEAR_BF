import concurrent.futures
from rfsoc_rfdc.overlay_task import TASK_STATE
import time
import logging
from rfsoc_rfdc.rfdc_config import ZCU216_CONFIG
from rfsoc_rfdc.receiver.multi_ch_rx_task import MultiChRxTask
import numpy as np
from rfsoc_rfdc.receiver.rx_analyzer import Real2IqDriver, MimoPipeline
from scipy.io import loadmat, savemat
from rfsoc_rfdc.measurement import LinkMetrics


class MultiChRxMIMOTask(MultiChRxTask):
    """Multi-Channel Rx MIMO Task"""

    def __init__(self, overlay, mode="real2iq", channel_count=4, dp_vect_dim=1):
        super().__init__(overlay, mode, channel_count, dp_vect_dim)
        self.mimo_pipeline = MimoPipeline(
            detection_scheme=ZCU216_CONFIG["DETECTION_SCHEME"],
            rx_ant_count=channel_count)
        self.rx_analyzer = Real2IqDriver(pipeline=self.mimo_pipeline)

    def run(self):
        """Main task loop"""
        PKT_COUNT = 5
        captured_pkts = 0
        base_config_name = ZCU216_CONFIG["CONFIG_NAME"]
        metrics_list = [[] for _ in range(self.channel_count)]

        while not self._stop_event.is_set():
            if self._pause_event.is_set():
                # DMA transfer
                self.rx_ch.transfer()
                self.rx_ch.transfer()  # This is necessary to cleanup samples from previous capture

                # Extract data from multiple channels
                raw_mch_data = self.rx_ch.data
                mch_complex_arr = self._layout_factory(raw_mch_data)

                # Update config name for this packet to ensure unique log files
                ZCU216_CONFIG["CONFIG_NAME"] = f"{base_config_name}_PKT_{captured_pkts}"

                logging.info(
                    f"Start processing RX data (Packet {captured_pkts})...")
                rx_packet_list, snr_list, cfo_list = self.rx_analyzer.proc_rx(
                    mch_complex_arr)

                if np.isnan(snr_list).any():
                    logging.warning(f"Rx detection failed.")
                    continue

                for ch in range(self.channel_count):
                    # We are also only storing SNR, not CFO within LinkMetrics for now.
                    metrics_list[ch].append(LinkMetrics(
                        snr=snr_list[ch], evm=np.nan, ber=np.nan))

                waveFile = "./" + \
                    ZCU216_CONFIG["CONFIG_NAME"] + ".mat"
                waveKey = self.mimo_pipeline.mimo_detection.rxMatVarKey
                savemat(waveFile, {waveKey: rx_packet_list.T})

                captured_pkts += 1

                if captured_pkts >= PKT_COUNT:
                    for ch in range(self.channel_count):
                        # Sort by SNR (highest first)
                        sorted_metrics = LinkMetrics.sort_by_snr(
                            metrics_list[ch])

                        # Calculate statistics
                        avg = LinkMetrics.average(sorted_metrics)
                        med = LinkMetrics.median(sorted_metrics)

                        logging.info(f"--------------------")
                        logging.info(
                            f"CH{ch}: Config: {base_config_name}")
                        logging.info(f"CH{ch}: Sorted metrics (by SNR):")
                        for i, m in enumerate(sorted_metrics):
                            logging.info(
                                f"  [{i}] SNR = {m.snr:.2f}dB, CFO = {cfo_list[ch]:.2f}Hz")
                        # logging.info(
                        #     f"CH{ch}: Average: SNR = {avg['snr']:.2f}dB")
                        # logging.info(
                        #     f"CH{ch}: Median:  SNR = {med['snr']:.2f}dB")

                        metrics_list[ch] = []  # Reset for next average batch

                    self._stop_event.set()
                    self.task_state = TASK_STATE["STOP"]
                    # Restore base name
                    ZCU216_CONFIG["CONFIG_NAME"] = base_config_name
            else:
                # Clear metrics if task is stopped or paused
                for ch in range(self.channel_count):
                    metrics_list[ch] = []
                self._pause_event.wait()
