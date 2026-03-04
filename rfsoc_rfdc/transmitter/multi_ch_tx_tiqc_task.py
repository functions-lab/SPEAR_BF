from rfsoc_rfdc.overlay_task import TASK_STATE

from rfsoc_rfdc.transmitter.multi_ch_tx_task import MultiChTxTask
from rfsoc_rfdc.overlay_task import TASK_STATE
import time
from rfsoc_rfdc.waveform_generator import WaveFormGenerator as wg
from scipy.io import loadmat

import numpy as np

from rfsoc_rfdc.iq_loader import IqLoader
from rfsoc_rfdc.rfdc_type import MyRFdcType
from rfsoc_rfdc.rfdc_config import ZCU216_CONFIG
import logging


class MultiChTxTIQCTask(MultiChTxTask):

    def __init__(self, overlay, mode="iq2real", channel_count=4, dp_vect_dim=1):
        super().__init__(overlay, mode, channel_count, dp_vect_dim)

    def data_preparation(self):
        if self.mode == "iq2real":
            tiqc_fname = "./rb_baseband.npy"
            try:
                waveTx = np.load(tiqc_fname)
            except:
                raise (
                    f"Failed to load TIQC waveform at {tiqc_fname}")
            logging.info(
                f"TIQC waveform loaded from {tiqc_fname} successfully.")

            waveTx = np.tile(waveTx, (self.channel_count, 1))

            # Convert to int16
            raw_max = 1.0  # Assuming waveform ranges from +1.0 to -1.0
            scaling = MyRFdcType.DAC_MAX_SCALE / raw_max

            for ch in range(self.channel_count):
                # Scale to int16
                waveTx[ch] = waveTx[ch, :] * scaling

        else:
            raise RuntimeError(f"Unrecognized mode {self.mode}")

        # Generate multi-channel memory layout
        mch_data = self.mch_mem_layout.gen_layout(waveTx)
        # Convert to np.int16
        mch_data = mch_data.astype(np.int16)
        # Perform data copy
        self.tx_ch.data_copy(mch_data)
        logging.info(f"Tx data preparation done.")

    def run(self):
        self.data_preparation()
        # MIMO Processing
        while not self._stop_event.is_set():
            if self._pause_event.is_set():
                # Streaming IQ samples
                self.tx_ch.stream(duty_cycle=100)
                time.sleep(1)
            else:
                self.tx_ch.tx_dma.stop()
                self._pause_event.wait()
