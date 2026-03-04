from abc import ABC, abstractmethod


class BaseComponent(ABC):

    def __init__(self, channel_id):
        self.channel_id = channel_id

    @abstractmethod
    def io_logging_thd(self, data):
        pass

    @abstractmethod
    def plot_thd(self, data):
        pass
