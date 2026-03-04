import threading
from rfsoc_rfdc.plotter.fft_plotter import FFTPlotter
from rfsoc_rfdc.rfdc_config import ZCU216_CONFIG
from rfsoc_rfdc.receiver.rx_analyzer.components.base_component import BaseComponent


class SpectrumVisualizer(BaseComponent):
    """Visualizer for frequency-domain packet analysis"""

    def __init__(self, channel_id, mode="real2iq"):
        super().__init__(channel_id)
        dac_samp_rate = ZCU216_CONFIG['DACSampleRate'] / \
            ZCU216_CONFIG['DACInterpolationRate'] * 1e6
        self.fft_pkt_plotter = FFTPlotter(
            sample_rate=dac_samp_rate,
            title=f"SpectrumVisualizer (Channel {channel_id})")

    def io_logging_thd(self, pkt_iq_data):
        pass

    def plot_thd(self, pkt_iq_data):
        thd = threading.Thread(
            target=self.fft_pkt_plotter.update_plot, args=(pkt_iq_data,))
        return thd

    def close(self):
        self.fft_pkt_plotter.close()

    def __del__(self):
        self.close()
