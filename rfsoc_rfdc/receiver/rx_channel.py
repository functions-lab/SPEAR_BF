import logging
from rfsoc_rfdc.dma_monitor import RxDmaMonitor
from pynq import allocate
from rfsoc_rfdc.rfdc_type import MyRFdcType


class RxChannel:
    def __init__(self, dma_ip, fifo_count_ip, target_device, buff_size=1024, debug_mode=False):
        self.rx_buff_size = buff_size
        self.rx_buff = allocate(shape=(self.rx_buff_size,),
                                dtype=MyRFdcType.DATA_PATH_DTYPE, target=target_device)

        self.rx_dma = dma_ip
        self.warning_cnt = 0
        self.debug_mode = debug_mode
        # Config FIFO count IP
        self.fifo_count = fifo_count_ip
        self.fifo_count.setdirection("in")
        self.fifo_count.setlength(32)

    def _monitor_fifo(self):
        if self.debug_mode:
            fifo_count = self.fifo_count.read()

            # Warning for low FIFO count
            if fifo_count > self.rx_buff_size:
                self.warning_cnt += 1
            if self.warning_cnt > 1000:
                self.warning_cnt = 0
                logging.info(
                    f"[Rx] Warning: Rx FIFO count {fifo_count} is larger than buffer size {self.rx_buff_size}. DMA transfer is too slow!")

    def transfer(self):
        # Monitor FIFO in debug mode
        self._monitor_fifo()
        # Trigger DMA transfer
        self.rx_dma.transfer(self.rx_buff)

    def stream(self, mode='STREAM'):
        # Monitor FIFO in debug mode
        self._monitor_fifo()
        # Trigger DMA transfer
        self.rx_dma.stream(self.rx_buff)

    @property
    def data(self):
        return self.rx_buff

    def close(self):
        """Release the DMA buffer"""
        if hasattr(self, 'rx_buff') and self.rx_buff is not None:
            # PYNQ buffers have a close() method to release the memory
            if hasattr(self.rx_buff, 'close'):
                self.rx_buff.close()
            self.rx_buff = None

    def __del__(self):
        self.close()
