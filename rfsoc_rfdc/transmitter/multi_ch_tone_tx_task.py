from rfsoc_rfdc.overlay_task import TASK_STATE
from rfsoc_rfdc.transmitter.multi_ch_tx_task import MultiChTxTask
from rfsoc_rfdc.waveform_generator import WaveFormGenerator as wg
from rfsoc_rfdc.rfdc_config import ZCU216_CONFIG
import logging
import time
import numpy as np

from rfsoc_rfdc.multi_ch_mem_layout import MchIq2RLayout


class MultiChToneTxTask(MultiChTxTask):

    def __init__(self, overlay, mode="iq2real", channel_count=4, dp_vect_dim=1, tone_freq_mhz=100):
        super().__init__(overlay, mode, channel_count, dp_vect_dim)

        self.tone_freq_mhz = tone_freq_mhz
        self.sideband = "SSB"

        # Tone generation
        sch_data = wg.generate_tone(
            tone_freq_mhz=self.tone_freq_mhz,
            sample_rate=ZCU216_CONFIG['DACSampleRate'],
            interpolation_rate=ZCU216_CONFIG['DACInterpolationRate'],
            sideband=self.sideband,
            mode=mode
        )

        # Replicate across all channels
        mch_data_input = np.tile(sch_data, (self.channel_count, 1))
        # Generate multi-channel memory layout
        mch_data = self.mch_mem_layout.gen_layout(mch_data_input)
        # Convert to np.int16
        mch_data = mch_data.astype(np.int16)
        # Perform data copy
        self.tx_ch.data_copy(mch_data)
        logging.info(
            f"Tx tone preparation done. Freq: {self.tone_freq_mhz} MHz")

    def run(self):

        while not self._stop_event.is_set():
            if self._pause_event.is_set():
                self.tx_ch.stream(duty_cycle=100)
                time.sleep(1)
            else:
                self.tx_ch.tx_dma.stop()
                self._pause_event.wait()
        self.tx_ch.tx_dma.stop()
