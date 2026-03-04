from rfsoc_rfdc.overlay_task import OverlayTask, TASK_STATE
from pynq.lib import AxiGPIO
from rfsoc_rfdc.transmitter.tx_channel_iq2real import TxChannelIq2Real
from rfsoc_rfdc.transmitter.tx_channel_real2real import TxChannelReal2Real
from rfsoc_rfdc.transmitter.tx_data_generator import TxDataGenerator

from rfsoc_rfdc.waveform_generator import WaveFormGenerator as wg
from rfsoc_rfdc.rfdc_config import ZCU216_CONFIG
import time


class SingleChTxTask(OverlayTask):
    """Single-Channel Tx Task"""

    def __init__(self, overlay, mode="iq2real", waveform_type='OFDM'):
        super().__init__(overlay, name="SingleChTxTask")
        # Hardware IPs
        self.dma_ip = self.ol.dac_datapath.hw_trigger_dma
        self.fifo_count_ip = AxiGPIO(
            self.ol.ip_dict['dac_datapath/fifo_count']).channel1
        # Initialize Tx channels
        self.mode = mode
        self.waveform_type = waveform_type
        self._channel_factory()
        self._layout_factory()
        # Reset DMA before proceeding
        self.dma_ip.stop()

    def _channel_factory(self):
        if self.mode == "iq2real" or self.mode == "iq2iq":
            tx_channel = TxChannelIq2Real(
                dma_ip=self.dma_ip,
                fifo_count_ip=self.fifo_count_ip,
                target_device=self.ol.PSDDR,
                debug_mode=False
            )
        elif self.mode == "real2real":
            tx_channel = TxChannelReal2Real(
                dma_ip=self.dma_ip,
                fifo_count_ip=self.fifo_count_ip,
                target_device=self.ol.PSDDR,
                debug_mode=False
            )
        else:
            raise RuntimeError(f"Unrecognized mode {self.mode}")

        self.tx_ch = tx_channel

    def _layout_factory(self):
        if self.mode == "iq2real" or self.mode == "iq2iq":
            tx_data_generator = TxDataGenerator(
                waveform_type=self.waveform_type)
            data = tx_data_generator.get_iq_samples()
            self.tx_ch.data_copy(complex_array=data)
        elif self.mode == "real2real":
            target_cw_freq_mhz = 100
            pts_per_period = int(ZCU216_CONFIG['DACSampleRate'] /
                                 ZCU216_CONFIG['DACInterpolationRate'] / target_cw_freq_mhz)
            data = wg.generate_sine_wave(repeat_time=10000, sample_pts=100)
            self.tx_ch.data_copy(real_array=data)
        else:
            raise RuntimeError(f"Unrecognized mode {self.mode}")

    def close(self):
        """Close all resources associated with the task."""
        if hasattr(self, 'tx_ch') and self.tx_ch is not None:
            self.tx_ch.close()
            self.tx_ch = None

    def __del__(self):
        self.close()

    def run(self):
        while not self._stop_event.is_set():
            if self._pause_event.is_set():
                self.tx_ch.stream(duty_cycle=100)
                time.sleep(1)
            else:
                self.tx_ch.tx_dma.stop()
                self._pause_event.wait()
        self.tx_ch.tx_dma.stop()
