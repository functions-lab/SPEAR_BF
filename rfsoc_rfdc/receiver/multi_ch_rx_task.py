import concurrent.futures
from rfsoc_rfdc.overlay_task import OverlayTask, TASK_STATE
from pynq.lib import AxiGPIO
from rfsoc_rfdc.receiver.rx_channel_real2iq import RxChannelReal2Iq
from rfsoc_rfdc.receiver.rx_channel_real2real import RxChannelReal2Real
from rfsoc_rfdc.multi_ch_mem_layout import MchR2IqLayout, MchR2RLayout
import time
import logging
from rfsoc_rfdc.rfdc_config import ZCU216_CONFIG


class MultiChRxTask(OverlayTask):
    """Multi-Channel Rx Task"""

    def __init__(self, overlay, mode="real2iq", channel_count=4, dp_vect_dim=1, buff_size=2**26):
        super().__init__(overlay, name="MultiChRxTask")
        self.mode = mode
        # Number of DACs controlled by a DMA
        self.channel_count = channel_count
        # IQ samples vectorization in the datapath
        self.dp_vect_dim = dp_vect_dim
        # Receiver datapath parameters
        self.buff_size = buff_size
        # Hardware IPs
        self.ch_dma = self.ol.adc_datapath.hw_trigger_dma
        self.ch_fifo_count_ip = AxiGPIO(
            self.ol.ip_dict['adc_datapath/fifo_count']).channel1
        # Reset DMA before proceeding
        self.ch_dma.stop()
        self._channel_factory()

    def _channel_factory(self):
        if self.mode == "real2iq" or self.mode == "iq2iq":
            rx_channel = RxChannelReal2Iq(
                dma_ip=self.ch_dma,
                fifo_count_ip=self.ch_fifo_count_ip,
                target_device=self.ol.ddr4_rx,
                buff_size=self.buff_size,
                debug_mode=True
            )
            self.mch_mem_layout = MchR2IqLayout(
                channel_count=self.channel_count, dp_vect_dim=self.dp_vect_dim)

        elif self.mode == "real2real":
            rx_channel = RxChannelReal2Real(
                dma_ip=self.ch_dma,
                fifo_count_ip=self.ch_fifo_count_ip,
                target_device=self.ol.ddr4_rx,
                buff_size=self.buff_size,
                debug_mode=True
            )
            self.mch_mem_layout = MchR2RLayout(
                channel_count=self.channel_count, dp_vect_dim=self.dp_vect_dim)

        else:
            raise RuntimeError(f"Unrecognized mode {self.mode}")

        self.rx_ch = rx_channel

    def _layout_factory(self, mch_data):
        if self.mode == "real2iq" or self.mode == "iq2iq":
            mch_complex_arr = self.mch_mem_layout.dec_layout(mch_data)
            return mch_complex_arr
        elif self.mode == "real2real":
            # TODO: Implement multi-channel real2real support for this receiver
            raise RuntimeError(f"Not supported")
        else:
            raise RuntimeError(f"Unrecognized mode {self.mode}")

    def close(self):
        """Close all resources associated with the task."""
        if hasattr(self, 'rx_ch') and self.rx_ch is not None:
            self.rx_ch.close()
            self.rx_ch = None
        if hasattr(self, 'rx_analyzer') and self.rx_analyzer is not None:
            if hasattr(self.rx_analyzer, 'close'):
                self.rx_analyzer.close()
            self.rx_analyzer = None

    def __del__(self):
        self.close()

    def run(self):
        """Main task loop"""
        while not self._stop_event.is_set():
            self._pause_event.wait()
            if self._stop_event.is_set():
                break
            
            # DMA transfer
            self.rx_ch.transfer()  # Additional DMA transfer that clears out remainings in FIFO
            self.rx_ch.transfer()
            raw_mch_data = self.rx_ch.data
            mch_complex_arr = self._layout_factory(raw_mch_data)
            # Process multi-channel data here
