from rfsoc_rfdc.overlay_task import TASK_STATE

from rfsoc_rfdc.transmitter.multi_ch_tx_task import MultiChTxTask
from rfsoc_rfdc.overlay_task import TASK_STATE
import time
from rfsoc_rfdc.waveform_generator import WaveFormGenerator as wg
from scipy.io import loadmat

import numpy as np
from rfsoc_rfdc.transmitter.tx_data_generator import TxDataGenerator

from rfsoc_rfdc.iq_loader import IqLoader
from rfsoc_rfdc.rfdc_type import MyRFdcType
from rfsoc_rfdc.rfdc_config import ZCU216_CONFIG
from rfsoc_rfdc.dsp.unit_convt import dB2Amp
import logging


class MultiChTxMIMOTask(MultiChTxTask):

    def __init__(self, overlay, mode="iq2real", channel_count=4, dp_vect_dim=1):
        super().__init__(overlay, mode, channel_count, dp_vect_dim)

    def data_preparation(self):
        if self.mode == "iq2real" or self.mode == "iq2iq":
            detection_scheme = ZCU216_CONFIG["DETECTION_SCHEME"]
            try:
                fname = f"./CHARM_OTA_{detection_scheme.tx_num}T{detection_scheme.rx_num}R_MCS_{detection_scheme.MCS}.mat"
                packetTx = loadmat(fname)[
                    detection_scheme.txMatVarKey].T
            except:
                raise FileNotFoundError(
                    f"Failed to load Tx waveform from {fname}")
            logging.info(
                f"Tx waveform {fname} loaded successfully.")

            # OFDM symbol attenuation
            db2amp = 0.5 * dB2Amp(ZCU216_CONFIG["OFDM_ATTEN_DB"])
            for ch in range(self.channel_count):
                # Scale to int16
                packetTx[ch] = packetTx[ch, :] / \
                    np.std(packetTx[ch, :]) * db2amp

            # Add preamble
            waveTx = detection_scheme.proc_tx(packetTx)

            # Convert to int16
            real_max, imag_max = np.max(
                np.abs(np.real(waveTx))), np.max(np.abs(np.imag(waveTx)))
            raw_max = max(real_max, imag_max)
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
