from rfsoc_rfdc.rfdc_type import MyRFdcType
from pynq import allocate
from rfsoc_rfdc.transmitter.tx_channel import TxChannel
import numpy as np


class TxChannelIq2Real(TxChannel):
    """
    A IQ-to-real Tx channel, also works for IQ-to-IQ Tx channel.
    """

    def __init__(self, dma_ip, fifo_count_ip, target_device, debug_mode=False):
        super().__init__(dma_ip, fifo_count_ip, target_device, debug_mode)

    def data_copy(self, complex_array):
        i_arr, q_arr = np.int16(
            complex_array.real), np.int16(complex_array.imag)

        if i_arr.size != q_arr.size:
            raise ValueError("i/q array must have the same size")
        self.data_type_check(i_arr)
        self.data_type_check(q_arr)

        # Release previous buffer if it exists
        self.close()

        self.tx_buff = allocate(shape=(complex_array.size*2,),
                                dtype=MyRFdcType.DATA_PATH_DTYPE, target=self.target_device)
        # iq samples shall be interleaved, i samples for even indices and q samples for odd indices
        self.tx_buff[0::2] = i_arr
        self.tx_buff[1::2] = q_arr
