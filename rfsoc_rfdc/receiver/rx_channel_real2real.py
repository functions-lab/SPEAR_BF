from rfsoc_rfdc.receiver.rx_channel import RxChannel


class RxChannelReal2Real(RxChannel):
    """
    A dual real channel Rx implementation.
    """

    def __init__(self, dma_ip, fifo_count_ip, target_device, buff_size=1024, debug_mode=False):
        super().__init__(dma_ip, fifo_count_ip,
                         target_device, buff_size, debug_mode)

    @property
    def data(self):
        return self.rx_buff
