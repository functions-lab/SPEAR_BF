import threading
from rfsoc_rfdc.plotter.signal_plotter import ComplexSignalPlotter, RealSignalPlotter
from rfsoc_rfdc.receiver.rx_analyzer.components.base_component import BaseComponent
from rfsoc_rfdc.receiver.rx_analyzer.utils import save_to_file


from rfsoc_rfdc.rfdc_config import ZCU216_CONFIG


class TimeDomainVisualizer(BaseComponent):
    """Visualize and save raw waveform data"""

    def __init__(self, channel_id, mode="real2iq"):
        super().__init__(channel_id)
        if mode == "real2iq" or mode == "iq2iq":
            self.time_domain_plotter = ComplexSignalPlotter(
                title=f"TimeDomainVisualizer (IQ) (Channel {channel_id})")
        elif mode == "real2real":
            self.time_domain_plotter = RealSignalPlotter(
                title=f"TimeDomainVisualizer (Channel {channel_id})")
        else:
            raise RuntimeError(f"Unrecognize mode {mode}")

    def io_logging_thd(self, data):
        fname = f"{ZCU216_CONFIG['LOGGER'].get_log_dir()}/Rx{self.channel_id}_raw"
        thd = threading.Thread(target=save_to_file, args=(
            data, fname))
        return thd

    def plot_thd(self, data):
        thd = threading.Thread(
            target=self.time_domain_plotter.update_plot, args=(data, ))
        return thd

    def close(self):
        self.time_domain_plotter.close()

    def __del__(self):
        self.close()


class TimeDomainPacketVisualizer(BaseComponent):
    """Visualizer for time-domain packet analysis (assumed real2iq mode)"""

    def __init__(self, channel_id):
        super().__init__(channel_id)
        self.time_pkt_plotter = ComplexSignalPlotter(
            title=f"TimeDomainPacketVisualizer (Channel {channel_id})")

    def io_logging_thd(self, pkt_iq_data):
        fname = f"{ZCU216_CONFIG['LOGGER'].get_log_dir()}/Rx_pkt"
        thd = threading.Thread(target=save_to_file, args=(
            pkt_iq_data, fname))
        return thd

    def plot_thd(self, pkt_iq_data):
        thd = threading.Thread(
            target=self.time_pkt_plotter.update_plot, args=(pkt_iq_data, ))
        return thd

    def close(self):
        self.time_pkt_plotter.close()

    def __del__(self):
        self.close()
