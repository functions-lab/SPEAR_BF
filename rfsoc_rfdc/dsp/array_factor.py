import numpy as np
from abc import ABC, abstractmethod


class ArrayFactor(ABC):
    """
    Abstract base class for Array Factor calculations.

    This class defines the interface for beamformers and array factor computations.
    """

    @abstractmethod
    def get_spacing(self):
        """
        Get the physical spacing of the array elements.

        Returns:
            numpy.ndarray: An array containing the positions of the antenna elements (in meters).
        """
        pass

    @abstractmethod
    def get_bfw(self):
        """
        Calculate the complex weights for beamforming.

        Returns:
            numpy.ndarray: Complex weights for the array elements.
        """
        pass

    @abstractmethod
    def get_bfw_sim(self):
        """
        Calculate the complex weights for beamforming (Simulation Only).
        This should return ideal weights without any hardware-specific calibration.

        Returns:
            numpy.ndarray: Complex weights for the array elements.
        """
        pass

    @abstractmethod
    def get_bfw_fixpt(self, bits=16):
        """
        Calculate the fixed-point weights for beamforming.

        Args:
            bits (int): The number of bits for fixed-point representation. Defaults to 16.

        Returns:
            tuple: A tuple containing (real_weights, imag_weights) as integer arrays.
        """
        pass
