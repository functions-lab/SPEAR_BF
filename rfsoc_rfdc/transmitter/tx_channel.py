import numpy as np
import logging
from pynq import allocate
from rfsoc_rfdc.rfdc_type import MyRFdcType
from rfsoc_rfdc.dma_monitor import TxDmaMonitor


class TxChannel:
    def __init__(self, dma_ip, fifo_count_ip, target_device, debug_mode=False):
        self.tx_buff = None
        self.tx_dma = dma_ip
        self.warning_cnt = 0
        self.debug_mode = debug_mode
        self.target_device = target_device
        # Config FIFO count IP
        self.fifo_count = fifo_count_ip
        self.fifo_count.setdirection("in")
        self.fifo_count.setlength(32)

    def data_type_check(self, buff):
        # Validations for input buffers
        if not isinstance(buff, np.ndarray):
            raise TypeError("buff must be of type numpy.ndarray")
        if buff.dtype != MyRFdcType.DATA_PATH_DTYPE:
            raise TypeError("buff must be of data type numpy.int16")

    def data_copy(self, buff):
        self.data_type_check(buff)
        # Release previous buffer if it exists
        self.close()
        # Buffer copy
        self.tx_buff = allocate(shape=(buff.size,),
                                dtype=MyRFdcType.DATA_PATH_DTYPE, target=self.target_device)
        self.tx_buff[:] = buff[:]

    def _monitor_fifo(self):
        if self.debug_mode:
            fifo_count = self.fifo_count.read()

            # Warning for low FIFO count
            if fifo_count == 0:
                self.warning_cnt += 1
            if self.warning_cnt > 1000:
                self.warning_cnt = 0
                logging.info(
                    f"[Tx] Warning: Tx FIFO count {fifo_count} is zero. DMA transfer is too slow!")

    def transfer(self):
        # Monitor FIFO in debug mode
        self._monitor_fifo()
        # Trigger DMA transfer
        self.tx_dma.transfer(self.tx_buff)

    def stream(self, duty_cycle=100):
        # Monitor FIFO in debug mode
        self._monitor_fifo()
        # Trigger DMA transfer
        self.tx_dma.stream(self.tx_buff, duty_cycle=duty_cycle)

    def close(self):
        """Release the DMA buffer"""
        if hasattr(self, 'tx_buff') and self.tx_buff is not None:
            # PYNQ buffers have a close() method to release the memory
            if hasattr(self.tx_buff, 'close'):
                self.tx_buff.close()
            self.tx_buff = None

    def __del__(self):
        self.close()
