from rfsoc_rfdc.receiver.single_ch_rx_task import SingleChRxTask
from rfsoc_rfdc.receiver.rx_channel_real2iq import RxChannelReal2Iq
from rfsoc_rfdc.receiver.rx_analyzer import Real2IqDriver, ChPowerPipeline
from rfsoc_rfdc.overlay_task import TASK_STATE
import time
import logging


class SingleChToneRxTask(SingleChRxTask):
    """Single-Channel Tone Power Measurement Task"""

    def __init__(self, overlay, buff_size=2**14):
        """Initialize SingleChToneRxTask"""
        super().__init__(overlay, mode="real2iq", buff_size=buff_size)

    def _receiver_factory(self, mode):
        """Create appropriate channel object for Tone Power measurement"""
        # We override this to force ChPowerPipeline usage.
        # mode argument is passed by super().__init__ but we ignore it or assume it is real2iq.

        self.rx_ch = RxChannelReal2Iq(
            dma_ip=self.dma_ip,
            fifo_count_ip=self.fifo_count_ip,
            target_device=self.ol.ddr4_rx,
            buff_size=self.buff_size,
            debug_mode=True
        )

        pipeline = ChPowerPipeline()
        self.rx_analyzer = Real2IqDriver(
            pipeline=pipeline, channel_id=0)

    def run(self):
        """
        Main task loop.
        For tone measurement, we usually drive this task manually via transfer()
        calls in the calibration script.
        """
        self._stop_event.wait()
