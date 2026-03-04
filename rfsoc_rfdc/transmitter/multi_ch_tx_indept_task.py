from rfsoc_rfdc.overlay_task import TASK_STATE

from rfsoc_rfdc.transmitter.multi_ch_tx_task import MultiChTxTask
from rfsoc_rfdc.overlay_task import TASK_STATE
import time
from rfsoc_rfdc.waveform_generator import WaveFormGenerator as wg
import numpy as np
from rfsoc_rfdc.transmitter.tx_data_generator import TxDataGenerator


class MultiChTxIndeptTask(MultiChTxTask):

    def __init__(self, overlay, mode="iq2real", channel_count=4, dp_vect_dim=1):
        super().__init__(overlay, mode, channel_count, dp_vect_dim)

    def run(self):
        if self.mode == "iq2real" or self.mode == "iq2iq":
            tx_data_generator = TxDataGenerator()
            sch_data = tx_data_generator.get_iq_samples()
        else:
            sch_data = wg.generate_sine_wave(repeat_time=100, sample_pts=8)
        # Replicate across all channels
        data = np.tile(sch_data, (self.channel_count, 1))
        # Generate multi-channel memory layout
        mch_data = self.mch_mem_layout.gen_layout(data)
        # Convert to np.int16
        mch_data = mch_data.astype(np.int16)
        # Perform data copy
        self.tx_ch.data_copy(mch_data)
        # Start transmission
        while not self._stop_event.is_set():
            if self._pause_event.is_set():
                # Streaming IQ samples
                self.tx_ch.stream(duty_cycle=100)
                time.sleep(1)
            else:
                self.tx_ch.tx_dma.stop()
                self._pause_event.wait()
