from rfsoc_rfdc.receiver.rx_analyzer.pipelines.base_pipeline import BasePipeline
from rfsoc_rfdc.receiver.rx_analyzer.components.time_domain_visualizer import TimeDomainVisualizer


class Real2RealPipeline(BasePipeline):
    """Pipeline for Real to Real conversion (Simple Pass-through for plotting)"""

    def __init__(self, channel_id):
        super().__init__(channel_id)
        # Initialize real visualizer directly as it's simple
        self.waveform_visualizer = TimeDomainVisualizer(
            self.channel_id, mode="real2real")

    def process(self, data, run_async_func):
        thd_list = []
        thd_list.append(self.waveform_visualizer.plot_thd(data))
        # thd_list.append(self.waveform_visualizer.io_logging_thd(data))

        run_async_func(thd_list)
        # Real2Real doesn't return metrics like snr, cfo, evm, ber.
        # It's primarily for visualization of raw data.
        return None, None, None, None

    def close(self):
        self.waveform_visualizer.close()

    def __del__(self):
        self.close()
