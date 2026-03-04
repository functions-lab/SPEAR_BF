import os
import numpy as np
import scipy.io
from abc import ABC, abstractmethod
import logging

from rfsoc_rfdc.rfdc_type import MyRFdcType
from rfsoc_rfdc.rfdc_config import ZCU216_CONFIG


class IqLoader:
    def __init__(self, file_path):
        self.file_path = file_path
        self.iq = None

    def check_file_exist(self):
        if not os.path.isfile(self.file_path):
            raise FileNotFoundError(
                f"The specified file does not exist: {self.file_path}")

    @staticmethod
    def scale_to_int16(iq, range_max):
        real_max, imag_max = np.max(
            np.abs(np.real(iq))), np.max(np.abs(np.imag(iq)))
        raw_max = max(real_max, imag_max)
        scaled_iq = iq * (range_max / raw_max)
        return scaled_iq

    def get_iq(self, repeat_times=1):
        if isinstance(repeat_times, int) and repeat_times != 1:
            return np.tile(self.iq.real, repeat_times), np.tile(self.iq.imag, repeat_times)
        return self.iq

    @abstractmethod
    def load_iq(self):
        pass


class NumpyIqLoader(IqLoader):
    def __init__(self, file_path, key='wave'):
        super().__init__(file_path)
        self.check_file_exist()
        self.load_iq()
        self.iq = self.scale_to_int16(self.iq, MyRFdcType.DAC_MAX_SCALE)

    def load_iq(self):
        try:
            self.iq = np.load(self.file_path)
        except KeyError:
            raise KeyError(
                f"The key '{self.key}' was not found in the MATLAB file {self.file_path}.")


class MatlabIqLoader(IqLoader):
    def __init__(self, file_path, key='wave'):
        super().__init__(file_path)
        self.key = key
        self.check_file_exist()
        self.load_iq()
        self.iq = self.scale_to_int16(self.iq, MyRFdcType.DAC_MAX_SCALE)

    def load_iq(self):
        try:
            self.iq = scipy.io.loadmat(self.file_path)[self.key]
        except KeyError:
            raise KeyError(
                f"The key '{self.key}' was not found in the MATLAB file {self.file_path}.")
