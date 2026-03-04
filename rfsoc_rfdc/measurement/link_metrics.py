import numpy as np
from typing import List, Dict


class LinkMetrics:
    """Class to store and analyze link quality metrics (SNR, EVM, BER)"""

    def __init__(self, snr: float, evm: float, ber: float):
        """
        Initialize LinkMetrics instance.

        Parameters
        ----------
        snr : float
            Signal-to-Noise Ratio in dB
        evm : float
            Error Vector Magnitude
        ber : float
            Bit Error Rate
        """
        self.snr = float(snr)
        self.evm = float(evm)
        self.ber = float(ber)

    @staticmethod
    def sort_by_snr(metrics_list: List['LinkMetrics']) -> List['LinkMetrics']:
        """
        Sort a list of LinkMetrics instances by SNR in descending order.

        Parameters
        ----------
        metrics_list : List[LinkMetrics]
            List of LinkMetrics instances to sort

        Returns
        -------
        List[LinkMetrics]
            Sorted list (highest SNR first)
        """
        return sorted(metrics_list, key=lambda m: m.snr, reverse=True)

    @staticmethod
    def average(metrics_list: List['LinkMetrics']) -> Dict[str, float]:
        """
        Calculate average SNR, EVM, and BER from a list of LinkMetrics.

        Parameters
        ----------
        metrics_list : List[LinkMetrics]
            List of LinkMetrics instances

        Returns
        -------
        Dict[str, float]
            Dictionary with keys 'snr', 'evm', 'ber' containing averages
        """
        if not metrics_list:
            return {'snr': np.nan, 'evm': np.nan, 'ber': np.nan}

        snr_vals = [m.snr for m in metrics_list]
        evm_vals = [m.evm for m in metrics_list]
        ber_vals = [m.ber for m in metrics_list]

        return {
            'snr': np.mean(snr_vals),
            'evm': np.mean(evm_vals),
            'ber': np.mean(ber_vals)
        }

    @staticmethod
    def median(metrics_list: List['LinkMetrics']) -> Dict[str, float]:
        """
        Calculate median SNR, EVM, and BER from a list of LinkMetrics.

        Parameters
        ----------
        metrics_list : List[LinkMetrics]
            List of LinkMetrics instances

        Returns
        -------
        Dict[str, float]
            Dictionary with keys 'snr', 'evm', 'ber' containing medians
        """
        if not metrics_list:
            return {'snr': np.nan, 'evm': np.nan, 'ber': np.nan}

        snr_vals = [m.snr for m in metrics_list]
        evm_vals = [m.evm for m in metrics_list]
        ber_vals = [m.ber for m in metrics_list]

        return {
            'snr': np.median(snr_vals),
            'evm': np.median(evm_vals),
            'ber': np.median(ber_vals)
        }

    @staticmethod
    def best(metrics_list: List['LinkMetrics']) -> Dict[str, float]:
        """
        Return the LinkMetrics entry with the highest SNR.

        Parameters
        ----------
        metrics_list : List[LinkMetrics]
            List of LinkMetrics instances

        Returns
        -------
        LinkMetrics
            The instance with the highest SNR, or None if list is empty
        """
        if not metrics_list:
            return {'snr': np.nan, 'evm': np.nan, 'ber': np.nan}

        return {
            'snr': metrics_list[0].snr,
            'evm': metrics_list[0].evm,
            'ber': metrics_list[0].ber
        }

    def __repr__(self):
        return f"LinkMetrics(snr={self.snr:.2f}, evm={self.evm:.4f}, ber={self.ber:.6f})"

    def __str__(self):
        return f"SNR: {self.snr:.2f} dB, EVM: {self.evm:.4f}, BER: {self.ber:.6f}"
