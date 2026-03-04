import numpy as np
from rfsoc_rfdc.iq_loader import MatlabIqLoader, NumpyIqLoader

import logging

from rfsoc_rfdc.dsp.ofdm import OFDM
from rfsoc_rfdc.dsp.fmcw import FMCW
from rfsoc_rfdc.dsp.detection import Detection
from rfsoc_rfdc.rfdc_config import ZCU216_CONFIG
from rfsoc_rfdc.dsp.unit_convt import dB2Amp


class TxDataGenerator:
    def __init__(self, tx_file=None, waveform_type='OFDM'):
        self.tx_file = tx_file
        self.waveform_type = waveform_type

    def get_iq_samples(self):
        if self.tx_file is not None:
            return self._tx_data_from_file(self.tx_file)

        if self.waveform_type == 'FMCW':
            return self._tx_data_fmcw_from_dsp()
        elif self.waveform_type == 'OFDM':
            return self._tx_data_from_dsp()
        else:
            raise ValueError(
                f"Unsupported waveform_type: {self.waveform_type}. Expected 'OFDM' or 'FMCW'.")

    def _tx_data_fmcw_from_dsp(self):
        """Generates FMCW waveform and pads it with a preamble."""
        try:
            # Use a detection scheme for the preamble, can be shared
            detect_scheme = ZCU216_CONFIG['DETECTION_SCHEME']
        except KeyError:
            logging.warning(
                f"[{self.__class__.__name__}] DETECTION_SCHEME not defined in config. Using default Detection.")
            detect_scheme = Detection(
                sample_rate=ZCU216_CONFIG['DACSampleRate'] /
                ZCU216_CONFIG['DACInterpolationRate'] * 1e6)

        # Generate FMCW packet
        fmcw = FMCW()
        fmcw_packet = fmcw.generate()

        # Pad with preamble
        wave_tx = detect_scheme.proc_tx(fmcw_packet)
        np.save(detect_scheme.txFile, wave_tx)
        iq = self._tx_data_from_file(detect_scheme.txFile)
        return iq

    def _tx_data_from_dsp(self):
        """Generates OFDM waveform with preamble."""
        try:
            ofdm_scheme = ZCU216_CONFIG['OFDM_SCHEME']
            detect_scheme = ZCU216_CONFIG['DETECTION_SCHEME']
            ofdm_atten = ZCU216_CONFIG['OFDM_ATTEN_DB']
        except:
            ofdm_scheme = OFDM(sym_num=100, fft_size=64,
                               sub_num=48, modu="16QAM", cp_rate=0.25)
            detect_scheme = Detection(
                sample_rate=ZCU216_CONFIG['DACSampleRate'] /
                ZCU216_CONFIG['DACInterpolationRate'] * 1e6)
            ofdm_atten = 0.0
            logging.warning(
                f"[{self.__class__.__name__}] OFDM config not defined. Using the default config.")

        packet_tx = ofdm_scheme.generate(
            amp=dB2Amp(ZCU216_CONFIG["OFDM_ATTEN_DB"]))
        wave_tx = detect_scheme.proc_tx(packet_tx)
        np.save(detect_scheme.txFile, wave_tx)
        iq = self._tx_data_from_file(detect_scheme.txFile)
        return iq

    def _tx_data_from_file(self, file_path):
        if file_path.endswith('.npy'):
            loader = NumpyIqLoader(file_path)
            return loader.get_iq()
        elif file_path.endswith('.mat'):
            loader = MatlabIqLoader(file_path, key='wave')
            return loader.get_iq()
        else:
            raise Exception(f"File {file_path} is not supported.")


if __name__ == "__main__":
    print("Generating OFDM packet...")
    ofdm_gen = TxDataGenerator(waveform_type='OFDM')
    ofdm_samples = ofdm_gen.get_iq_samples()
    np.save('ofdm_packet.npy', ofdm_samples)
    print(
        f"OFDM packet generated and saved to 'ofdm_packet.npy' with shape: {ofdm_samples.shape}")

    print("\nGenerating FMCW packet...")
    fmcw_gen = TxDataGenerator(waveform_type='FMCW')
    fmcw_samples = fmcw_gen.get_iq_samples()
    np.save('fmcw_packet.npy', fmcw_samples)
    print(
        f"FMCW packet generated and saved to 'fmcw_packet.npy' with shape: {fmcw_samples.shape}")
