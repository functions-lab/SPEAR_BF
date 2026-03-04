import concurrent.futures
from rfsoc_rfdc.overlay_task import TASK_STATE
import time
import logging
from rfsoc_rfdc.rfdc_config import ZCU216_CONFIG
from rfsoc_rfdc.receiver.multi_ch_rx_task import MultiChRxTask

from rfsoc_rfdc.receiver.rx_analyzer import Real2IqDriver, FmcwPipeline
from rfsoc_rfdc.dsp.radar_detection import RadarDetection
import numpy as np


class FmcwRxTask(MultiChRxTask):
    """FMCW Radar Rx Task"""

    def __init__(self, overlay, channel_count=2, dp_vect_dim=4):
        super().__init__(overlay, "real2iq", channel_count, dp_vect_dim, buff_size=2**21)

    def _channel_factory(self):
        super()._channel_factory()

        if self.mode == "real2iq":
            # FMCW usually requires RadarDetection to get packet indices
            fs = ZCU216_CONFIG['ADCSampleRate'] / \
                ZCU216_CONFIG['ADCInterpolationRate'] * 1e6
            detect_scheme = RadarDetection(sample_rate=fs)
            pipeline = FmcwPipeline(channel_id=0, detect_scheme=detect_scheme)

            self.rx_analyzers = Real2IqDriver(pipeline=pipeline, channel_id=0)
        else:
            raise RuntimeError(f"Unrecognized mode {self.mode}")

    def run(self):
        while not self._stop_event.is_set():
            self._pause_event.wait()
            if self._stop_event.is_set():
                break

            self.rx_ch.transfer()
            self.rx_ch.transfer()  # This is necessary to cleanup samples from previous capture
            print("transfer done")

            raw_mch_data = self.rx_ch.data
            mch_complex_arr = self._layout_factory(raw_mch_data)

            # Assumed 2 RX for FMCW: Ch0 loopback, Ch1 OTA
            lpb_ch = mch_complex_arr[0]
            ota_ch = mch_complex_arr[1]

            snr, cfo = self.rx_analyzers.proc_rx(lpb_ch, ota_ch)
            logging.info(f"SNR: {snr}, CFO: {cfo}")
