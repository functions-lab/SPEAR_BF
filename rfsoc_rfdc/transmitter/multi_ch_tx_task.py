from rfsoc_rfdc.overlay_task import OverlayTask, TASK_STATE
from rfsoc_rfdc.transmitter.tx_channel import TxChannel
from rfsoc_rfdc.waveform_generator import WaveFormGenerator as wg
from pynq.lib import AxiGPIO
import numpy as np
import time
import logging

from rfsoc_rfdc.transmitter.tx_data_generator import TxDataGenerator
from rfsoc_rfdc.rfdc_config import ZCU216_CONFIG
from rfsoc_rfdc.multi_ch_mem_layout import MchIq2RLayout, MchR2RLayout


class MultiChTxTask(OverlayTask):

    def __init__(self, overlay, mode, channel_count=4, dp_vect_dim=1):
        super().__init__(overlay, name="MultiChTxTask")
        self.mode = mode
        # Number of DACs controlled by a DMA
        self.channel_count = channel_count
        # IQ samples vectorization in the datapath
        self.dp_vect_dim = dp_vect_dim
        # Hardware IPs
        self.ch_dma = self.ol.dac_datapath.hw_trigger_dma
        self.ch_fifo_count_ip = AxiGPIO(
            self.ol.ip_dict['dac_datapath/fifo_count']).channel1
        self._channel_factory()
        self._layout_factory()
        # Reset DMA before proceeding
        self.ch_dma.stop()

    def _channel_factory(self):
        # Initialize Tx channels
        self.tx_ch = TxChannel(
            dma_ip=self.ch_dma,
            fifo_count_ip=self.ch_fifo_count_ip,
            target_device=self.ol.PSDDR,
            debug_mode=False
        )

    def _layout_factory(self):
        if self.mode == "iq2real" or self.mode == "iq2iq":
            self.mch_mem_layout = MchIq2RLayout(
                channel_count=self.channel_count, dp_vect_dim=self.dp_vect_dim)
        elif self.mode == "real2real":
            self.mch_mem_layout = MchR2RLayout(
                channel_count=self.channel_count, dp_vect_dim=self.dp_vect_dim)
            raise RuntimeError(f"Not supported")
        else:
            raise RuntimeError(f"Unrecognized mode {self.mode}")

    def data_preparation(self):
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
        logging.info(f"Tx data preparation done.")

    def close(self):
        """Close all resources associated with the task."""
        if hasattr(self, 'tx_ch') and self.tx_ch is not None:
            self.tx_ch.close()
            self.tx_ch = None

    def __del__(self):
        self.close()

    def run(self):
        self.data_preparation()
        # Start transmission
        while not self._stop_event.is_set():
            if self._pause_event.is_set():
                # Streaming IQ samples
                self.tx_ch.stream(duty_cycle=100)
                time.sleep(1)
            else:
                self.tx_ch.tx_dma.stop()
                self._pause_event.wait()
        self.tx_ch.tx_dma.stop()
