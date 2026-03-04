from rfsoc_rfdc.receiver.rx_analyzer.drivers.base_driver import BaseDriver


class Real2RealDriver(BaseDriver):
    """Driver for Real to Real conversion using injected Pipeline"""

    def __init__(self, pipeline, channel_id):
        super().__init__(channel_id)
        self.pipeline = pipeline

    def proc_rx(self, data):
        # Delegate processing to pipeline, providing the thread runner callback
        # Real2RealPipeline returns (None, None, None, None) for snr, cfo, evm, ber
        return self.pipeline.process(data, self._run_thds)

    def close(self):
        if hasattr(self.pipeline, 'close'):
            self.pipeline.close()

    def __del__(self):
        self.close()
