from rfsoc_rfdc.rfdc_type import MyRFdcType
from pynq import allocate
from rfsoc_rfdc.transmitter.tx_channel import TxChannel


class TxChannelReal2Real(TxChannel):
    """
    A real to real Tx channel.
    """

    def __init__(self, dma_ip, fifo_count_ip, target_device, debug_mode=False):
        super().__init__(dma_ip, fifo_count_ip, target_device, debug_mode)

    def data_copy(self, real_array):
        self.data_type_check(real_array)
        # Release previous buffer if it exists
        self.close()
        self.tx_buff = allocate(shape=(real_array.size,),
                                dtype=MyRFdcType.DATA_PATH_DTYPE, target=self.target_device)
        self.tx_buff[:] = real_array[:]
