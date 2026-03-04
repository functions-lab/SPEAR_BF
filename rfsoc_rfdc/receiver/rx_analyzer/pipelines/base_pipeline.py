from abc import ABC, abstractmethod


class BasePipeline(ABC):
    """Abstract base class for DSP pipelines"""

    def __init__(self, channel_id=-1):
        self.channel_id = channel_id

    @abstractmethod
    def process(self, data, run_async_func):
        """
        Process received data.

        Args:
            data: Input data (numpy array)
            run_async_func: Function to execute async tasks (threads). 
                            Signature: run_async_func(task_list)

        Returns:
            metrics tuple (snr, cfo, evm, ber, etc.)
        """
        pass
