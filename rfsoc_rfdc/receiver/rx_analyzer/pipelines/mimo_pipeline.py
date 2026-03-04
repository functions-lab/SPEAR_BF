import numpy as np
from rfsoc_rfdc.receiver.rx_analyzer.pipelines.base_pipeline import BasePipeline
from rfsoc_rfdc.receiver.rx_analyzer.components.time_domain_visualizer import TimeDomainVisualizer


class MimoPipeline(BasePipeline):
    """Pipeline for MIMO Processing"""

    def __init__(self, detection_scheme, rx_ant_count):
        super().__init__(channel_id=-1)
        self.channel_count = rx_ant_count
        self.time_visualizer_list = [TimeDomainVisualizer(channel_id=id,
                                                          mode="real2iq")
                                     for id in range(self.channel_count)]
        self.mimo_detection = detection_scheme

    def process(self, data, run_async_func):
        """
        Args:
            data: Multi-channel data array
        """
        thd_list = []
        for id in range(self.channel_count):
            thd_list.append(
                self.time_visualizer_list[id].plot_thd(data[id]))
            # thd_list.append(self.time_visualizer_list[id].io_logging_thd(data[id]))

        run_async_func(thd_list)

        rx_packet_list, snr_list, cfo_list = self.mimo_detection.proc_rx(data)
        return rx_packet_list, snr_list, cfo_list
