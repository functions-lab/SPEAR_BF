from abc import ABC, abstractmethod
from rfsoc_rfdc.receiver.rx_analyzer.utils import _sample_logger


class BaseDriver(ABC):
    """Base class for common driver functionality"""

    def __init__(self, channel_id):
        self.thd_list = []
        self.channel_id = channel_id

    def _run_thds(self, task_list=None):
        """Common thread processing"""
        target_list = task_list if task_list is not None else self.thd_list

        for thd in target_list:
            thd.start()
        for thd in target_list:
            thd.join()

        if task_list is None:
            self.thd_list.clear()

    def finalize(self):
        """Wait for all async file writes to complete before exiting."""
        _sample_logger.wait_for_writes()

    @abstractmethod
    def proc_rx(self, data):
        pass
