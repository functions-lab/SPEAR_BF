from rfsoc_rfdc.receiver.rx_channel import RxChannel
import numpy as np


class RxChannelReal2Iq(RxChannel):
    """
    A real-to-IQ Rx channel, also works for IQ-to-IQ Rx channel.
    """

    def __init__(self, dma_ip, fifo_count_ip, target_device, buff_size=1024, debug_mode=False):
        super().__init__(dma_ip, fifo_count_ip,
                         target_device, buff_size, debug_mode)

    @property
    def data(self):
        # Reshape to (N, 2) and convert to complex64 using a view after casting to float32.
        # This makes one copy (int16 to float32) and then creates a view,
        # which is more efficient than the original slicing and arithmetic.
        return self.rx_buff.astype(np.float32).view(np.complex64)
