import numpy as np
import logging
from rfsoc_rfdc.receiver.rx_analyzer.pipelines.base_pipeline import BasePipeline
from rfsoc_rfdc.receiver.rx_analyzer.components.time_domain_visualizer import TimeDomainVisualizer
from rfsoc_rfdc.receiver.rx_analyzer.components.spectrum_visualizer import SpectrumVisualizer
from rfsoc_rfdc.rfdc_config import ZCU216_CONFIG


class ChPowerPipeline(BasePipeline):
    """Pipeline for Channel Power Measurement"""

    def __init__(self, channel_id=0):
        super().__init__(channel_id)

        self.waveform_visualizer = TimeDomainVisualizer(
            channel_id, mode="real2iq")
        self.spectrum_visualizer = SpectrumVisualizer(channel_id)

    def process(self, data, run_async_func):
        # Time Domain and Spectrum Visualization
        thd_list = []
        thd_list.append(self.waveform_visualizer.plot_thd(data))
        thd_list.append(self.spectrum_visualizer.plot_thd(data))

        # Run visualization threads
        run_async_func(thd_list)

        try:
            power = np.mean(np.abs(data)**2)
            dBm = 10 * np.log10(power * 1000)
            return dBm
        except Exception as e:
            logging.error(
                f"Rx #{self.channel_id} Failed to calculate power spectrum: {e}")
            return 0.0
