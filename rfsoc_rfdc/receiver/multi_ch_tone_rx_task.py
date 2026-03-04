from rfsoc_rfdc.receiver.multi_ch_rx_task import MultiChRxTask
from rfsoc_rfdc.receiver.rx_analyzer import Real2IqDriver, ChPowerPipeline
from rfsoc_rfdc.overlay_task import TASK_STATE
import time
import logging
import numpy as np


class MultiChToneRxTask(MultiChRxTask):
    """Multi-Channel Tone Power Measurement Task"""

    def __init__(self, overlay, mode="real2iq", channel_count=4, dp_vect_dim=1, buff_size=2**26):
        super().__init__(overlay, mode, channel_count, dp_vect_dim, buff_size=buff_size)

    def _channel_factory(self):
        super()._channel_factory()
        pipeline = ChPowerPipeline()
        self.rx_analyzers = Real2IqDriver(pipeline=pipeline, channel_id=0)

    def run(self):
        """
        Main task loop.
        For tone measurement, we usually drive this task manually via transfer()
        calls in the calibration script.
        """
        self._stop_event.wait()
