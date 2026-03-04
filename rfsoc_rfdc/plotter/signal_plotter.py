import plotly.graph_objs as go
import numpy as np
from rfsoc_rfdc.rfdc_type import MyRFdcType
from IPython.display import display
import logging
import time


class SignalPlotter:
    """Base class for plotting ADC samples in the time domain.
    """

    def __init__(self, title, auto_range=False):
        max_range = MyRFdcType.DAC_MAX_SCALE * 1.25
        adc_thres = MyRFdcType.DAC_MAX_SCALE
        range_min, range_max = -max_range, max_range

        self.fig = go.FigureWidget(layout={
            'title': title,
            'xaxis': {'title': 'ADC Sample Index'},
            'yaxis': {'title': 'Amplitude', 'range': [range_min, range_max] if not auto_range else None}
        })

        if auto_range:
            self.fig.layout.yaxis.autorange = True
            self.fig.layout.shapes = [
                dict(type='line', xref='paper', x0=0, x1=1, yref='y', y0=range_min, y1=range_min,
                     line=dict(dash='dash', color='red')),
                dict(type='line', xref='paper', x0=0, x1=1, yref='y', y0=range_max, y1=range_max,
                     line=dict(dash='dash', color='red'))
            ]

        # Add red dotted threshold lines at ±adc_thres
        self.fig.add_shape(
            type='line', x0=0, x1=1, xref='paper',
            y0=adc_thres, y1=adc_thres, yref='y',
            line=dict(color='red', dash='dot'),
        )
        self.fig.add_shape(
            type='line', x0=0, x1=1, xref='paper',
            y0=-adc_thres, y1=-adc_thres, yref='y',
            line=dict(color='red', dash='dot'),
        )

        display(self.fig)

    def update_plot(self, data, plot_ratio=1.0):
        raise NotImplementedError(
            "This method should be overridden by subclasses")

    def close(self):
        """Close the figure widget."""
        self.fig.close()

    def __del__(self):
        self.close()


class RealSignalPlotter(SignalPlotter):
    """
    Plot real ADC samples in the time domain
    """

    def __init__(self, title, auto_range=False):
        super().__init__(title, auto_range)
        self.fig.add_scattergl(x=[], y=[], name='Real Samples')

    def update_plot(self, data, plot_ratio=1.0):
        window_size = int(len(data) * plot_ratio)
        self.fig.data[0].x = np.arange(0, window_size, 1)
        self.fig.data[0].y = data[0:window_size]


class ComplexSignalPlotter(SignalPlotter):
    """
    Plot complex ADC samples in the time domain
    """

    def __init__(self, title='Complex Signal Plot', auto_range=False):
        super().__init__(title, auto_range)
        self.fig.add_scattergl(x=[], y=[], name='Real Samples')
        self.fig.add_scattergl(x=[], y=[], name='Complex Samples')
        self.max_windows_size = 2 ** 12

    def __update_plot_partial(self, iq_data):
        window_size = self.max_windows_size
        if len(iq_data) != window_size:
            raise ValueError(
                f"Input data length {len(iq_data)} does not match max_windows_size {self.max_windows_size}")

        x_indices = np.arange(window_size)
        self.fig.data[0].x = x_indices
        self.fig.data[0].y = iq_data.real[:window_size]
        self.fig.data[1].x = x_indices
        self.fig.data[1].y = iq_data.imag[:window_size]

    def update_plot(self, iq_data, plot_ratio=1.0):
        window_size = int(len(iq_data) * plot_ratio)
        if window_size > self.max_windows_size:
            window_size = self.max_windows_size
        x_indices = np.arange(window_size)

        self.fig.data[0].x = x_indices
        self.fig.data[0].y = iq_data.real[:window_size]
        self.fig.data[1].x = x_indices
        self.fig.data[1].y = iq_data.imag[:window_size]
