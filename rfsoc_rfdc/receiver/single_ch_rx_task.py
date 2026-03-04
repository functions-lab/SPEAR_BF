from rfsoc_rfdc.overlay_task import OverlayTask, TASK_STATE

from rfsoc_rfdc.receiver.rx_channel_real2iq import RxChannelReal2Iq
from rfsoc_rfdc.receiver.rx_channel_real2real import RxChannelReal2Real
from rfsoc_rfdc.receiver.rx_analyzer import Real2IqDriver, Real2RealDriver, OfdmPipeline, Real2RealPipeline
from rfsoc_rfdc.rfdc_config import ZCU216_CONFIG
from rfsoc_rfdc.measurement import LinkMetrics
from pynq.lib import AxiGPIO
import time
import numpy as np
import logging


class SingleChRxTask(OverlayTask):
    """Single-Channel ADC Task"""

    def __init__(self, overlay, mode="real2iq", buff_size=2**26):
        """Initialize SingleChRxTask"""
        super().__init__(overlay, name="SingleChRxTask")

        self.logger = logging.getLogger(self.__class__.__name__)

        self.mode = mode
        # Receiver datapath parameters
        self.buff_size = buff_size
        # Hardware IPs
        self.dma_ip = self.ol.adc_datapath.hw_trigger_dma
        self.fifo_count_ip = AxiGPIO(
            self.ol.ip_dict['adc_datapath/fifo_count']).channel1
        # Initialize Rx channel
        self._receiver_factory(mode)
        # Reset DMA before proceeding
        self.dma_ip.stop()

    def _receiver_factory(self, mode):
        """Create appropriate channel object based on mode"""
        if mode == "real2iq":
            rx_channel = RxChannelReal2Iq(
                dma_ip=self.dma_ip,
                fifo_count_ip=self.fifo_count_ip,
                target_device=self.ol.ddr4_rx,
                buff_size=self.buff_size,
                debug_mode=True
            )

            pipeline = OfdmPipeline(
                channel_id=0, ofdm_scheme=ZCU216_CONFIG['OFDM_SCHEME'], detect_scheme=ZCU216_CONFIG['DETECTION_SCHEME'])

            rx_analyzer = Real2IqDriver(
                pipeline=pipeline, channel_id=0)
        elif mode == "real2real":
            rx_channel = RxChannelReal2Real(
                dma_ip=self.dma_ip,
                fifo_count_ip=self.fifo_count_ip,
                target_device=self.ol.ddr4_rx,
                buff_size=self.buff_size,
                debug_mode=False
            )
            real2real_pipeline = Real2RealPipeline(channel_id=0)
            rx_analyzer = Real2RealDriver(
                pipeline=real2real_pipeline, channel_id=0)
        else:
            raise RuntimeError(
                f"Unrecognized mode: {mode}")

        self.rx_ch = rx_channel
        self.rx_analyzer = rx_analyzer

    def close(self):
        """Close all resources associated with the task."""
        if hasattr(self, 'rx_ch') and self.rx_ch is not None:
            self.rx_ch.close()
            self.rx_ch = None
        if hasattr(self, 'rx_analyzer') and self.rx_analyzer is not None:
            if hasattr(self.rx_analyzer, 'close'):
                self.rx_analyzer.close()
            # Set to None to indicate it's closed
            self.rx_analyzer = None
        self.logger.info("SingleChRxTask closed.")

    def __del__(self):
        self.close()

    def run(self):
        """Main task loop with EVM/BER averaging across multiple frames"""
        AVG_COUNT = 5
        metrics_list = []

        while not self._stop_event.is_set():
            if self._pause_event.is_set():
                self.rx_ch.transfer()
                self.rx_ch.transfer()  # This is necessary to cleanup samples from previous capture
                wave_rx = self.rx_ch.data
                self.logger.info(f"Start processing RX data...")

                snr, cfo, evm, ber = self.rx_analyzer.proc_rx(wave_rx)
                self.logger.info(
                    f"SNR = {snr:.2f}, EVM = {evm:.4f}, BER = {ber:.6f}")

                if not np.isnan(snr):
                    metrics_list.append(LinkMetrics(
                        snr=snr, evm=evm, ber=ber))

                    if len(metrics_list) >= AVG_COUNT:
                        # Sort by SNR (highest first)
                        sorted_metrics = LinkMetrics.sort_by_snr(
                            metrics_list)

                        # Calculate statistics
                        avg = LinkMetrics.average(sorted_metrics)
                        med = LinkMetrics.median(sorted_metrics)
                        best = LinkMetrics.best(sorted_metrics)

                        self.logger.info(f"--------------------")
                        self.logger.info(
                            f"Config: {ZCU216_CONFIG['CONFIG_NAME']}")
                        self.logger.info(f"Sorted metrics (by SNR):")
                        for i, m in enumerate(sorted_metrics):
                            self.logger.info(f"  [{i}] {m}")
                        self.logger.info(
                            f"Median:  SNR = {med['snr']:.2f}, EVM = {med['evm']:.4f}, BER = {med['ber']:.6f}")
                        self.logger.info(
                            f"Average: SNR = {avg['snr']:.2f}, EVM = {avg['evm']:.4f}, BER = {avg['ber']:.6f}")
                        self.logger.info(
                            f"Best   : SNR = {best['snr']:.2f}, EVM = {best['evm']:.4f}, BER = {best['ber']:.6f}")

                        metrics_list = []
                        self._stop_event.set()
                        self.task_state = TASK_STATE["STOP"]
            else:
                metrics_list = []
                self._pause_event.wait()
